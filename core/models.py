from django.db import models


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
    is_primary = models.BooleanField(default=False, verbose_name='Principal')

    class Meta:
        ordering = ['-is_primary', 'id']
        verbose_name = 'Imagen del proyecto'
        verbose_name_plural = 'Imágenes del proyecto'

    def __str__(self):
        return f'{self.project.name} - {self.caption or "Imagen"}'


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
