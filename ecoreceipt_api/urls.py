from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from docs import views

urlpatterns = [
    path("", views.docs),
    path('admin/', admin.site.urls),
    path("terminal_api/", include("terminal_api.urls")),
    path("client_api/", include("client_api.urls"))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
