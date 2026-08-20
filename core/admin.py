from django.contrib import admin

from .models import Lead, PageVisit, PortfolioImage, PortfolioProject, Service, SiteContent


class PortfolioImageInline(admin.TabularInline):
    model = PortfolioImage
    extra = 3


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PortfolioProject)
class PortfolioProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PortfolioImageInline]


@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'slug', 'body')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'email', 'phone', 'message', 'admin_notes')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Datos del lead', {
            'fields': ('name', 'phone', 'email', 'address', 'message')
        }),
        ('Gestión', {
            'fields': ('status', 'admin_notes')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = ('path', 'device_type', 'session_key', 'created_at')
    list_filter = ('device_type', 'created_at')
    search_fields = ('path', 'session_key')
    readonly_fields = ('path', 'device_type', 'session_key', 'created_at')
    ordering = ('-created_at',)
