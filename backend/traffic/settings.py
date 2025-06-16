INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',  # CORS 추가
    'traffic',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS 미들웨어 추가 (최상단에 위치)
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS 설정
CORS_ALLOW_ALL_ORIGINS = True  # 개발 환경에서만 사용
CORS_ALLOW_CREDENTIALS = True

# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
# ] 