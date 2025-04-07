from django.urls import path
from core.views import motorista_views

app_name = 'motorista'

urlpatterns = [
    # Autenticação
    path('', motorista_views.motorista_login, name='login'),
    path('logout/', motorista_views.motorista_logout, name='logout'),
    path('get_first_name/', motorista_views.get_first_name, name='get_first_name'),
    path('get_empresa_logo/', motorista_views.get_empresa_logo, name='get_empresa_logo'),
    
    # Dashboard
    path('loading/', motorista_views.loading_screen, name='loading'),
    path('dashboard/', motorista_views.motorista_dashboard, name='dashboard'),
    
    # Abastecimentos
    path('abastecimentos/', motorista_views.listar_abastecimentos_pendentes, name='listar_abastecimentos_pendentes'),
    path('abastecimentos/<int:pk>/', motorista_views.detalhe_abastecimento_pendente, name='detalhe_abastecimento_pendente'),
    path('abastecimentos/novo/', motorista_views.criar_abastecimento_pendente, name='criar_abastecimento_pendente'),
    
    # Perfil
    path('perfil/', motorista_views.perfil_motorista, name='perfil'),
    path('perfil/alterar-senha/', motorista_views.alterar_senha, name='alterar_senha'),
    
    # Contatos
    path('contatos/', motorista_views.contatos_motorista, name='contatos'),
    path('contatos/novo/', motorista_views.contato_novo_motorista, name='contato_novo'),
    path('contatos/novo-posto/', motorista_views.criar_posto, name='criar_posto'),
]
