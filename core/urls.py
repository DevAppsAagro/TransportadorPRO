from django.urls import path
from django.contrib.auth import views as auth_views
from .views import dashboard, financeiro, veiculos, relatorios, configuracao
from .views.auth_views import register
from .views.contatos import contatos, contato_novo, contato_editar, contato_excluir
from .views.categorias import categorias, categoria_nova, categoria_editar, categoria_excluir, subcategorias, subcategoria_nova, subcategoria_editar, subcategoria_excluir
from .views.cargas import cargas, carga_nova, carga_editar, carga_excluir
from .views.caminhoes import caminhoes, caminhao_novo, caminhao_editar, caminhao_excluir
from .views.carretas import lista_carretas, criar_carreta, editar_carreta, excluir_carreta
from .views.conjuntos import conjuntos, conjunto_novo, conjunto_editar, conjunto_excluir
from .views.fretes import fretes, frete_novo, frete_editar, frete_excluir, frete_detalhes
from .views.abastecimentos import abastecimentos, abastecimento_novo, abastecimento_editar, abastecimento_excluir
from .views.estimativa_pneus import estimativa_pneus_list, estimativa_pneus_create, estimativa_pneus_edit, estimativa_pneus_delete, detalhes_estimativa
from .views.estimativa_manutencao import estimativa_manutencao_list, estimativa_manutencao_create, estimativa_manutencao_edit, estimativa_manutencao_delete, detalhes_estimativa_manutencao
from .views.estimativa_custo_fixo import estimativa_custo_fixo_list, estimativa_custo_fixo_create, estimativa_custo_fixo_edit, estimativa_custo_fixo_delete, detalhes_estimativa_custo_fixo, calcular_valor_por_dia
from .views.despesa import despesa_list, despesa_create, despesa_edit, despesa_delete, despesa_detail, registrar_pagamento, get_subcategorias, get_destinos_por_alocacao
from .views.relatorios import relatorio_veiculo, relatorio_frete, fluxo_caixa, dre, relatorio_cliente
from .views.configuracoes import configuracoes_empresa

