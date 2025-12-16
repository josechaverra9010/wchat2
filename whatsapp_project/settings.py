"""
Django settings for whatsapp_project project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv()

# --- Security and Debugging ---

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production-xyz123')

# SECURITY WARNING: don't run with debug turned on in production!
# IMPORTANT: Convert the environment variable string to a boolean properly.
# 'True' or '1' is True, anything else is False.
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

# Dominio ngrok dinámico
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN") # No default needed, as it's checked below

# ALLOWED_HOSTS corregido y simplificado
ALLOWED_HOSTS = [
    'wchat2.onrender.com', # The domain where your app is hosted
    '.onrender.com',
    "127.0.0.1",
    "localhost",
]

# Agregar dominio ngrok si existe y aceptar subdominios *.ngrok-free.app
# **IMPROVEMENT**: It's safer to only add NGROK_DOMAIN if it's explicitly set.
if NGROK_DOMAIN:
    ALLOWED_HOSTS.append(NGROK_DOMAIN)

# Aceptar el dominio ngrok con el wildcard (it's safe as ngrok manages it)
ALLOWED_HOSTS.append(".ngrok-free.app")

# Permitir desde el entorno si existe
ENV_ALLOWED = os.getenv("ALLOWED_HOSTS")
if ENV_ALLOWED:
    # Ensure no empty strings from split (e.g., if env var is "host1,,host2")
    ALLOWED_HOSTS.extend([h.strip() for h in ENV_ALLOWED.split(",") if h.strip()])


# --- Application definition ---

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'chatbot',
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
]

ROOT_URLCONF = 'whatsapp_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'whatsapp_project.wsgi.application'


# --- Database ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# --- Internationalization ---
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# --- Static files (CSS, JavaScript, Images) ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- WhatsApp Configuration ---
META_PHONE_NUMBER_ID = os.getenv('META_PHONE_NUMBER_ID', '')
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN', '')
META_VERIFY_TOKEN = os.getenv('META_VERIFY_TOKEN', 'my_secure_verify_token')
META_WEBHOOK_SECRET = os.getenv('META_WEBHOOK_SECRET', '')

# --- Gemini Configuration ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# --- Logging Configuration ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'chatbot': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# --- CSRF Configuration para webhook ---
# CSRF_TRUSTED_ORIGINS should ONLY be used for HTTPS origins
CSRF_TRUSTED_ORIGINS = []

# Add NGROK_DOMAIN to CSRF_TRUSTED_ORIGINS for development if it exists
if NGROK_DOMAIN and DEBUG:
    # Ensure it starts with https:// for the Meta webhook to work correctly
    CSRF_TRUSTED_ORIGINS.append(f"https://{NGROK_DOMAIN}")
elif not DEBUG:
    # Agregar tu dominio en producción
    CSRF_TRUSTED_ORIGINS = ['https://tu-dominio.com']
