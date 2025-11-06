from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Optionnel : garder l'admin Django si besoin
    # path('admin/', admin.site.urls),

    # Inclure les URLs de l'app principale
    path('', include('main.urls')),
]
