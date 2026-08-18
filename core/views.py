from django.shortcuts import render


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
    return render(request, 'contact.html', {
        'site_name': 'JJ Construmadera',
        'page_title': 'Contacto',
    })
