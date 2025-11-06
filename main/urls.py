from django.urls import path
from . import views

urlpatterns = [
    # Page principale
    path('', views.index, name='index'),

    # Pages des advancements
    path('advancements/<str:folder>/', views.advancements, name='advancements'),
]
