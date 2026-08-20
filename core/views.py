from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .forms import (
    ContactForm,
    PortfolioCategoryForm,
    PortfolioImageForm,
    PortfolioProjectForm,
    ServiceForm,
    SiteContentForm,
)
from .models import Lead, PageVisit, PortfolioCategory, PortfolioImage, PortfolioProject, Service, SiteContent

WHATSAPP_NUMBER = getattr(settings, 'WHATSAPP_BUSINESS_NUMBER', '3117195100')


def build_whatsapp_message(lead):
    lines = [
        'Hola, vengo del sitio web de JJ Construmadera.',
        f'Mi nombre es {lead.name}.',
        f'Mi teléfono es {lead.phone}.',
        f'Mi correo es {lead.email}.',
    ]

    if lead.address:
        lines.append(f'Mi dirección es {lead.address}.')

    lines.extend(['', 'Mensaje:', lead.message])
    return '\n'.join(lines)


def build_whatsapp_url(lead):
    message = build_whatsapp_message(lead)
    return f'https://wa.me/{WHATSAPP_NUMBER}?text={quote(message)}'


def build_admin_notification_message(lead):
    sent_at = timezone.localtime(lead.created_at).strftime('%d/%m/%Y %H:%M:%S')
    lines = [
        'Nuevo contacto en JJ Construmadera',
        f'Fecha y hora: {sent_at}',
        '',
        f'Nombre: {lead.name}',
        f'Teléfono: {lead.phone}',
        f'Email: {lead.email}',
    ]

    if lead.address:
        lines.append(f'Dirección: {lead.address}')

    lines.extend(['', 'Mensaje:', lead.message])
    return '\n'.join(lines)


SECTION_EDITOR_MAP = {
    'inicio': {
        'label': 'Inicio',
        'entries': [
            ('home_hero_title', 'Título principal'),
            ('home_hero_subtitle', 'Subtítulo'),
            ('home_cta_primary', 'Texto de botón principal'),
            ('home_cta_secondary', 'Texto de botón secundario'),
        ],
    },
    'nosotros': {
        'label': 'Nosotros',
        'entries': [
            ('about_title', 'Título'),
            ('about_description', 'Descripción'),
            ('about_mission', 'Misión'),
            ('about_vision', 'Visión'),
        ],
    },
    'servicios': {
        'label': 'Servicios',
        'entries': [
            ('services_title', 'Título'),
            ('services_intro', 'Texto introductorio'),
        ],
    },
    'portafolio': {
        'label': 'Portafolio',
        'entries': [
            ('portfolio_title', 'Título'),
            ('portfolio_intro', 'Texto introductorio'),
        ],
    },
    'contacto': {
        'label': 'Contacto',
        'entries': [
            ('contact_phone', 'Teléfono'),
            ('contact_whatsapp', 'WhatsApp'),
            ('contact_address', 'Dirección'),
            ('contact_company_info', 'Información empresarial'),
            ('contact_map_query', 'Ubicación del mapa'),
        ],
    },
}


def get_site_content_value(slug, default=''):
    item = SiteContent.objects.filter(slug=slug).first()
    if not item:
        return default
    if item.body:
        return item.body
    if item.title:
        return item.title
    return default


def get_site_content_image(slug):
    item = SiteContent.objects.filter(slug=slug).first()
    if item and item.image:
        return item.image.url
    return ''


def ensure_site_content_entry(slug, title):
    return SiteContent.objects.get_or_create(
        slug=slug,
        defaults={'title': title, 'body': '', 'is_active': True},
    )[0]


def get_portfolio_category_items():
    categories = list(PortfolioCategory.objects.filter(is_active=True).order_by('sort_order', 'name'))
    legacy_names = sorted({
        project.category for project in PortfolioProject.objects.filter(is_active=True)
        if project.category and not PortfolioCategory.objects.filter(name=project.category).exists()
    })
    for name in legacy_names:
        categories.append(PortfolioCategory(name=name, slug=slugify(name), sort_order=999, is_active=True))
    return categories


