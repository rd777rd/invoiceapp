from django.conf import settings


def branding(request):
    """Makes COMPANY_NAME available to every template as {{ company_name }}
    without touching every view. The only per-client customization point
    this app has right now -- see settings.py."""
    return {'company_name': settings.COMPANY_NAME}
