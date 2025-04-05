"""
URL configuration for transportador_pro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

# Configuração das URLs
urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/guide/motorista/', TemplateView.as_view(template_name='admin/guide_motorista.html'), name='admin_guide_motorista'),
    path('', include(('core.urls', 'core'))),  # URLs principais com namespace 'core'
    path('motorista/', include(('transportador_pro.urls_motorista', 'motorista'))),  # URLs de motoristas (subdomínio)
    
    # Auth URLs
    path('accounts/login/', auth_views.LoginView.as_view(template_name='core/auth/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='core/auth/password_reset.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='/password_reset/done/'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='core/auth/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='core/auth/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='core/auth/password_reset_complete.html',
        extra_context={'login_url': '/accounts/login/'}
    ), name='password_reset_complete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Se for um subdomínio de motorista, usar as URLs específicas
class SubdomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().lower()
        
        # Identificar o subdomínio
        if 'motorista.' in host:
            # Redirecionar para as URLs do subdomínio do motorista
            request.is_motorista_subdomain = True
        
        return self.get_response(request)