app_name = 'core'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('financeiro/', financeiro, name='financeiro'),
    path('veiculos/', veiculos, name='veiculos'),
    path('contatos/', contatos, name='contatos'),
    path('contatos/novo/', contato_novo, name='contato_novo'),
    path('contatos/<int:pk>/editar/', contato_editar, name='contato_editar'),
    path('contatos/<int:pk>/excluir/', contato_excluir, name='contato_excluir'),
    path('relatorios/', relatorios, name='relatorios'),
    path('relatorios/veiculo/', relatorio_veiculo, name='relatorio_veiculo'),
    path('relatorios/frete/', relatorio_frete, name='relatorio_frete'),
    path('relatorios/frete/<int:pk>/', relatorio_frete, name='relatorio_frete_detalhe'),
    path('relatorios/fluxo-caixa/', fluxo_caixa, name='fluxo_caixa'),
    path('relatorios/dre/', dre, name='dre'),
    path('relatorios/cliente/', relatorio_cliente, name='relatorio_cliente'),
    
    # Configurações
    path('configuracoes/empresa/', configuracoes_empresa, name='configuracoes_empresa'),
    
    # Rotas de categorias
    path('categorias/', categorias, name='categorias'),
    path('categorias/nova/', categoria_nova, name='categoria_nova'),
    path('categorias/<int:id>/editar/', categoria_editar, name='categoria_editar'),
    path('categorias/<int:id>/excluir/', categoria_excluir, name='categoria_excluir'),
    
    # Rotas de subcategorias
    path('categorias/<int:categoria_id>/subcategorias/', subcategorias, name='subcategorias'),
    path('categorias/<int:categoria_id>/subcategorias/nova/', subcategoria_nova, name='subcategoria_nova'),
    path('categorias/<int:categoria_id>/subcategorias/<int:id>/editar/', subcategoria_editar, name='subcategoria_editar'),
    path('categorias/<int:categoria_id>/subcategorias/<int:id>/excluir/', subcategoria_excluir, name='subcategoria_excluir'),
    
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
    
    # Rotas de carretas
    path('carretas/', lista_carretas, name='carretas'),
    path('carretas/nova/', criar_carreta, name='carreta_nova'),
    path('carretas/<int:pk>/editar/', editar_carreta, name='carreta_editar'),
    path('carretas/<int:pk>/excluir/', excluir_carreta, name='carreta_excluir'),
    
    # Rotas de conjuntos
    path('conjuntos/', conjuntos, name='conjuntos'),
    path('conjuntos/novo/', conjunto_novo, name='conjunto_novo'),
    path('conjuntos/<int:id>/editar/', conjunto_editar, name='conjunto_editar'),
    path('conjuntos/<int:id>/excluir/', conjunto_excluir, name='conjunto_excluir'),
    
    # Rotas de fretes
    path('fretes/', fretes, name='fretes'),
    path('fretes/novo/', frete_novo, name='frete_novo'),
    path('fretes/<int:pk>/editar/', frete_editar, name='frete_editar'),
    path('fretes/<int:pk>/excluir/', frete_excluir, name='frete_excluir'),
    path('fretes/<int:pk>/detalhes/', frete_detalhes, name='frete_detalhes'),
    
    # Rotas de abastecimentos
    path('abastecimentos/', abastecimentos, name='abastecimentos'),
    path('abastecimentos/novo/', abastecimento_novo, name='abastecimento_novo'),
    path('abastecimentos/<int:pk>/editar/', abastecimento_editar, name='abastecimento_editar'),
    path('abastecimentos/<int:pk>/excluir/', abastecimento_excluir, name='abastecimento_excluir'),
    
    # Rotas de autenticação
    path('login/', auth_views.LoginView.as_view(template_name='core/auth/login.html'), name='login'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='core/auth/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='core/auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core/auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='core/auth/password_reset_complete.html'), name='password_reset_complete'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:login'), name='logout'),
    path('register/', register, name='register'),
    
    # Rotas de estimativa de pneus
    path('estimativa-pneus/', estimativa_pneus_list, name='estimativa_pneus_list'),
    path('estimativa-pneus/nova/', estimativa_pneus_create, name='estimativa_pneus_create'),
    path('estimativa-pneus/<int:pk>/editar/', estimativa_pneus_edit, name='estimativa_pneus_edit'),
    path('estimativa-pneus/<int:pk>/excluir/', estimativa_pneus_delete, name='estimativa_pneus_delete'),
    path('estimativa-pneus/<int:pk>/detalhes/', detalhes_estimativa, name='detalhes_estimativa'),
    
    # Rotas de estimativa de manutenção
    path('estimativa-manutencao/', estimativa_manutencao_list, name='estimativa_manutencao_list'),
    path('estimativa-manutencao/nova/', estimativa_manutencao_create, name='estimativa_manutencao_create'),
    path('estimativa-manutencao/<int:pk>/editar/', estimativa_manutencao_edit, name='estimativa_manutencao_edit'),
    path('estimativa-manutencao/<int:pk>/excluir/', estimativa_manutencao_delete, name='estimativa_manutencao_delete'),
    path('estimativa-manutencao/<int:pk>/detalhes/', detalhes_estimativa_manutencao, name='detalhes_estimativa_manutencao'),
    
    # Rotas de estimativa de custo fixo
    path('estimativa-custo-fixo/', estimativa_custo_fixo_list, name='estimativa_custo_fixo_list'),
    path('estimativa-custo-fixo/nova/', estimativa_custo_fixo_create, name='estimativa_custo_fixo_create'),
    path('estimativa-custo-fixo/<int:pk>/editar/', estimativa_custo_fixo_edit, name='estimativa_custo_fixo_edit'),
    path('estimativa-custo-fixo/<int:pk>/excluir/', estimativa_custo_fixo_delete, name='estimativa_custo_fixo_delete'),
    path('estimativa-custo-fixo/<int:pk>/detalhes/', detalhes_estimativa_custo_fixo, name='detalhes_estimativa_custo_fixo'),
    path('api/calcular-valor-por-dia/', calcular_valor_por_dia, name='calcular_valor_por_dia'),
    
    # Rotas de despesas
    path('despesas/', despesa_list, name='despesa_list'),
    path('despesas/nova/', despesa_create, name='despesa_create'),
    path('despesas/<int:pk>/editar/', despesa_edit, name='despesa_edit'),
    path('despesas/<int:pk>/excluir/', despesa_delete, name='despesa_delete'),
    path('despesas/<int:pk>/detalhes/', despesa_detail, name='despesa_detail'),
    path('despesas/<int:pk>/registrar-pagamento/', registrar_pagamento, name='registrar_pagamento'),
    path('api/subcategorias/', get_subcategorias, name='get_subcategorias'),
    path('api/destinos-por-alocacao/', get_destinos_por_alocacao, name='get_destinos_por_alocacao'),
]