from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from .forms import ContactForm
from .models import Lead


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
                success = True
                form = ContactForm()
                return render(request, 'contact.html', {
                    'site_name': 'JJ Construmadera',
                    'page_title': 'Contacto',
                    'form': form,
                    'success': success,
                    'lead': lead,
                })

    return render(request, 'contact.html', {
        'site_name': 'JJ Construmadera',
        'page_title': 'Contacto',
        'form': form,
        'success': success,
        'duplicate_message': duplicate_message,
    })
