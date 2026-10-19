from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from core.admin import admin_site

urlpatterns = [
    path("admin/", admin_site.urls),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
