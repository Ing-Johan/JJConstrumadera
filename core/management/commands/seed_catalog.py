import os
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from core.models import PortfolioCategory, PortfolioImage, PortfolioProject


CATALOG_CONFIG = {
    'puertas': {
        'category_name': 'Puertas',
        'sort_order': 1,
    },
    'cocinas': {
        'category_name': 'Cocinas',
        'sort_order': 2,
    },
    'muebles_closets': {
        'category_name': 'Muebles y Closets',
        'sort_order': 3,
    },
}

IMAGE_EXTENSIONS = {'.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp'}


def make_project_name(filename):
    """Convert filename to a readable project name."""
    name = Path(filename).stem
    name = name.replace('_', ' ').replace('-', ' ')
    words = name.split()
    result = []
    for word in words:
        if word.isdigit() or (word[0].isdigit() if word else False):
            result.append(word.upper())
        else:
            result.append(word.capitalize())
    return ' '.join(result)


class Command(BaseCommand):
    help = 'Importa el catálogo inicial de JJ ConstruMadera desde media/catalog/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la importación sin guardar cambios en la base de datos.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la reimportación aunque existan proyectos con el mismo nombre.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        base_path = Path(settings.BASE_DIR) / 'media' / 'catalog'

        if not base_path.exists():
            self.stderr.write(self.style.ERROR(f'No existe el directorio: {base_path}'))
            return

        stats = {
            'categories_created': 0,
            'categories_existing': 0,
            'projects_created': 0,
            'projects_existing': 0,
            'images_created': 0,
            'images_existing': 0,
            'files_skipped': 0,
            'files_error': 0,
            'errors': [],
        }

        self.stdout.write(self.style.NOTICE('=== INICIANDO IMPORTACIÓN DEL CATÁLOGO ==='))
        self.stdout.write(f'Directorio base: {base_path}')
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se guardarán cambios'))

        with transaction.atomic():
            for folder_key, config in CATALOG_CONFIG.items():
                folder_path = base_path / folder_key
                if not folder_path.exists():
                    self.stdout.write(self.style.WARNING(f'  Carpeta no encontrada: {folder_path}'))
                    continue

                self.stdout.write(f'\n--- Procesando: {config["category_name"]} ({folder_key}) ---')

                category, created = self.get_or_create_category(config, dry_run, stats)

                image_files = self.get_image_files(folder_path)
                self.stdout.write(f'  Imágenes encontradas: {len(image_files)}')

                for img_file in image_files:
                    self.process_image(img_file, folder_key, category, force, dry_run, stats)

            if dry_run:
                self.stdout.write(self.style.WARNING('\nDRY-RUN: Rollback de transacción (no se guardaron cambios)'))
                raise Exception('DRY_RUN_ROLLBACK')

        self.print_summary(stats)

    def get_or_create_category(self, config, dry_run, stats):
        category_name = config['category_name']
        slug = slugify(category_name)

        category = PortfolioCategory.objects.filter(slug=slug).first()

        if category:
            self.stdout.write(f'  Categoría existente: {category_name} (slug: {slug})')
            stats['categories_existing'] += 1
        else:
            if not dry_run:
                category = PortfolioCategory.objects.create(
                    name=category_name,
                    slug=slug,
                    sort_order=config['sort_order'],
                    is_active=True,
                )
            self.stdout.write(self.style.SUCCESS(f'  Categoría creada: {category_name} (slug: {slug})'))
            stats['categories_created'] += 1

        return category, not category

    def get_image_files(self, folder_path):
        files = []
        for f in sorted(folder_path.iterdir()):
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
                files.append(f)
        return files

    def process_image(self, img_path, folder_key, category, force, dry_run, stats):
        project_name = make_project_name(img_path.name)

        existing_project = PortfolioProject.objects.filter(name=project_name).first()

        if existing_project and not force:
            self.stdout.write(f'    - Proyecto existente: {project_name}')
            stats['projects_existing'] += 1

            if not existing_project.images.exists():
                self.create_gallery_image(existing_project, img_path, dry_run, stats, is_primary=True)
            return

        if not dry_run:
            with img_path.open('rb') as f:
                project = PortfolioProject.objects.create(
                    name=project_name,
                    description=f'Proyecto de {category.name}: {project_name}. Detalles disponibles en el panel administrativo.',
                    category=category.name,
                    image=File(f, name=img_path.name),
                    is_active=True,
                )
                project.image.close()
        else:
            self.stdout.write(self.style.SUCCESS(f'    + Proyecto a crear: {project_name}'))
            stats['projects_created'] += 1
            return

        self.stdout.write(self.style.SUCCESS(f'    + Proyecto creado: {project_name}'))
        stats['projects_created'] += 1

        self.create_gallery_image(project, img_path, dry_run, stats, is_primary=True)

    def create_gallery_image(self, project, img_path, dry_run, stats, is_primary=False):
        caption = f'{project.name} - Vista principal'

        existing_image = project.images.filter(image__icontains=img_path.stem).first()

        if existing_image:
            self.stdout.write(f'      - Imagen de galería existente')
            stats['images_existing'] += 1
            return

        if not dry_run:
            with img_path.open('rb') as f:
                gallery_img = PortfolioImage.objects.create(
                    project=project,
                    image=File(f, name=img_path.name),
                    caption=caption,
                    sort_order=0,
                    is_primary=is_primary,
                )
                gallery_img.image.close()
        else:
            stats['images_created'] += 1
            return

        self.stdout.write(f'      + Imagen de galería creada (se generarán optimized/thumb automáticamente)')
        stats['images_created'] += 1

    def print_summary(self, stats):
        self.stdout.write(self.style.NOTICE('\n=== RESUMEN DE IMPORTACIÓN ==='))
        self.stdout.write(f'Categorías creadas:     {stats["categories_created"]}')
        self.stdout.write(f'Categorías existentes:  {stats["categories_existing"]}')
        self.stdout.write(f'Proyectos creados:      {stats["projects_created"]}')
        self.stdout.write(f'Proyectos existentes:   {stats["projects_existing"]}')
        self.stdout.write(f'Imágenes de galería creadas: {stats["images_created"]}')
        self.stdout.write(f'Imágenes existentes:    {stats["images_existing"]}')
        self.stdout.write(f'Archivos omitidos:      {stats["files_skipped"]}')
        self.stdout.write(f'Archivos con error:     {stats["files_error"]}')

        if stats['errors']:
            self.stdout.write(self.style.ERROR('\nErrores:'))
            for err in stats['errors']:
                self.stdout.write(self.style.ERROR(f'  - {err}'))

        if stats['files_error'] == 0 and stats['files_skipped'] == 0:
            self.stdout.write(self.style.SUCCESS('\nImportación completada sin errores.'))
        else:
            self.stdout.write(self.style.WARNING('\nImportación completada con advertencias.'))