@staff_member_required
def admin_analytics(request):
    now = timezone.now()
    today = now.date()
    week_start = now - timedelta(days=6)
    month_start = now.replace(day=1)

    total_visits = PageVisit.objects.count()
    visits_today = PageVisit.objects.filter(created_at__date=today).count()
    visits_week = PageVisit.objects.filter(created_at__gte=week_start).count()
    visits_month = PageVisit.objects.filter(created_at__gte=month_start).count()

    device_breakdown = {
        'mobile': PageVisit.objects.filter(device_type='mobile').count(),
        'tablet': PageVisit.objects.filter(device_type='tablet').count(),
        'pc': PageVisit.objects.filter(device_type='pc').count(),
    }

    total_devices = sum(device_breakdown.values()) or 1
    device_share = {
        key: round((value / total_devices) * 100, 1)
        for key, value in device_breakdown.items()
    }

    top_pages = list(
        PageVisit.objects.values('path').annotate(total=Count('id')).order_by('-total')[:8]
    )
    max_page_visits = max((item['total'] for item in top_pages), default=1)

    leads_total = Lead.objects.count()
    leads_new = Lead.objects.filter(status='nuevo').count()
    leads_contacted = Lead.objects.filter(status='contactado').count()
    leads_closed = Lead.objects.filter(status='cerrado').count()
    status_breakdown = {
        'nuevo': leads_new,
        'contactado': leads_contacted,
        'cerrado': leads_closed,
    }

    admin_links = [
        {'label': 'Leads', 'url': reverse('owner_leads')},
        {'label': 'Servicios', 'url': reverse('owner_service_list')},
        {'label': 'Portafolio', 'url': reverse('owner_portfolio_list')},
        {'label': 'Contenido', 'url': reverse('owner_content_dashboard')},
        {'label': 'Visitas', 'url': reverse('owner_dashboard')},
    ]

    recent_leads = Lead.objects.order_by('-created_at')[:5]

    return render(request, 'admin_analytics.html', {
        'site_name': 'JJ Construmadera',
        'total_visits': total_visits,
        'visits_today': visits_today,
        'visits_week': visits_week,
        'visits_month': visits_month,
        'device_breakdown': device_breakdown,
        'device_share': device_share,
        'top_pages': top_pages,
        'max_page_visits': max_page_visits,
        'leads_total': leads_total,
        'leads_new': leads_new,
        'leads_contacted': leads_contacted,
        'leads_closed': leads_closed,
        'status_breakdown': status_breakdown,
        'admin_links': admin_links,
        'recent_leads': recent_leads,
    })


