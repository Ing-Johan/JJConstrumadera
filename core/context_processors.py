from urllib.parse import quote

from django.conf import settings

DEFAULT_PHONE = '3117195100'
DEFAULT_LOCATION = 'JJ Construmadera S.A.S, Cl 22 #30b1, Montería, Córdoba'
DEFAULT_LOCATION_SHORT = 'Montería, Córdoba'


def footer_contact(request):
    """Datos de contacto compartidos por el footer de todas las páginas."""
    phone = getattr(settings, 'WHATSAPP_BUSINESS_NUMBER', DEFAULT_PHONE).strip()
    location = getattr(settings, 'CONTACT_MAP_QUERY', DEFAULT_LOCATION).strip()
    return {
        'footer_phone': phone,
        'footer_phone_href': f'tel:{phone}',
        'footer_whatsapp_url': f'https://wa.me/{phone}',
        'footer_location_short': DEFAULT_LOCATION_SHORT,
        'footer_maps_url': f'https://www.google.com/maps/search/?api=1&query={quote(location)}',
    }