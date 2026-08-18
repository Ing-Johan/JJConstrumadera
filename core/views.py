from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render
from django.utils import timezone

from .forms import ContactForm
from .models import Lead

WHATSAPP_NUMBER = '3117195100'


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


def home(request):
    return render(request, 'home.html', {
        'site_name': 'JJ Construmadera',
        'page_title': 'Inicio',
    })


def services(request):
    return render(request, 'services.html', {
        'site_name': 'JJ Construmadera',
        'page_title': 'Servicios',
    })


def portfolio(request):
    return render(request, 'portfolio.html', {
        'site_name': 'JJ Construmadera',
        'page_title': 'Portafolio',
    })


def about(request):
    return render(request, 'about.html', {
        'site_name': 'JJ Construmadera',
        'page_title': 'Nosotros',
    })


def contact(request):
    form = ContactForm(request.POST if request.method == 'POST' else None)
    success = False
    duplicate_message = None

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
                admin_email = getattr(settings, 'ADMIN_EMAIL', None)
                if admin_email:
                    send_mail(
                        subject='Nuevo contacto - JJ Construmadera',
                        message=build_admin_notification_message(lead),
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@localhost'),
                        recipient_list=[admin_email],
                        fail_silently=False,
                    )

                success = True
                form = ContactForm()
                whatsapp_url = build_whatsapp_url(lead)
                return render(request, 'contact.html', {
                    'site_name': 'JJ Construmadera',
                    'page_title': 'Contacto',
                    'form': form,
                    'success': success,
                    'lead': lead,
                    'whatsapp_url': whatsapp_url,
                })

    return render(request, 'contact.html', {
        'site_name': 'JJ Construmadera',
        'page_title': 'Contacto',
        'form': form,
        'success': success,
        'duplicate_message': duplicate_message,
    })
