from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('servicios/', views.services, name='services'),
    path('portafolio/', views.portfolio, name='portfolio'),
    path('nosotros/', views.about, name='about'),
    path('contacto/', views.contact, name='contact'),
]
