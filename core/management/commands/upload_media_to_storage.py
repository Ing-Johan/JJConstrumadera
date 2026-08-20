import mimetypes
import os

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from storages.backends.s3boto3 import S3Boto3Storage


class Command(BaseCommand):
    help = (
        'Sube los archivos multimedia locales (media/) al almacenamiento persistente '
        'configurado (USE_S3=True) conservando exactamente sus rutas relativas. '
        'No elimina los archivos locales originales ni modifica la base de datos.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se subiría sin subir nada.',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Re-subir archivos aunque ya existan en el almacenamiento remoto.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        overwrite = options['overwrite']

        if not isinstance(default_storage, S3Boto3Storage):
            self.stderr.write(self.style.ERROR(
                'El almacenamiento "default" no es S3. Activa USE_S3=True '
                '(con las variables AWS configuradas) antes de ejecutar este comando.'
            ))
            return

        media_root = settings.MEDIA_ROOT
        if not os.path.isdir(media_root):
            self.stderr.write(self.style.ERROR(f'No existe el directorio MEDIA_ROOT: {media_root}'))
            return

        # Preflight: verifica credenciales/bucket/endpoint antes de subir nada.
        if not dry_run:
            try:
                default_storage.exists('__construmadera_preflight__')
            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    'No se pudo conectar al almacenamiento S3. Revisa bucket, credenciales y endpoint.'
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
                    self.stdout.write(f'  [dry-run] SUBIRIA {rel}')
                    uploaded += 1
                    continue
                if exists and overwrite:
                    default_storage.delete(rel)
                with open(full, 'rb') as fh:
                    content = File(fh)
                    content.content_type = mimetypes.guess_type(rel)[0] or 'application/octet-stream'
                    default_storage.save(rel, content)
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