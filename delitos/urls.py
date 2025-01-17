from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tipo_delito/', views.tipo_delito, name='tipo_delito'),
    path('mapa/', views.mapa, name='mapa'),
]
