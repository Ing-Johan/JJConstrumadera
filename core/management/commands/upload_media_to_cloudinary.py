import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

CLOUDINARY_ENV_VARS = (
    'CLOUDINARY_CLOUD_NAME',
    'CLOUDINARY_API_KEY',
    'CLOUDINARY_API_SECRET',
)


class Command(BaseCommand):
    help = (
        'Sube los archivos multimedia locales (media/) a Cloudinary '
        'conservando sus rutas relativas como public_id. '
        'No elimina los archivos locales originales ni modifica la base de datos.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se subiría (y qué se omitiría) sin subir nada.',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Re-subir archivos aunque ya existan en Cloudinary.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        overwrite = options['overwrite']

        missing = [name for name in CLOUDINARY_ENV_VARS if not os.getenv(name)]
        if missing:
            self.stderr.write(self.style.ERROR(
                'Credenciales de Cloudinary no configuradas. Define '
                + ', '.join(CLOUDINARY_ENV_VARS)
                + ' (con USE_CLOUDINARY=True) antes de ejecutar este comando.'
            ))
            return

        if not settings.USE_CLOUDINARY:
            self.stderr.write(self.style.ERROR(
                'USE_CLOUDINARY no está activo. Activa USE_CLOUDINARY=True '
                '(con las variables CLOUDINARY_* configuradas) antes de ejecutar este comando.'
            ))
            return

        from cloudinary_storage.storage import MediaCloudinaryStorage

        if not isinstance(default_storage, MediaCloudinaryStorage):
            self.stderr.write(self.style.ERROR(
                'El almacenamiento "default" no es Cloudinary. '
                'Revisa la configuración de USE_CLOUDINARY en settings.py.'
            ))
            return

        media_root = settings.MEDIA_ROOT
        if not os.path.isdir(media_root):
            self.stderr.write(self.style.ERROR(
                f'No existe el directorio MEDIA_ROOT: {media_root}'
            ))
            return

        if not dry_run:
            try:
                import cloudinary.api
                cloudinary.api.usage()
            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    'No se pudo conectar con Cloudinary. Revisa cloud name, '
                    'API key y API secret, o el plan de la cuenta.'
                ))
                self.stderr.write(self.style.ERROR(str(e)))
                return

        files = []
        for root, dirs, names in os.walk(media_root):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for name in names:
                if name.startswith('.'):
                    continue
                full = os.path.join(root, name)
                rel = os.path.relpath(full, media_root).replace(os.sep, '/')
                files.append((full, rel))

        total = len(files)
        self.stdout.write(f'Encontrados {total} archivo(s) en {media_root}')

        uploaded = skipped = failed = 0
        failed_names = []

        for full, rel in sorted(files):
            try:
                exists = default_storage.exists(rel)
                if exists and not overwrite:
                    skipped += 1
                    self.stdout.write(f'  SKIP {rel}')
                    continue
                if dry_run:
                    if exists and overwrite:
                        self.stdout.write(f'  [dry-run] RE-SUBIRIA {rel}')
                    else:
                        self.stdout.write(f'  [dry-run] SUBIRIA {rel}')
                    uploaded += 1
                    continue
                if not dry_run:
                    import cloudinary.uploader
                    public_id = self._resource_public_id(rel)
                    cloudinary.uploader.upload(
                        full,
                        public_id=public_id,
                        resource_type='image',
                        overwrite=overwrite,
                        invalidate=overwrite,
                        tags=['media'],
                    )
                uploaded += 1
                self.stdout.write(self.style.SUCCESS(f'  OK   {rel}'))
            except Exception as e:
                failed += 1
                failed_names.append(rel)
                self.stdout.write(self.style.ERROR(f'  FALLO {rel}: {e}'))

        self.stdout.write('')
        self.stdout.write(
            f'Total: {total} | Subidos: {uploaded} | Omitidos: {skipped} | Fallidos: {failed}'
        )
        if failed_names:
            self.stdout.write(self.style.ERROR('Archivos fallidos:'))
            for name in failed_names:
                self.stdout.write(self.style.ERROR(f'  - {name}'))
        else:
            self.stdout.write(self.style.SUCCESS('Migración finalizada sin errores.'))

    @staticmethod
    def _resource_public_id(rel):
        prefix = settings.MEDIA_URL.strip('/')
        prefixed = f'{prefix}/{rel}' if prefix else rel
        root, _ = os.path.splitext(prefixed)
        return root