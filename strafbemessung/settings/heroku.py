"""
Production Settings for Heroku
"""


# If using in your own project, update the project namespace below
from strafbemessung.settings.base_settings import *

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# False if not in os.environ
DEBUG = env('DEBUG')

# Raises django's ImproperlyConfigured exception if SECRET_KEY not in os.environ
SECRET_KEY = env('SECRET_KEY')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Parse database connection url strings like psql://user:pass@127.0.0.1:8458/db
DATABASES = {
    # read os.environ['DATABASE_URL'] and raises ImproperlyConfigured exception if not found
    'default': env.db(),
}

# hinzugefügt für whitenoise
STATIC_ROOT = BASE_DIR / 'staticfiles'

# CSRF-Protection
CSRF_TRUSTED_ORIGINS = ["https://stagingstrafzumessung.applikuapp.com",
                        "https://www.stagingstrafzumessung.applikuapp.com",
                        "https://strafzumessung.ch",
                        "https://www.strafzumessung.ch",
                        "https://ki.strafzumessung.ch",
                        "https://www.ki.strafzumessung.ch",
                        "https://kistrafzumessung.applikuapp.com",
                        "https://www.kistrafzumessung.applikuapp.com",]
