from django.utils import timezone

from .models import PageVisit


def detect_device_type(user_agent):
    if not user_agent:
        return 'pc'

    ua = user_agent.lower()
    if 'ipad' in ua or 'tablet' in ua or 'playbook' in ua:
        return 'tablet'
    if 'android' in ua or 'iphone' in ua or 'mobile' in ua:
        return 'mobile'
    return 'pc'


class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method != 'GET':
            return response

        ignored_prefixes = ('/admin/', '/static/', '/media/', '/__debug__/', '/favicon.ico')
        if any(request.path.startswith(prefix) for prefix in ignored_prefixes):
            return response

        if request.path in {'', '/'}:
            path = '/'
        else:
            path = request.path

        PageVisit.objects.create(
            path=path,
            device_type=detect_device_type(request.META.get('HTTP_USER_AGENT', '')),
            session_key=request.session.session_key,
            created_at=timezone.now(),
        )

        return response
