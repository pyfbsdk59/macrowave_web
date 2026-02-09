import os
import dj_database_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 安全設定 (部署時請改為 False)
DEBUG = os.environ.get('RENDER', False) != 'true'
ALLOWED_HOSTS = ['*']

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-key-change-me')

# ... 其他設定 ...

# 自訂一個簡單的 API 金鑰，GUI 上傳時必須吻合才能存入
API_UPLOAD_KEY = os.environ.get('API_UPLOAD_KEY', 'macrowave168')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dashboard', # 你的 App
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # 靜態文件處理
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # 設定模板路徑
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

WSGI_APPLICATION = 'config.wsgi.application'

# 資料庫設定：優先讀取環境變數 DATABASE_URL (Koyeb 提供的)
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3', # 本地開發用 SQLite，部署用 Postgres
        conn_max_age=600
    )
}

# 靜態文件設定 (Render 需要)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'