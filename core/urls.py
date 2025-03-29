from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from .views import dashboard, financeiro, veiculos, relatorios, configuracao
from .views.auth_views import register, login_view
from .views.contatos import contatos, contato_novo, contato_editar, contato_excluir
from .views.categorias import categorias, categoria_nova, categoria_editar, categoria_excluir, subcategorias, subcategoria_nova, subcategoria_editar, subcategoria_excluir
from .views.cargas import cargas, carga_nova, carga_editar, carga_excluir
from .views.caminhoes import caminhoes, caminhao_novo, caminhao_editar, caminhao_excluir, caminhao_detalhes
from .views.carretas import lista_carretas, criar_carreta, editar_carreta, excluir_carreta
from .views.conjuntos import conjuntos, conjunto_novo, conjunto_editar, conjunto_excluir
from .views.fretes import fretes, frete_novo, frete_editar, frete_excluir, frete_detalhes, frete_print
from .views.abastecimentos import abastecimentos, abastecimento_novo, abastecimento_editar, abastecimento_excluir
from .views.estimativa_pneus import estimativa_pneus_list, estimativa_pneus_create, estimativa_pneus_edit, estimativa_pneus_delete, detalhes_estimativa
from .views.estimativa_manutencao import estimativa_manutencao_list, estimativa_manutencao_create, estimativa_manutencao_edit, estimativa_manutencao_delete, detalhes_estimativa_manutencao
from .views.estimativa_custo_fixo import estimativa_custo_fixo_list, estimativa_custo_fixo_create, estimativa_custo_fixo_edit, estimativa_custo_fixo_delete, detalhes_estimativa_custo_fixo, calcular_valor_por_dia
from .views.despesa import despesa_list, despesa_create, despesa_edit, despesa_delete, despesa_detail, registrar_pagamento, get_subcategorias, get_destinos_por_alocacao
from .views.relatorios import relatorio_veiculo, relatorio_frete, fluxo_caixa, dre, relatorio_cliente, relatorio_manutencao, relatorio_despesa, relatorio_cliente_print, relatorio_veiculo_print
from .views.configuracoes import configuracoes_empresa
from .views.landing import landing_page
from .views.motoristas import listar_motoristas, criar_motorista, editar_motorista, excluir_motorista, detalhe_motorista, resetar_senha_motorista
from .views.abastecimentos_pendentes import (
    listar_abastecimentos_pendentes, detalhe_abastecimento_pendente,
    aprovar_abastecimento, rejeitar_abastecimento, estatisticas_abastecimentos_pendentes
)

app_name = 'core'

