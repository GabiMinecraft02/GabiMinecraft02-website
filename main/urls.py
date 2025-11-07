from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('advancements/<str:folder>/', views.advancements, name='advancements'),

    # Google Search Console
    path(
        'googlea128813747473c36.html',
        TemplateView.as_view(template_name='main/googlea128813747473c36.html'),
        name='google_verification'
    ),
]
