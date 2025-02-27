from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import datetime, timedelta
from core.models.frete import Frete
from core.models.despesa import Despesa
from core.models.conjunto import Conjunto
from core.models.caminhao import Caminhao
from core.models.carreta import Carreta
from core.models.contato import Contato
from core.models.categoria import Categoria
import json

@login_required
def dashboard(request):
    # Data atual e períodos
    hoje = datetime.now().date()
    primeiro_dia_mes = hoje.replace(day=1)
    ultimo_dia_mes = (primeiro_dia_mes.replace(month=primeiro_dia_mes.month % 12 + 1, day=1) - timedelta(days=1)) if primeiro_dia_mes.month < 12 else primeiro_dia_mes.replace(year=primeiro_dia_mes.year + 1, month=1, day=1) - timedelta(days=1)
    
    # Ano e mês atual
    ano_atual = hoje.year
    mes_atual = hoje.month
    
    # Parâmetros para personalizar o período do gráfico
    periodo = request.GET.get('periodo', '6')  # Padrão: 6 meses
    try:
        periodo = int(periodo)
        if periodo <= 0:
            periodo = 6
    except ValueError:
        periodo = 6
    
    # === RESUMO FINANCEIRO DO MÊS ATUAL ===
    # Receitas do mês (fretes)
    receitas_mes = Frete.objects.filter(
        data_saida__year=ano_atual,
        data_saida__month=mes_atual
    ).aggregate(
        total=Coalesce(Sum('valor_total'), Decimal('0'))
    )['total']
    
    # Despesas do mês
    despesas_mes = Despesa.objects.filter(
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual
    ).aggregate(
        total=Coalesce(Sum('valor'), Decimal('0'))
    )['total']
    
    # Despesas pagas do mês
    despesas_pagas_mes = Despesa.objects.filter(
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual,
        data_pagamento__isnull=False
    ).aggregate(
        total=Coalesce(Sum('valor'), Decimal('0'))
    )['total']
    
    # Despesas a pagar do mês
    despesas_a_pagar_mes = Despesa.objects.filter(
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual,
        data_pagamento__isnull=True
    ).aggregate(
        total=Coalesce(Sum('valor'), Decimal('0'))
    )['total']
    
    # Resultado do mês (receitas - despesas)
    resultado_mes = receitas_mes - despesas_mes
    
    # === RESUMO DE FRETES ===
    # Total de fretes no mês
    total_fretes_mes = Frete.objects.filter(
        data_saida__year=ano_atual,
        data_saida__month=mes_atual
    ).count()
    
    # Fretes em andamento
    fretes_em_andamento = Frete.objects.filter(
        status='EM_ANDAMENTO'
    ).count()
    
    # Fretes concluídos no mês
    fretes_concluidos_mes = Frete.objects.filter(
        data_saida__year=ano_atual,
        data_saida__month=mes_atual,
        status='CONCLUIDO'
    ).count()
    
    # === RESUMO DE VEÍCULOS ===
    # Total de caminhões ativos
    total_caminhoes_ativos = Caminhao.objects.filter(
        status='ATIVO'
    ).count()
    
    # Total de carretas ativas
    total_carretas_ativas = Carreta.objects.filter(
        status='ATIVO'
    ).count()
    
    # Total de conjuntos ativos
    total_conjuntos_ativos = Conjunto.objects.filter(
        status='ATIVO'
    ).count()
    
    # === DADOS PARA GRÁFICOS ===
    # Dados para o gráfico de receitas e despesas (últimos X meses)
    meses_labels = []
    dados_receitas = []
    dados_despesas = []
    
    for i in range(periodo-1, -1, -1):
        data_ref = hoje.replace(day=1) - timedelta(days=1) * i * 30  # Aproximação de meses
        ano_idx = data_ref.year
        mes_idx = data_ref.month
        
        nome_mes = {
            1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
            5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
            9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
        }[mes_idx]
        
        meses_labels.append(f"{nome_mes}/{str(ano_idx)[2:]}")
        
        # Receitas do mês
        receita_mes = Frete.objects.filter(
            data_saida__year=ano_idx,
            data_saida__month=mes_idx
        ).aggregate(
            total=Coalesce(Sum('valor_total'), Decimal('0'))
        )['total']
        
        # Despesas do mês
        despesa_mes = Despesa.objects.filter(
            data_vencimento__year=ano_idx,
            data_vencimento__month=mes_idx
        ).aggregate(
            total=Coalesce(Sum('valor'), Decimal('0'))
        )['total']
        
        dados_receitas.append(float(receita_mes))
        dados_despesas.append(float(despesa_mes))
    
    # === TOP 5 DESPESAS POR CATEGORIA NO MÊS ATUAL ===
    # Buscar as categorias e seus nomes
    top_categorias_query = Despesa.objects.filter(
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual
    ).values('categoria').annotate(
        total=Sum('valor')
    ).order_by('-total')[:5]
    
    # Mapear IDs de categoria para nomes
    categorias_ids = [item['categoria'] for item in top_categorias_query]
    categorias_map = {cat.id: cat.nome for cat in Categoria.objects.filter(id__in=categorias_ids)}
    
    # Criar listas para o gráfico
    categorias_labels = []
    categorias_valores = []
    
    for item in top_categorias_query:
        categoria_id = item['categoria']
        categoria_nome = categorias_map.get(categoria_id, f"Categoria {categoria_id}")
        categorias_labels.append(categoria_nome)
        categorias_valores.append(float(item['total']))
    
    # === CONTATOS ===
    total_clientes = Contato.objects.filter(tipo='CLIENTE').count()
    total_fornecedores = Contato.objects.filter(tipo='FORNECEDOR').count()
    total_motoristas = Contato.objects.filter(tipo='MOTORISTA').count()
    
    context = {
        # Resumo financeiro
        'receitas_mes': receitas_mes,
        'despesas_mes': despesas_mes,
        'despesas_pagas_mes': despesas_pagas_mes,
        'despesas_a_pagar_mes': despesas_a_pagar_mes,
        'resultado_mes': resultado_mes,
        
        # Resumo de fretes
        'total_fretes_mes': total_fretes_mes,
        'fretes_em_andamento': fretes_em_andamento,
        'fretes_concluidos_mes': fretes_concluidos_mes,
        
        # Resumo de veículos
        'total_caminhoes_ativos': total_caminhoes_ativos,
        'total_carretas_ativas': total_carretas_ativas,
        'total_conjuntos_ativos': total_conjuntos_ativos,
        
        # Resumo de contatos
        'total_clientes': total_clientes,
        'total_fornecedores': total_fornecedores,
        'total_motoristas': total_motoristas,
        
        # Dados para gráficos
        'meses_labels': json.dumps(meses_labels),
        'dados_receitas': json.dumps(dados_receitas),
        'dados_despesas': json.dumps(dados_despesas),
        'categorias_labels': json.dumps(categorias_labels),
        'categorias_valores': json.dumps(categorias_valores),
        
        # Configurações de período
        'periodo': periodo,
        'periodos_disponiveis': [3, 6, 12],
        
        # Data atual
        'data_atual': hoje,
        'nome_mes_atual': {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }[mes_atual],
    }
    
    return render(request, 'core/dashboard/dashboard.html', context)