def owner_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('owner_dashboard')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if user.is_staff:
            login(request, user)
            messages.success(request, 'Bienvenido al panel de JJ Construmadera.')
            return redirect('owner_dashboard')
        messages.error(request, 'Este usuario no tiene permisos de administración.')

    return render(request, 'owner_login.html', {
        'site_name': 'JJ Construmadera',
        'form': form,
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_dashboard(request):
    return admin_analytics(request)


@login_required(login_url='owner_login')
@staff_member_required
def owner_content_dashboard(request):
    sections = []
    for section_key, config in SECTION_EDITOR_MAP.items():
        sections.append({
            'slug': section_key,
            'label': config['label'],
            'url': reverse('owner_section_edit', args=[section_key]),
        })
    return render(request, 'owner_content_dashboard.html', {
        'site_name': 'JJ Construmadera',
        'sections': sections,
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_section_edit(request, section):
    config = SECTION_EDITOR_MAP.get(section)
    if not config:
        raise Http404

    entries = []
    posted = False
    for slug, label in config['entries']:
        obj = ensure_site_content_entry(slug, label)
        form = SiteContentForm(
            instance=obj,
            prefix=slug,
            data=request.POST if request.method == 'POST' else None,
            files=request.FILES if request.method == 'POST' else None,
        )
        if request.method == 'POST' and form.is_valid():
            form.save()
            posted = True
        entries.append({'slug': slug, 'label': label, 'object': obj, 'form': form})

    if request.method == 'POST' and posted:
        messages.success(request, f'Contenido de {config["label"]} actualizado correctamente.')
        return redirect('owner_section_edit', section=section)

    return render(request, 'owner_section_edit.html', {
        'site_name': 'JJ Construmadera',
        'section_label': config['label'],
        'section_slug': section,
        'entries': entries,
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_leads(request):
    leads = Lead.objects.all().order_by('-created_at')
    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    if search:
        leads = leads.filter(
            Q(name__icontains=search) | Q(email__icontains=search) | Q(phone__icontains=search)
        )
    if status_filter:
        leads = leads.filter(status=status_filter)

    return render(request, 'owner_leads.html', {
        'site_name': 'JJ Construmadera',
        'leads': leads,
        'search': search,
        'status_filter': status_filter,
        'status_choices': Lead.STATUS_CHOICES,
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_lead_update_status(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    if request.method == 'POST':
        status = request.POST.get('status', lead.status)
        if status in dict(Lead.STATUS_CHOICES):
            lead.status = status
            lead.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Estado del lead actualizado.')
    return redirect('owner_leads')


@login_required(login_url='owner_login')
@staff_member_required
def owner_service_list(request):
    services = Service.objects.all().order_by('name')
    return render(request, 'owner_services.html', {
        'site_name': 'JJ Construmadera',
        'services': services,
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_service_create(request):
    form = ServiceForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Servicio creado correctamente.')
        return redirect('owner_service_list')
    return render(request, 'owner_service_form.html', {
        'site_name': 'JJ Construmadera',
        'form': form,
        'title': 'Crear servicio',
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_service_update(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    form = ServiceForm(request.POST or None, request.FILES or None, instance=service)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Servicio actualizado correctamente.')
        return redirect('owner_service_list')
    return render(request, 'owner_service_form.html', {
        'site_name': 'JJ Construmadera',
        'form': form,
        'title': 'Editar servicio',
        'service': service,
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_service_delete(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    service.delete()
    messages.success(request, 'Servicio eliminado correctamente.')
    return redirect('owner_service_list')


@login_required(login_url='owner_login')
@staff_member_required
def owner_portfolio_list(request):
    categories = get_portfolio_category_items()
    selected_slug = request.GET.get('category', '').strip()
    selected_category = next((category for category in categories if category.slug == selected_slug), categories[0] if categories else None)
    if selected_category:
        projects = PortfolioProject.objects.filter(category=selected_category.name, is_active=True).order_by('-created_at').prefetch_related('images')
    else:
        projects = PortfolioProject.objects.filter(is_active=True).order_by('-created_at').prefetch_related('images')
    return render(request, 'owner_portfolio.html', {
        'site_name': 'JJ Construmadera',
        'categories': categories,
        'selected_category': selected_category,
        'projects': projects,
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_portfolio_category_create(request):
    form = PortfolioCategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        category = form.save(commit=False)
        category.slug = slugify(category.name)
        category.save()
        messages.success(request, 'Categoría creada correctamente.')
        return redirect('owner_portfolio_list')
    return render(request, 'owner_portfolio_category_form.html', {
        'site_name': 'JJ Construmadera',
        'form': form,
        'title': 'Nueva categoría',
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_portfolio_category_update(request, category_id):
    category = get_object_or_404(PortfolioCategory, pk=category_id)
    old_name = category.name
    form = PortfolioCategoryForm(request.POST or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        updated_category = form.save(commit=False)
        updated_category.slug = slugify(updated_category.name)
        updated_category.save()
        if old_name != updated_category.name:
            PortfolioProject.objects.filter(category=old_name).update(category=updated_category.name)
        messages.success(request, 'Categoría actualizada correctamente.')
        return redirect('owner_portfolio_list')
    return render(request, 'owner_portfolio_category_form.html', {
        'site_name': 'JJ Construmadera',
        'form': form,
        'title': 'Editar categoría',
        'category': category,
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_portfolio_category_delete(request, category_id):
    category = get_object_or_404(PortfolioCategory, pk=category_id)
    fallback_category = PortfolioCategory.objects.exclude(pk=category.pk).order_by('sort_order', 'name').first()
    fallback_name = fallback_category.name if fallback_category else 'Residencial'
    PortfolioProject.objects.filter(category=category.name).update(category=fallback_name)
    category.delete()
    messages.success(request, 'Categoría eliminada correctamente.')
    return redirect('owner_portfolio_list')


@login_required(login_url='owner_login')
@staff_member_required
def owner_portfolio_create(request):
    form = PortfolioProjectForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        project = form.save()
        messages.success(request, 'Proyecto creado correctamente.')
        return redirect('owner_portfolio_images', project_id=project.pk)
    return render(request, 'owner_portfolio_form.html', {
        'site_name': 'JJ Construmadera',
        'form': form,
        'title': 'Crear proyecto',
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_portfolio_update(request, project_id):
    project = get_object_or_404(PortfolioProject, pk=project_id)
    form = PortfolioProjectForm(request.POST or None, request.FILES or None, instance=project)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Proyecto actualizado correctamente.')
        return redirect('owner_portfolio_list')
    return render(request, 'owner_portfolio_form.html', {
        'site_name': 'JJ Construmadera',
        'form': form,
        'title': 'Editar proyecto',
        'project': project,
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_portfolio_delete(request, project_id):
    project = get_object_or_404(PortfolioProject, pk=project_id)
    project.delete()
    messages.success(request, 'Proyecto eliminado correctamente.')
    return redirect('owner_portfolio_list')


@login_required(login_url='owner_login')
@staff_member_required
def owner_portfolio_images(request, project_id):
    project = get_object_or_404(PortfolioProject, pk=project_id)
    form = PortfolioImageForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        image = form.save(commit=False)
        image.project = project
        image.save()
        messages.success(request, 'Imagen agregada al proyecto.')
        return redirect('owner_portfolio_images', project_id=project.pk)
    return render(request, 'owner_portfolio_images.html', {
        'site_name': 'JJ Construmadera',
        'project': project,
        'form': form,
        'images': project.images.all(),
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_portfolio_image_update(request, project_id, image_id):
    project = get_object_or_404(PortfolioProject, pk=project_id)
    image = get_object_or_404(PortfolioImage, pk=image_id, project=project)
    form = PortfolioImageForm(request.POST or None, request.FILES or None, instance=image)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Imagen actualizada correctamente.')
        return redirect('owner_portfolio_images', project_id=project.pk)
    return render(request, 'owner_portfolio_image_form.html', {
        'site_name': 'JJ Construmadera',
        'project': project,
        'image': image,
        'form': form,
        'title': 'Editar imagen',
    })


@login_required(login_url='owner_login')
@staff_member_required
def owner_portfolio_image_delete(request, project_id, image_id):
    project = get_object_or_404(PortfolioProject, pk=project_id)
    image = get_object_or_404(PortfolioImage, pk=image_id, project=project)
    image.delete()
    messages.success(request, 'Imagen eliminada.')
    return redirect('owner_portfolio_images', project_id=project.pk)


@login_required(login_url='owner_login')
def owner_logout(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('owner_login')


def home(request):
    service_list = Service.objects.filter(is_active=True).order_by('name')[:3]
    project_list = PortfolioProject.objects.filter(is_active=True).order_by('-created_at')[:3]
    hero_title = get_site_content_value('home_hero_title', 'Soluciones a medida para espacios que marcan la diferencia.')
    hero_subtitle = get_site_content_value('home_hero_subtitle', 'En JJ Construmadera SAS creamos ambientes funcionales y elegantes con acabados de calidad, atención cercana y ejecución responsable.')
    cta_primary = get_site_content_value('home_cta_primary', 'Solicitar cotización')
    cta_secondary = get_site_content_value('home_cta_secondary', 'Ver servicios')
    return render(request, 'home.html', {
        'site_name': 'JJ Construmadera',
        'page_title': 'Inicio',
        'hero_title': hero_title,
        'hero_subtitle': hero_subtitle,
        'cta_primary': cta_primary,
        'cta_secondary': cta_secondary,
        'services': service_list,
        'projects': project_list,
    })


def services(request):
    service_list = Service.objects.filter(is_active=True).order_by('name')
    service_title = get_site_content_value('services_title', 'Soluciones en madera y acabados para proyectos reales.')
    service_intro = get_site_content_value('services_intro', 'Diseñamos, elaboramos y ejecutamos soluciones de madera para espacios residenciales y comerciales.')
    return render(request, 'services.html', {
        'site_name': 'JJ Construmadera',
        'page_title': 'Servicios',
        'services': service_list,
        'service_title': service_title,
        'service_intro': service_intro,
    })


def portfolio(request):
    categories = get_portfolio_category_items()
    selected_slug = request.GET.get('categoria', '').strip()
    selected_category = next((category for category in categories if category.slug == selected_slug), categories[0] if categories else None)
    if selected_category:
        projects = PortfolioProject.objects.filter(category=selected_category.name, is_active=True).order_by('-created_at').prefetch_related('images')
    else:
        projects = PortfolioProject.objects.filter(is_active=True).order_by('-created_at').prefetch_related('images')
    portfolio_title = get_site_content_value('portfolio_title', 'Experiencias pensadas para vivir mejor.')
    portfolio_intro = get_site_content_value('portfolio_intro', 'Proyectos que reflejan detalle, funcionalidad y estilo.')
    return render(request, 'portfolio.html', {
        'site_name': 'JJ Construmadera',
        'page_title': 'Portafolio',
        'projects': projects,
        'categories': categories,
        'selected_category': selected_category,
        'portfolio_title': portfolio_title,
        'portfolio_intro': portfolio_intro,
    })


def portfolio_detail(request, project_id):
    project = get_object_or_404(PortfolioProject, pk=project_id, is_active=True)
    images = project.images.all().order_by('sort_order', 'id')
    return render(request, 'portfolio_detail.html', {
        'site_name': 'JJ Construmadera',
        'page_title': project.name,
        'project': project,
        'images': images,
        'category': project.category,
    })


def about(request):
    about_title = get_site_content_value('about_title', 'Una empresa con criterio, experiencia y compromiso.')
    about_description = get_site_content_value('about_description', 'JJ Construmadera SAS nace con el propósito de aportar valor a cada proyecto mediante carpintería, mobiliario y acabados de calidad, siempre con atención cercana a las necesidades del cliente.')
    about_mission = get_site_content_value('about_mission', 'Crear espacios funcionales, bonitos y duraderos que mejoren la vida de las personas.')
    about_vision = get_site_content_value('about_vision', 'Ser la referencia en soluciones de madera y acabados para proyectos residenciales y comerciales.')
    return render(request, 'about.html', {
        'site_name': 'JJ Construmadera',
        'page_title': 'Nosotros',
        'about_title': about_title,
        'about_description': about_description,
        'about_mission': about_mission,
        'about_vision': about_vision,
    })


def contact(request):
    form = ContactForm(request.POST if request.method == 'POST' else None)
    success = False
    duplicate_message = None

    map_query = getattr(settings, 'CONTACT_MAP_QUERY', 'JJ Construmadera S.A.S, Cl 22 #30b1, Montería, Córdoba').strip()
    map_query_url = quote(map_query)
    map_embed_url = f'https://www.google.com/maps?q={map_query_url}&output=embed'
    map_directions_url = f'https://www.google.com/maps/search/?api=1&query={map_query_url}'

    contact_phone = get_site_content_value('contact_phone', '+57 (000) 000 0000')
    contact_whatsapp = get_site_content_value('contact_whatsapp', '3117195100')
    contact_address = get_site_content_value('contact_address', 'JJ Construmadera S.A.S, Cl 22 #30b1, Montería, Córdoba')
    contact_company_info = get_site_content_value('contact_company_info', 'Atención personalizada para proyectos residenciales y comerciales.')
    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data
            payload = {
                'name': data['name'].strip(),
                'phone': data['phone'].strip(),
                'email': data['email'].strip().lower(),
                'address': (data.get('address') or '').strip(),
                'message': data['message'].strip(),
            }

            window_start = timezone.now() - timedelta(minutes=5)
            duplicate = Lead.objects.filter(
                email=payload['email'],
                phone=payload['phone'],
                message__iexact=payload['message'],
                created_at__gte=window_start,
            ).exists()

            if duplicate:
                duplicate_message = 'Ya recibimos una solicitud similar recientemente. Nuestro equipo la revisará pronto.'
                form.add_error(None, duplicate_message)
            else:
                lead = Lead.objects.create(**payload, status='nuevo')
                whatsapp_url = build_whatsapp_url(lead)
                return redirect(whatsapp_url)

    return render(request, 'contact.html', {
        'site_name': 'JJ Construmadera',
        'page_title': 'Contacto',
        'form': form,
        'success': success,
        'duplicate_message': duplicate_message,
        'map_query': map_query,
        'map_embed_url': map_embed_url,
        'map_directions_url': map_directions_url,
        'contact_phone': contact_phone,
        'contact_whatsapp': contact_whatsapp,
        'contact_address': contact_address,
        'contact_company_info': contact_company_info,
    })
