from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('servicios/', views.services, name='services'),
    path('portafolio/', views.portfolio, name='portfolio'),
    path('portafolio/<int:project_id>/', views.portfolio_detail, name='portfolio_detail'),
    path('nosotros/', views.about, name='about'),
    path('contacto/', views.contact, name='contact'),
    path('owner/login/', views.owner_login, name='owner_login'),
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/content/', views.owner_content_dashboard, name='owner_content_dashboard'),
    path('owner/content/<str:section>/', views.owner_section_edit, name='owner_section_edit'),
    path('owner/leads/', views.owner_leads, name='owner_leads'),
    path('owner/leads/<int:lead_id>/status/', views.owner_lead_update_status, name='owner_lead_update_status'),
    path('owner/services/', views.owner_service_list, name='owner_service_list'),
    path('owner/services/new/', views.owner_service_create, name='owner_service_create'),
    path('owner/services/<int:service_id>/edit/', views.owner_service_update, name='owner_service_update'),
    path('owner/services/<int:service_id>/delete/', views.owner_service_delete, name='owner_service_delete'),
    path('owner/portfolio/', views.owner_portfolio_list, name='owner_portfolio_list'),
    path('owner/portfolio/categories/new/', views.owner_portfolio_category_create, name='owner_portfolio_category_create'),
    path('owner/portfolio/categories/<int:category_id>/edit/', views.owner_portfolio_category_update, name='owner_portfolio_category_update'),
    path('owner/portfolio/categories/<int:category_id>/delete/', views.owner_portfolio_category_delete, name='owner_portfolio_category_delete'),
    path('owner/portfolio/new/', views.owner_portfolio_create, name='owner_portfolio_create'),
    path('owner/portfolio/<int:project_id>/edit/', views.owner_portfolio_update, name='owner_portfolio_update'),
    path('owner/portfolio/<int:project_id>/delete/', views.owner_portfolio_delete, name='owner_portfolio_delete'),
    path('owner/portfolio/<int:project_id>/images/', views.owner_portfolio_images, name='owner_portfolio_images'),
    path('owner/portfolio/<int:project_id>/images/<int:image_id>/edit/', views.owner_portfolio_image_update, name='owner_portfolio_image_update'),
    path('owner/portfolio/<int:project_id>/images/<int:image_id>/delete/', views.owner_portfolio_image_delete, name='owner_portfolio_image_delete'),
    path('owner/logout/', views.owner_logout, name='owner_logout'),
]