urlpatterns = [
    # Landing page (para domínio principal)
    path('', landing_page, name='landing_page'),
    
    # Sistema (app)
    path('dashboard/', dashboard, name='dashboard'),
    path('login/', login_view, name='login'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='core/auth/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='core/auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core/auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='core/auth/password_reset_complete.html'), name='password_reset_complete'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:login'), name='logout'),
    path('register/', register, name='register'),
    path('index/', landing_page, name='landing_page'),
    path('financeiro/', financeiro, name='financeiro'),
    path('veiculos/', veiculos, name='veiculos'),
    path('contatos/', contatos, name='contatos'),
    path('contatos/novo/', contato_novo, name='contato_novo'),
    path('contatos/<int:pk>/editar/', contato_editar, name='contato_editar'),
    path('contatos/<int:pk>/excluir/', contato_excluir, name='contato_excluir'),
    path('relatorios/', relatorios, name='relatorios'),
    path('relatorios/veiculo/', relatorio_veiculo, name='relatorio_veiculo'),
    path('relatorios/veiculo/print/', relatorio_veiculo_print, name='relatorio_veiculo_print'),
    path('relatorios/frete/', relatorio_frete, name='relatorio_frete'),
    path('relatorios/frete/<int:pk>/', relatorio_frete, name='relatorio_frete_detalhe'),
    path('relatorios/fluxo-caixa/', fluxo_caixa, name='fluxo_caixa'),
    path('relatorios/dre/', dre, name='dre'),
    path('relatorios/cliente/', relatorio_cliente, name='relatorio_cliente'),
    path('relatorios/cliente/print/', relatorio_cliente_print, name='relatorio_cliente_print'),
    path('relatorios/manutencao/', relatorio_manutencao, name='relatorio_manutencao'),
    path('relatorios/despesa/', relatorio_despesa, name='relatorio_despesa'),
    
    # Configurações
    path('configuracoes/empresa/', configuracoes_empresa, name='configuracoes_empresa'),
    
    # Rotas de categorias
    path('categorias/', categorias, name='categorias'),
    path('categorias/nova/', categoria_nova, name='categoria_nova'),
    path('categorias/<int:id>/editar/', categoria_editar, name='categoria_editar'),
    path('categorias/<int:id>/excluir/', categoria_excluir, name='categoria_excluir'),
    
    # Rotas de subcategorias
    path('subcategorias/', subcategorias, name='subcategorias'),  
    path('categorias/<int:categoria_id>/subcategorias/', subcategorias, name='subcategorias_por_categoria'),
    path('subcategorias/nova/', subcategoria_nova, name='subcategoria_nova'),
    path('subcategorias/<int:id>/editar/', subcategoria_editar, name='subcategoria_editar'),
    path('subcategorias/<int:id>/excluir/', subcategoria_excluir, name='subcategoria_excluir'),
    path('categorias/<int:categoria_id>/subcategorias/nova/', subcategoria_nova, name='subcategoria_nova_por_categoria'),
    path('categorias/<int:categoria_id>/subcategorias/<int:id>/editar/', subcategoria_editar, name='subcategoria_editar_por_categoria'),
    path('categorias/<int:categoria_id>/subcategorias/<int:id>/excluir/', subcategoria_excluir, name='subcategoria_excluir_por_categoria'),
    
    # Rotas de cargas
    path('cargas/', cargas, name='cargas'),
    path('cargas/nova/', carga_nova, name='carga_nova'),
    path('cargas/<int:id>/editar/', carga_editar, name='carga_editar'),
    path('cargas/<int:id>/excluir/', carga_excluir, name='carga_excluir'),
    
    # Rotas de caminhões
    path('caminhoes/', caminhoes, name='caminhoes'),
    path('caminhoes/novo/', caminhao_novo, name='caminhao_novo'),
    path('caminhoes/<int:id>/editar/', caminhao_editar, name='caminhao_editar'),
    path('caminhoes/<int:id>/excluir/', caminhao_excluir, name='caminhao_excluir'),
    path('caminhoes/<int:id>/detalhes/', caminhao_detalhes, name='caminhao_detalhes'),
    
    # Rotas de carretas
    path('carretas/', lista_carretas, name='carretas'),
    path('carretas/nova/', criar_carreta, name='carreta_nova'),
    path('carretas/<int:id>/editar/', editar_carreta, name='carreta_editar'),
    path('carretas/<int:id>/excluir/', excluir_carreta, name='carreta_excluir'),
    
    # Rotas de conjuntos
    path('conjuntos/', conjuntos, name='conjuntos'),
    path('conjuntos/novo/', conjunto_novo, name='conjunto_novo'),
    path('conjuntos/<int:id>/editar/', conjunto_editar, name='conjunto_editar'),
    path('conjuntos/<int:id>/excluir/', conjunto_excluir, name='conjunto_excluir'),
    
    # Rotas para manipulação de fretes
    path('fretes/', fretes, name='fretes'),
    path('fretes/novo/', frete_novo, name='frete_novo'),
    path('fretes/<int:id>/editar/', frete_editar, name='frete_editar'),
    path('fretes/<int:id>/excluir/', frete_excluir, name='frete_excluir'),
    path('fretes/<int:id>/detalhes/', frete_detalhes, name='frete_detalhes'),
    path('fretes/<int:id>/print/', frete_print, name='frete_print'),
    
    # Rotas de abastecimentos
    path('abastecimentos/', abastecimentos, name='abastecimentos'),
    path('abastecimentos/novo/', abastecimento_novo, name='abastecimento_novo'),
    path('abastecimentos/<int:id>/editar/', abastecimento_editar, name='abastecimento_editar'),
    path('abastecimentos/<int:id>/excluir/', abastecimento_excluir, name='abastecimento_excluir'),
    # Comentando o redirecionamento errado
    # path('abastecimentos/pendentes/', lambda request: redirect('motorista:listar_abastecimentos_pendentes'), name='abastecimentos_pendentes'),
    
    # Rotas de estimativa de pneus
    path('estimativa-pneus/', estimativa_pneus_list, name='estimativa_pneus_list'),
    path('estimativa-pneus/nova/', estimativa_pneus_create, name='estimativa_pneus_create'),
    path('estimativa-pneus/<int:id>/editar/', estimativa_pneus_edit, name='estimativa_pneus_edit'),
    path('estimativa-pneus/<int:id>/excluir/', estimativa_pneus_delete, name='estimativa_pneus_delete'),
    path('estimativa-pneus/<int:id>/detalhes/', detalhes_estimativa, name='detalhes_estimativa'),
    
    # Rotas de estimativa de manutenção
    path('estimativa-manutencao/', estimativa_manutencao_list, name='estimativa_manutencao_list'),
    path('estimativa-manutencao/nova/', estimativa_manutencao_create, name='estimativa_manutencao_create'),
    path('estimativa-manutencao/<int:id>/editar/', estimativa_manutencao_edit, name='estimativa_manutencao_edit'),
    path('estimativa-manutencao/<int:id>/excluir/', estimativa_manutencao_delete, name='estimativa_manutencao_delete'),
    path('estimativa-manutencao/<int:id>/detalhes/', detalhes_estimativa_manutencao, name='detalhes_estimativa_manutencao'),
    
    # Rotas de estimativa de custo fixo
    path('estimativa-custo-fixo/', estimativa_custo_fixo_list, name='estimativa_custo_fixo_list'),
    path('estimativa-custo-fixo/nova/', estimativa_custo_fixo_create, name='estimativa_custo_fixo_create'),
    path('estimativa-custo-fixo/<int:id>/editar/', estimativa_custo_fixo_edit, name='estimativa_custo_fixo_edit'),
    path('estimativa-custo-fixo/<int:id>/excluir/', estimativa_custo_fixo_delete, name='estimativa_custo_fixo_delete'),
    path('estimativa-custo-fixo/<int:id>/detalhes/', detalhes_estimativa_custo_fixo, name='detalhes_estimativa_custo_fixo'),
    path('api/calcular-valor-por-dia/', calcular_valor_por_dia, name='calcular_valor_por_dia'),
    
    # Rotas de despesas
    path('despesas/', despesa_list, name='despesa_list'),
    path('despesas/nova/', despesa_create, name='despesa_create'),
    path('despesas/<int:id>/editar/', despesa_edit, name='despesa_edit'),
    path('despesas/<int:id>/excluir/', despesa_delete, name='despesa_delete'),
    path('despesas/<int:id>/detalhes/', despesa_detail, name='despesa_detail'),
    path('despesas/<int:id>/registrar-pagamento/', registrar_pagamento, name='registrar_pagamento'),
    path('api/subcategorias/', get_subcategorias, name='get_subcategorias'),
    path('api/destinos-por-alocacao/', get_destinos_por_alocacao, name='get_destinos_por_alocacao'),
    
    # Rotas de abastecimentos pendentes
    path('abastecimentos/pendentes/', listar_abastecimentos_pendentes, name='listar_abastecimentos_pendentes'),
    path('abastecimentos/pendentes/<int:id>/', detalhe_abastecimento_pendente, name='detalhe_abastecimento_pendente'),
    path('abastecimentos/pendentes/<int:id>/aprovar/', aprovar_abastecimento, name='aprovar_abastecimento'),
    path('abastecimentos/pendentes/<int:id>/rejeitar/', rejeitar_abastecimento, name='rejeitar_abastecimento'),
    path('abastecimentos/pendentes/estatisticas/', estatisticas_abastecimentos_pendentes, name='estatisticas_abastecimentos_pendentes'),
    
    # Rotas de motoristas
    path('motoristas/', listar_motoristas, name='listar_motoristas'),
    path('motoristas/novo/', criar_motorista, name='criar_motorista'),
    path('motoristas/<int:pk>/', detalhe_motorista, name='detalhe_motorista'),
    path('motoristas/<int:pk>/editar/', editar_motorista, name='editar_motorista'),
    path('motoristas/<int:pk>/resetar-senha/', resetar_senha_motorista, name='resetar_senha_motorista'),
    path('motoristas/<int:pk>/excluir/', excluir_motorista, name='excluir_motorista'),
]