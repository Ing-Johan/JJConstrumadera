import logging
from io import BytesIO

from django.core.files.base import ContentFile
from django.db import models

logger = logging.getLogger(__name__)


class PageVisit(models.Model):
    DEVICE_CHOICES = [
        ('mobile', 'Móvil'),
        ('tablet', 'Tablet'),
        ('pc', 'PC'),
    ]

    path = models.CharField(max_length=255, db_index=True, verbose_name='Ruta')
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_CHOICES,
        default='pc',
        verbose_name='Tipo de dispositivo',
    )
    session_key = models.CharField(max_length=50, blank=True, null=True, db_index=True, verbose_name='Sesión')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de visita')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Visita'
        verbose_name_plural = 'Visitas'

    def __str__(self):
        return f'{self.path} - {self.device_type}'


class BaseContentModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Service(BaseContentModel):
    name = models.CharField(max_length=120, verbose_name='Nombre')
    description = models.TextField(verbose_name='Descripción')
    image = models.ImageField(upload_to='services/', blank=True, null=True, verbose_name='Imagen')
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        ordering = ['name']
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'

    def __str__(self):
        return self.name


class PortfolioCategory(BaseContentModel):
    name = models.CharField(max_length=120, unique=True, verbose_name='Nombre')
    slug = models.SlugField(max_length=140, unique=True, verbose_name='Slug')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='Orden')
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Categoría del portafolio'
        verbose_name_plural = 'Categorías del portafolio'

    def __str__(self):
        return self.name


class PortfolioProject(BaseContentModel):
    CATEGORY_CHOICES = [
        ('Residencial', 'Residencial'),
        ('Comercial', 'Comercial'),
        ('Rehabilitación', 'Rehabilitación'),
        ('Mobiliario', 'Mobiliario'),
    ]

    name = models.CharField(max_length=150, verbose_name='Nombre')
    description = models.TextField(verbose_name='Descripción')
    category = models.CharField(max_length=60, choices=CATEGORY_CHOICES, verbose_name='Categoría')
    image = models.ImageField(upload_to='portfolio/', blank=True, null=True, verbose_name='Imagen principal')
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Portafolio'

    def __str__(self):
        return self.name


class PortfolioImage(BaseContentModel):
    project = models.ForeignKey(
        PortfolioProject,
        related_name='images',
        on_delete=models.CASCADE,
        verbose_name='Proyecto',
    )
    image = models.ImageField(upload_to='portfolio/gallery/', verbose_name='Imagen')
    caption = models.CharField(max_length=120, blank=True, verbose_name='Leyenda')
    optimized_image = models.ImageField(upload_to='portfolio/optimized/', blank=True, null=True, verbose_name='Imagen optimizada')
    thumb_image = models.ImageField(upload_to='portfolio/thumbs/', blank=True, null=True, verbose_name='Miniatura')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='Orden')
    is_primary = models.BooleanField(default=False, verbose_name='Principal')

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Imagen del proyecto'
        verbose_name_plural = 'Imágenes del proyecto'

    def __str__(self):
        return f'{self.project.name} - {self.caption or "Imagen"}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.image:
            return

        self.regenerate_derivatives()
        super().save(update_fields=['optimized_image', 'thumb_image', 'updated_at'])

    def regenerate_derivatives(self):
        """Genera optimized_image y thumb_image a partir del archivo original.

        No destructivo: nunca elimina la imagen original y conserva el registro.
        """
        if not self.image:
            return

        try:
            from PIL import Image
        except ImportError:
            logger.warning(
                'Pillow no está disponible; no se generaron versiones optimizadas para %s (id=%s).',
                self.image.name,
                self.pk,
            )
            return

        basename = self.image.name.rsplit('/', 1)[-1]
        prefix = f'{self.pk}_{basename}'

        try:
            with self.image.open('rb') as image_file:
                img = Image.open(image_file)
                img.load()
        except Exception:
            logger.exception(
                'No se pudo abrir la imagen original "%s" (id=%s).',
                self.image.name,
                self.pk,
            )
            return

        img_format = img.format or 'JPEG'
        save_kwargs = {'optimize': True}
        if img_format.upper() == 'JPEG':
            save_kwargs.update({'quality': 85})

        # Imagen optimizada (máx. 1600px de ancho, conservando proporción)
        try:
            max_width = 1600
            if img.width > max_width:
                ratio = max_width / float(img.width)
                new_size = (max_width, int(float(img.height) * ratio))
            else:
                new_size = (img.width, img.height)

            optimized_io = BytesIO()
            optimized = img.copy()
            optimized.thumbnail(new_size, Image.LANCZOS)
            if img_format.upper() == 'JPEG':
                optimized = optimized.convert('RGB')
            optimized.save(optimized_io, format=img_format, **save_kwargs)
            if self.optimized_image:
                self.optimized_image.delete(save=False)
            self.optimized_image.save(prefix, ContentFile(optimized_io.getvalue()), save=False)
            optimized_io.close()
        except Exception:
            logger.exception(
                'Falló la generación de la imagen optimizada para %s (id=%s).',
                self.image.name,
                self.pk,
            )

        # Miniatura (ajustada dentro de 800x600, conservando proporción)
        try:
            thumb_io = BytesIO()
            thumb = img.copy()
            thumb.thumbnail((800, 600), Image.LANCZOS)
            if img_format.upper() == 'JPEG':
                thumb = thumb.convert('RGB')
            thumb.save(thumb_io, format=img_format, **save_kwargs)
            if self.thumb_image:
                self.thumb_image.delete(save=False)
            self.thumb_image.save(prefix, ContentFile(thumb_io.getvalue()), save=False)
            thumb_io.close()
        except Exception:
            logger.exception(
                'Falló la generación de la miniatura para %s (id=%s).',
                self.image.name,
                self.pk,
            )


class SiteContent(BaseContentModel):
    slug = models.SlugField(unique=True, max_length=120, verbose_name='Slug')
    title = models.CharField(max_length=200, verbose_name='Título')
    body = models.TextField(blank=True, verbose_name='Texto')
    image = models.ImageField(upload_to='content/', blank=True, null=True, verbose_name='Imagen')
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        ordering = ['slug']
        verbose_name = 'Contenido general'
        verbose_name_plural = 'Contenido general'

    def __str__(self):
        return self.title


class Lead(BaseContentModel):
    STATUS_CHOICES = [
        ('nuevo', 'Nuevo'),
        ('contactado', 'Contactado'),
        ('en_proceso', 'En proceso'),
        ('cerrado', 'Cerrado'),
        ('no_interesado', 'No interesado'),
    ]

    name = models.CharField(max_length=120, verbose_name='Nombre')
    phone = models.CharField(max_length=30, verbose_name='Teléfono')
    email = models.EmailField(verbose_name='Email')
    address = models.CharField(max_length=200, blank=True, verbose_name='Dirección')
    message = models.TextField(verbose_name='Mensaje')
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='nuevo',
        verbose_name='Estado',
    )
    admin_notes = models.TextField(blank=True, verbose_name='Observaciones administrativas')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'

    def __str__(self):
        return f'{self.name} - {self.get_status_display()}'
