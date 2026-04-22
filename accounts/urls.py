from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('registro/', views.RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('validar-username/', views.validar_username, name='validar_username'),
    path('servicios/recientes/', views.servicios_recientes, name='servicios_recientes'),
    
    # Admin Panel
    path('admin-panel/', views.AdminPanelView.as_view(), name='admin_panel'),
    path('admin-panel/categorias/', views.admin_category_list, name='admin_category_list'),
    path('admin-panel/categorias/crear/', views.admin_create_category, name='admin_create_category'),
    path('admin-panel/categorias/<int:pk>/eliminar/', views.admin_delete_category, name='admin_delete_category'),
    
    # Servicios
    path('servicios/crear/', views.ServiceCreateView.as_view(), name='service_create'),
    path('servicios/', views.ServiceListView.as_view(), name='service_list'),
    path('servicios/buscar/', views.search_services, name='search_services'),
    # Solicitudes
    path('solicitudes/', views.RequestsInboxView.as_view(), name='requests_inbox'),
    path('solicitudes/<int:request_id>/aceptar/', views.AcceptRequestView.as_view(), name='accept_request'),
    path('solicitudes/<int:request_id>/rechazar/', views.RejectRequestView.as_view(), name='reject_request'),
    path('solicitudes/pendientes-count/', views.PendingCountView.as_view(), name='pending_count'),

    # Reportes
    path('reportar/<int:client_id>/', views.ReportCreateView.as_view(), name='report_create'),
    path('admin-panel/reportes/<int:pk>/estado/<str:status>/', views.admin_change_report_status, name='admin_change_report_status'),

    # Reseñas
    path('reseñas/crear/<int:request_id>/', views.ReviewCreateView.as_view(), name='review_create'),
    path('usuarios/<int:client_id>/reseñas/', views.UserReviewsPartialView.as_view(), name='user_reviews'),
]
