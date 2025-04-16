from django.urls import path
from .views.cobranca_views import (
    configurar_cobranca,
    gerar_cobranca_frete,
    atualizar_status_cobranca,
    cancelar_cobranca,
    webhook_cobranca,
    listar_cobrancas
)

urlpatterns = [
    # Configuração do Sistema de Cobrança
    path('configuracoes/cobranca/', configurar_cobranca, name='configurar_cobranca'),
    
    # Cobranças
    path('cobrancas/', listar_cobrancas, name='listar_cobrancas'),
    path('fretes/<int:frete_id>/gerar-cobranca/', gerar_cobranca_frete, name='gerar_cobranca_frete'),
    path('fretes/<int:frete_id>/atualizar-status-cobranca/', atualizar_status_cobranca, name='atualizar_status_cobranca'),
    path('fretes/<int:frete_id>/cancelar-cobranca/', cancelar_cobranca, name='cancelar_cobranca'),
    
    # Webhook
    path('webhook/cobranca/', webhook_cobranca, name='webhook_cobranca'),
]
