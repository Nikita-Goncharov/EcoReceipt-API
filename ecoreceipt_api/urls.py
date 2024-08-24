from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path("terminal_api/", include("terminal_api.urls")),
    path("client_api/", include("client_api.urls"))
]
