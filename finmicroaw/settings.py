"""
Configuración del proyecto FinMicro.
 
Basado en lo que exige el informe (Sección III, PESTEL — factor LEGAL y
TECNOLÓGICO): cumplimiento de la Ley N°19.628 de protección de datos, y
una arquitectura SaaS que hoy funciona en modo mono-servidor con
aislación de datos por usuario ("multi-tenant lógico"), pensada para
poder escalar a un esquema multi-tenant más estricto (p. ej. con
django-tenants) si el crecimiento del proyecto lo justifica.
 
NOTA SOBRE LA BASE DE DATOS: por defecto se usa SQLite (no requiere
ninguna configuración) para poder levantar el proyecto de inmediato.
Cuando definas tu motor de base de datos definitivo, solo hay que
completar las variables DB_* en tu archivo .env (ver .env.example) —
nada más en este archivo necesita cambiar.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def _env_bool(nombre, por_defecto=False):
    return os.environ.get(nombre, str(por_defecto)).strip().lower() in ("1", "true", "yes", "si", "sí")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-clave-de-desarrollo-mish",
)
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

if not DEBUG:
    # Lista mínima recomendada por el checklist de despliegue de Django
    # cuando DEBUG=False (settings-in-production). Requiere servir el
    # sitio bajo HTTPS. Para probar sin HTTPS (p. ej. Docker en tu PC),
    # define DJANGO_HTTPS=False.
    _https = _env_bool("DJANGO_HTTPS", True)
    SECURE_SSL_REDIRECT = _https
    SESSION_COOKIE_SECURE = _https
    CSRF_COOKIE_SECURE = _https
    if _https:
        # Nginx termina el HTTPS y avisa con esta cabecera (deploy/nginx).
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
        SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# HSTS preload inscribe el dominio en la lista de los navegadores y es
# difícil de revertir; se decidirá con el dominio definitivo (doc 11).
SILENCED_SYSTEM_CHECKS = ["security.W021"]

CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "core",
    "accounts",
    "subscriptions",
    "finances",
    "taxes",
    "projections"
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Sirve /static/ también con DEBUG=False (Docker / producción).
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # request.negocio / request.rol_negocio (colaboradores, ver accounts/negocio.py)
    'accounts.negocio.NegocioActivoMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'finmicroaw.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "core.context_processors.datos_de_cuenta",
            ],
        },
    },
]

WSGI_APPLICATION = 'finmicroaw.wsgi.application'

# --- Usuario personalizado ---

AUTH_USER_MODEL = "accounts.Usuario"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "finances:dashboard"
LOGOUT_REDIRECT_URL = "core:home"

# --- Correo (recuperación de contraseña, invitaciones) ---
# Por defecto los correos se imprimen en la consola del servidor. En
# producción, define EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# y los EMAIL_* de tu proveedor (p. ej. Amazon SES) en el .env.
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = _env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "FinMicro <no-responder@finmicro.cl>")


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

# SQLite por defecto (cero configuración). Para usar otro motor, define
# DB_ENGINE en tu .env (por ejemplo "postgresql") y completa los DB_*
# correspondientes — ver .env.example.
if os.environ.get("DB_ENGINE") == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "finmicro"),
            "USER": os.environ.get("DB_USER", "finmicro"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            # Reutiliza la conexión 60 s en vez de abrir una por petición,
            # y verifica que siga viva antes de usarla (RDS puede cortarla).
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {
                # En AWS RDS usar "require": la conexión viaja cifrada.
                "sslmode": os.environ.get("DB_SSLMODE", "prefer"),
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            # En Docker apunta a un volumen para que los datos sobrevivan.
            "NAME": os.environ.get("SQLITE_PATH", BASE_DIR / "db.sqlite3"),
        }
    }
 
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True

# Separador de miles con punto, como se escribe en Chile.
FORMAT_MODULE_PATH = ["finmicroaw.formats"]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- Caché (usada por core.services.BancoCentralService) -----------------
# LocMemCache alcanza para desarrollo y para un solo proceso. En
# producción con más de un worker conviene cambiar a Redis
# (django-redis) para que la caché se comparta entre procesos.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
 
# --- Mensajes (alineado con las clases CSS de static/css/styles.css) -----
from django.contrib.messages import constants as message_constants
 
MESSAGE_TAGS = {
    message_constants.DEBUG: "aviso-debug",
    message_constants.INFO: "aviso-info",
    message_constants.SUCCESS: "aviso-exito",
    message_constants.WARNING: "aviso-alerta",
    message_constants.ERROR: "aviso-error",
}
 
# --- Pasarelas de pago (Sección PESTEL: Khipu, Flow.cl) -------------------
# Mientras no se completen las credenciales reales, el sistema opera en
# modo simulado (ver subscriptions/services.py) para que el flujo de
# suscripción a Premium se pueda probar de punta a punta sin morosidad.
PAGOS_MODO_SIMULADO = _env_bool("PAGOS_MODO_SIMULADO", True)
KHIPU_API_KEY = os.environ.get("KHIPU_API_KEY", "")
FLOW_API_KEY = os.environ.get("FLOW_API_KEY", "")
FLOW_SECRET_KEY = os.environ.get("FLOW_SECRET_KEY", "")
FLOW_API_URL = os.environ.get("FLOW_API_URL", "https://sandbox.flow.cl/api")