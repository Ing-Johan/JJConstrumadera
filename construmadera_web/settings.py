"""
Django settings for construmadera_web project.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-key-change-me')
DEBUG = os.getenv('DEBUG', 'True').lower() in {'1', 'true', 'yes', 'on'}

if not DEBUG and SECRET_KEY == 'dev-secret-key-change-me':
    raise ImproperlyConfigured('DJANGO_SECRET_KEY debe configurarse en producción (DEBUG=False).')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]

# Security settings for production (when DEBUG=False)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.AnalyticsMiddleware',
]

ROOT_URLCONF = 'construmadera_web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.footer_contact',
            ],
        },
    },
]

WSGI_APPLICATION = 'construmadera_web.wsgi.application'

# Database configuration
# USE_SQLITE=True -> SQLite (desarrollo local)
# USE_SQLITE=False + DATABASE_URL -> PostgreSQL (producción Render)
# USE_SQLITE=False + DB_* variables -> PostgreSQL (manual)
use_sqlite = os.getenv('USE_SQLITE', 'True').lower() in {'1', 'true', 'yes', 'on'}
database_url = os.getenv('DATABASE_URL', '').strip()

if use_sqlite:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
elif database_url:
    DATABASES = {
        'default': dj_database_url.parse(
            database_url,
            conn_max_age=60,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'construmadera'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / os.getenv('MEDIA_ROOT', 'media')

# Almacenamiento de archivos.
# 'default' = archivos multimedia subidos desde el panel (local o Cloudinary según USE_CLOUDINARY).
# 'staticfiles' = archivos estáticos (WhiteNoise en producción, Django en desarrollo).
USE_CLOUDINARY = os.getenv('USE_CLOUDINARY', 'False').lower() in {'1', 'true', 'yes', 'on'}

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        'OPTIONS': {
            'location': MEDIA_ROOT,
            'base_url': MEDIA_URL,
        },
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

if USE_CLOUDINARY:
    import cloudinary

    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        secure=True,
    )
    # Backend oficial de Cloudinary para Django. Solo se configura con USE_CLOUDINARY=True
    # porque al importarse exige las credenciales CLOUDINARY_* (falla sin ellas en dev).
    STORAGES['default'] = {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    }

# CSRF trusted origins para producción (configurable por variable de entorno)
csrf_trusted_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '').strip()
if csrf_trusted_origins:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_trusted_origins.split(',') if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []

# Host público asignado por Render (cero configuración manual de dominios).
render_hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME', '').strip()
if render_hostname:
    if render_hostname not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(render_hostname)
    render_origin = f'https://{render_hostname}'
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session security
# Sesión expira al cerrar el navegador (no persiste entre sesiones de navegador)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Cookie security - Desarrollo (HTTP) y Producción (HTTPS via DEBUG=False)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# En producción (DEBUG=False) se activan automáticamente:
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

WHATSAPP_BUSINESS_NUMBER = os.getenv('WHATSAPP_BUSINESS_NUMBER', '3117195100').strip()
CONTACT_MAP_QUERY = os.getenv(
    'CONTACT_MAP_QUERY',
    'JJ Construmadera S.A.S, Cl 22 #30b1, Montería, Córdoba',
).strip()

EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in {'1', 'true', 'yes', 'on'}
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() in {'1', 'true', 'yes', 'on'}
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@localhost')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@localhost')
# Aviso por email al admin con cada lead nuevo (además del redirect a WhatsApp).
# False por defecto: el flujo principal es WhatsApp y los tests lo verifican.
SEND_ADMIN_EMAIL_ON_LEAD = os.getenv('SEND_ADMIN_EMAIL_ON_LEAD', 'False').lower() in {'1', 'true', 'yes', 'on'}

