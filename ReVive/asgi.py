"""
ASGI config for ReVive project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import get_default_application
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ReVive.settings')
django.setup()

application = get_default_application()
