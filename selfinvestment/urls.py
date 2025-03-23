from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('user_accounts.urls')),
    path('api/core/', include('app_core.urls')),
    path('api/analytics/', include('app_analytics.urls')),
    path('api/portfolio/', include('app_portfolio.urls')),
    path('api/reminders/', include('app_reminders.urls')),
]

# 開発環境でのメディアファイル配信
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
