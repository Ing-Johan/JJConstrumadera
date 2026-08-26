import os
import re
from pathlib import Path
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from core.models import PortfolioCategory, PortfolioImage, PortfolioProject


CATALOG_FOLDERS = {
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

# Patrones para limpiar nombres de archivo
REMOVE_PATTERNS = [
    r'\s*\(?\d+\)?\.?\s*$',  # números finales: " 01", "(1)", "1."
    r'^(?:puerta|cocina|mueble|closet|armario)\s*',  # prefijos genéricos
    r'\s*(?:madera|moderna|clasica|diseño|personalizada)\s*$',  # sufijos genéricos
]

# Palabras que se capitalizan completamente (siglas, etc.)
UPPER_WORDS = {'jj', 'sas', 'md', 'cv', 'hd', '3d', '2d'}


def is_auto_caption(caption):
    """Check if caption looks auto-generated."""
    if not caption:
        return True
    auto_patterns = [
        r'Vista principal',
        r'Vista \d+',
        r'- Vista',
    ]
    return any(re.search(p, caption) for p in auto_patterns)


def humanize_filename(filename, folder_key=None):
    """Convert filename to a readable human-friendly name."""
    name = Path(filename).stem
    
    # Replace separators with spaces
    name = name.replace('_', ' ').replace('-', ' ')
    
    # Handle current generic naming: P (1), C (1), M (1) -> Puerta 1, Cocina 1, Mueble 1
    generic_match = re.match(r'^([PCM])\s*\(?(\d+)\)?\.?\s*$', name, re.IGNORECASE)
    if generic_match:
        prefix = generic_match.group(1).upper()
        number = generic_match.group(2)
        if prefix == 'P':
            return f'Puerta {number}'
        elif prefix == 'C':
            return f'Cocina {number}'
        elif prefix == 'M':
            return f'Mueble {number}'
    
    # Remove common technical patterns (for future descriptive names)
    for pattern in REMOVE_PATTERNS:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Split into words and process
    words = name.split()
    result = []
    for word in words:
        if word.lower() in UPPER_WORDS:
            result.append(word.upper())
        elif word.isdigit():
            result.append(word)
        elif word and word[0].isdigit():
            result.append(word.upper())
        else:
            result.append(word.capitalize())
    
    # Join and clean up multiple spaces
    humanized = ' '.join(result)
    humanized = re.sub(r'\s+', ' ', humanized).strip()
    
    # Fallback if empty
    if not humanized:
        humanized = Path(filename).stem
    
    return humanized


def get_or_create_caption(project, img_path, existing_caption=None):
    """Generate caption for an image, preserving manual captions."""
    if existing_caption and not is_auto_caption(existing_caption):
        return existing_caption  # Preserve manual caption

    # Generate from filename
    name = humanize_filename(img_path.name)
    
    # Avoid redundancy: if project name is already in the filename, just use filename
    project_words = set(project.name.lower().split())
    name_words = set(name.lower().split())
    
    # If the humanized filename is very similar to project name, use a generic caption
    if name.lower() == project.name.lower() or project_words.issuperset(name_words):
        return f'{project.name} - Vista principal'
    
    return f'{project.name} - {name}'


class Command(BaseCommand):
    help = 'Sincroniza el catálogo desde media/catalog/ con la base de datos (idempotente)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la sincronización sin guardar cambios.',
        )
        parser.add_argument(
            '--regenerate-derivatives',
            action='store_true',
            help='Regenera optimized_image y thumb_image para todas las imágenes.',
        )
        parser.add_argument(
            '--update-captions',
            action='store_true',
            help='Actualiza captions a nombres legibles (respeta captions manuales).',
        )
        parser.add_argument(
            '--folder',
            type=str,
            help='Procesar solo una carpeta específica (puertas, cocinas, muebles_closets).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        regenerate = options['regenerate_derivatives']
        update_captions = options['update_captions']
        single_folder = options['folder']

        base_path = Path(settings.BASE_DIR) / 'media' / 'catalog'

        if not base_path.exists():
            self.stderr.write(self.style.ERROR(f'No existe el directorio: {base_path}'))
            return

        folders_to_process = {}
        if single_folder:
            if single_folder not in CATALOG_FOLDERS:
                self.stderr.write(self.style.ERROR(f'Carpeta desconocida: {single_folder}'))
                return
            folders_to_process[single_folder] = CATALOG_FOLDERS[single_folder]
        else:
            folders_to_process = CATALOG_FOLDERS

        stats = {
            'categories_created': 0,
            'categories_updated': 0,
            'categories_existing': 0,
            'projects_created': 0,
            'projects_updated': 0,
            'projects_unchanged': 0,
            'images_created': 0,
            'images_updated': 0,
            'images_unchanged': 0,
            'images_regenerated': 0,
            'captions_updated': 0,
            'files_skipped': 0,
            'errors': [],
        }

        self.stdout.write(self.style.NOTICE('=== SINCRONIZACIÓN DEL CATÁLOGO JJ CONSTRUMADERA ==='))
        self.stdout.write(f'Directorio base: {base_path}')
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se guardarán cambios'))

        try:
            with transaction.atomic():
                for folder_key, config in folders_to_process.items():
                    folder_path = base_path / folder_key
                    if not folder_path.exists():
                        self.stdout.write(self.style.WARNING(f'  Carpeta no encontrada: {folder_path}'))
                        continue

                    self.stdout.write(f'\n--- Procesando: {config["category_name"]} ({folder_key}) ---')

                    category = self.get_or_create_category(config, dry_run, stats)

                    image_files = self.get_image_files(folder_path)
                    self.stdout.write(f'  Imágenes encontradas: {len(image_files)}')

                    for img_file in image_files:
                        self.process_image(
                            img_file, folder_key, category,
                            force=dry_run, dry_run=dry_run, stats=stats,
                            update_captions=update_captions
                        )

                    if regenerate:
                        self.regenerate_category_derivatives(category, dry_run, stats)

                if dry_run:
                    self.stdout.write(self.style.WARNING('\nDRY-RUN: Rollback de transacción (no se guardaron cambios)'))
                    raise Exception('DRY_RUN_ROLLBACK')

        except Exception as e:
            if 'DRY_RUN_ROLLBACK' not in str(e):
                self.stderr.write(self.style.ERROR(f'Error: {e}'))
                raise
        finally:
            self.print_summary(stats)

    def get_or_create_category(self, config, dry_run, stats):
        category_name = config['category_name']
        slug = slugify(category_name)

        category = PortfolioCategory.objects.filter(slug=slug).first()

        if category:
            # Update sort_order if different
            if category.sort_order != config['sort_order'] or not category.is_active:
                if not dry_run:
                    category.sort_order = config['sort_order']
                    category.is_active = True
                    category.save(update_fields=['sort_order', 'is_active', 'updated_at'])
                self.stdout.write(f'  Categoría actualizada: {category_name} (orden: {config["sort_order"]})')
                stats['categories_updated'] += 1
            else:
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

        return category

    def get_image_files(self, folder_path):
        files = []
        for f in sorted(folder_path.iterdir()):
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
                files.append(f)
        return files

    def process_image(self, img_path, folder_key, category, force, dry_run, stats, update_captions):
        human_name = humanize_filename(img_path.name, folder_key)
        
        # Find existing project by image filename match (most reliable)
        existing_project = PortfolioProject.objects.filter(
            category=category.name,
            is_active=True,
            image__icontains=img_path.stem
        ).first()
        
        # Also check by humanized name match
        if not existing_project:
            for project in PortfolioProject.objects.filter(category=category.name, is_active=True):
                if humanize_filename(project.name, folder_key) == human_name:
                    existing_project = project
                    break

        if existing_project and not force:
            # Project exists - update if needed
            updated = False
            
            # Check if main image needs update (different file)
            current_main = existing_project.image.name if existing_project.image else ''
            expected_main = f'portfolio/{img_path.name}'
            
            if current_main != expected_main:
                if not dry_run:
                    with img_path.open('rb') as f:
                        existing_project.image.save(img_path.name, File(f), save=True)
                self.stdout.write(f'    ~ Proyecto actualizado (imagen principal): {human_name}')
                updated = True
                stats['projects_updated'] += 1
            
            # Ensure gallery image exists
            self.ensure_gallery_image(existing_project, img_path, dry_run, stats, update_captions)
            
            if not updated:
                self.stdout.write(f'    = Proyecto sin cambios: {human_name}')
                stats['projects_unchanged'] += 1
            
            return

        # Create new project
        if not dry_run:
            with img_path.open('rb') as f:
                project = PortfolioProject.objects.create(
                    name=human_name,
                    description=f'Proyecto de {category.name}: {human_name}. Detalles disponibles en el panel administrativo.',
                    category=category.name,
                    image=File(f, name=img_path.name),
                    is_active=True,
                )
                project.image.close()
        else:
            self.stdout.write(self.style.SUCCESS(f'    + Proyecto a crear: {human_name}'))
            stats['projects_created'] += 1
            return

        self.stdout.write(self.style.SUCCESS(f'    + Proyecto creado: {human_name}'))
        stats['projects_created'] += 1

        self.ensure_gallery_image(project, img_path, dry_run, stats, update_captions)

    def ensure_gallery_image(self, project, img_path, dry_run, stats, update_captions):
        caption = get_or_create_caption(project, img_path)
        
        # Check if gallery image already exists for this file
        existing_gallery = project.images.filter(
            image__icontains=img_path.stem
        ).first()

        if existing_gallery:
            if update_captions and existing_gallery.caption != caption:
                if not dry_run:
                    existing_gallery.caption = caption
                    existing_gallery.save(update_fields=['caption', 'updated_at'])
                self.stdout.write(f'      ~ Caption actualizada: {caption}')
                stats['captions_updated'] += 1
            else:
                self.stdout.write(f'      = Imagen de galería existente')
                stats['images_unchanged'] += 1
            return

        # Create gallery image
        if not dry_run:
            with img_path.open('rb') as f:
                gallery_img = PortfolioImage.objects.create(
                    project=project,
                    image=File(f, name=img_path.name),
                    caption=caption,
                    sort_order=0,
                    is_primary=True,
                )
                gallery_img.image.close()
        else:
            stats['images_created'] += 1
            return

        self.stdout.write(f'      + Imagen de galería creada (se generarán optimized/thumb automáticamente)')
        stats['images_created'] += 1

    def regenerate_category_derivatives(self, category, dry_run, stats):
        self.stdout.write(f'  Regenerando derivadas para categoría: {category.name}...')
        for project in PortfolioProject.objects.filter(category=category.name, is_active=True):
            for img in project.images.all():
                if not dry_run:
                    img.regenerate_derivatives()
                    img.save(update_fields=['optimized_image', 'thumb_image', 'updated_at'])
                stats['images_regenerated'] += 1
        self.stdout.write(f'    Derivadas regeneradas: {stats["images_regenerated"]}')

    def print_summary(self, stats):
        self.stdout.write(self.style.NOTICE('\n=== RESUMEN DE SINCRONIZACIÓN ==='))
        self.stdout.write(f'Categorías creadas:      {stats["categories_created"]}')
        self.stdout.write(f'Categorías actualizadas: {stats["categories_updated"]}')
        self.stdout.write(f'Proyectos creados:       {stats["projects_created"]}')
        self.stdout.write(f'Proyectos actualizados:  {stats["projects_updated"]}')
        self.stdout.write(f'Proyectos sin cambios:   {stats["projects_unchanged"]}')
        self.stdout.write(f'Imágenes creadas:        {stats["images_created"]}')
        self.stdout.write(f'Imágenes actualizadas:   {stats["images_updated"]}')
        self.stdout.write(f'Imágenes sin cambios:    {stats["images_unchanged"]}')
        self.stdout.write(f'Captions actualizadas:   {stats["captions_updated"]}')
        self.stdout.write(f'Derivadas regeneradas:   {stats["images_regenerated"]}')
        self.stdout.write(f'Archivos omitidos:       {stats["files_skipped"]}')

        if stats['errors']:
            self.stdout.write(self.style.ERROR('\nErrores:'))
            for err in stats['errors']:
                self.stdout.write(self.style.ERROR(f'  - {err}'))

        if stats['errors']:
            self.stdout.write(self.style.WARNING('\nSincronización completada con errores.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nSincronización completada exitosamente.'))