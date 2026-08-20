from django.core.management.base import BaseCommand
from django.db.models import Q

from core.models import PortfolioImage


class Command(BaseCommand):
    help = (
        'Regenera las versiones optimizadas y miniatura de las imágenes del portafolio '
        'conservando los archivos originales.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Regenera todas las imágenes, incluso las que ya tienen versiones generadas.',
        )
        parser.add_argument(
            '--ids',
            nargs='+',
            type=int,
            help='Regenera únicamente las imágenes con estos ids.',
        )

    def handle(self, *args, **options):
        queryset = PortfolioImage.objects.all()

        if options['ids']:
            queryset = queryset.filter(pk__in=options['ids'])
        elif not options['all']:
            queryset = queryset.filter(
                Q(optimized_image__isnull=True) | Q(thumb_image__isnull=True)
            )

        total = queryset.count()
        self.stdout.write(f'Procesando {total} imagen(es)...')

        processed = 0
        failed = []

        for image in queryset:
            image.regenerate_derivatives()
            image.save(update_fields=['optimized_image', 'thumb_image', 'updated_at'])

            if image.optimized_image and image.thumb_image:
                processed += 1
                self.stdout.write(self.style.SUCCESS(f'  OK    {image.image.name}'))
            else:
                failed.append(image.image.name)
                self.stdout.write(self.style.ERROR(f'  FALLO {image.image.name}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Procesadas correctamente: {processed}'))
        if failed:
            self.stdout.write(self.style.ERROR(f'Fallaron: {len(failed)}'))
            for name in failed:
                self.stdout.write(self.style.ERROR(f'  - {name}'))
        else:
            self.stdout.write(self.style.SUCCESS('Sin errores.'))