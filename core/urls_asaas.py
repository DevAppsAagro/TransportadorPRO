from django.urls import path
from .views.cobranca_views import (
    configurar_cobranca,
    gerar_cobranca_frete,
    atualizar_status_cobranca,
    cancelar_cobranca,
    webhook_cobranca,
    listar_cobrancas,
    detalhe_cobranca,
    simular_pagamento,
    recriar_subconta
)
from .views.transferencia_views import (
    saldo_transferencias,
    cadastrar_conta_bancaria,
    solicitar_transferencia
)

urlpatterns = [
    # Configuração do Sistema de Cobrança
    path('configuracoes/cobranca/', configurar_cobranca, name='configurar_cobranca'),
    path('configuracoes/cobranca/recriar-subconta/', recriar_subconta, name='recriar_subconta'),
    
    # Cobranças
    path('cobrancas/', listar_cobrancas, name='listar_cobrancas'),
    path('cobrancas/<str:cobranca_id>/', detalhe_cobranca, name='detalhe_cobranca'),
    path('cobrancas/<str:cobranca_id>/simular-pagamento/', simular_pagamento, name='simular_pagamento'),
    path('fretes/<int:frete_id>/gerar-cobranca/', gerar_cobranca_frete, name='gerar_cobranca_frete'),
    path('fretes/<int:frete_id>/atualizar-status-cobranca/', atualizar_status_cobranca, name='atualizar_status_cobranca'),
    path('fretes/<int:frete_id>/cancelar-cobranca/', cancelar_cobranca, name='cancelar_cobranca'),
    
    # Webhook
    path('webhook/cobranca/', webhook_cobranca, name='webhook_cobranca'),
    
    # Transferências
    path('financeiro/saldo-transferencias/', saldo_transferencias, name='saldo_transferencias'),
    path('financeiro/cadastrar-conta-bancaria/', cadastrar_conta_bancaria, name='cadastrar_conta_bancaria'),
    path('financeiro/solicitar-transferencia/', solicitar_transferencia, name='solicitar_transferencia'),
]
