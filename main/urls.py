from django.urls import path
from . import views

urlpatterns = [
    path('googlea128813747473c36.html', TemplateView.as_view(template_name='googlea128813747473c36.html')),
    # Page principale
    path('', views.index, name='index'),

    # Pages des advancements
    path('advancements/<str:folder>/', views.advancements, name='advancements'),
]
