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
        caminhao__usuario=request.user,
        data_saida__year=ano_atual,
        data_saida__month=mes_atual
    ).aggregate(
        total=Coalesce(Sum('valor_total'), Decimal('0'))
    )['total']
    
    # Despesas do mês
    despesas_mes = Despesa.objects.filter(
        Q(caminhao__usuario=request.user) | 
        Q(carreta__usuario=request.user) | 
        Q(frete__caminhao__usuario=request.user) | 
        Q(empresa__usuario=request.user),
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual
    ).aggregate(
        total=Coalesce(Sum('valor'), Decimal('0'))
    )['total']
    
    # Despesas pagas do mês
    despesas_pagas_mes = Despesa.objects.filter(
        Q(caminhao__usuario=request.user) | 
        Q(carreta__usuario=request.user) | 
        Q(frete__caminhao__usuario=request.user) | 
        Q(empresa__usuario=request.user),
        data_pagamento__isnull=False,
        data_pagamento__year=ano_atual,
        data_pagamento__month=mes_atual
    ).aggregate(
        total=Coalesce(Sum('valor'), Decimal('0'))
    )['total']
    
    # Despesas a pagar do mês
    despesas_a_pagar_mes = Despesa.objects.filter(
        Q(caminhao__usuario=request.user) | 
        Q(carreta__usuario=request.user) | 
        Q(frete__caminhao__usuario=request.user) | 
        Q(empresa__usuario=request.user),
        data_pagamento__isnull=True,
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual
    ).aggregate(
        total=Coalesce(Sum('valor'), Decimal('0'))
    )['total']
    
    # Saldo do mês
    saldo_mes = receitas_mes - despesas_mes
    
    # === RESUMO DE FRETES ===
    # Total de fretes
    total_fretes = Frete.objects.filter(caminhao__usuario=request.user).count()
    
    # Fretes em andamento
    fretes_andamento = Frete.objects.filter(
        caminhao__usuario=request.user,
        data_chegada__isnull=True
    ).count()
    
    # Fretes concluídos
    fretes_concluidos = Frete.objects.filter(
        caminhao__usuario=request.user,
        data_chegada__isnull=False
    ).count()
    
    # === RESUMO DE VEÍCULOS ===
    # Total de caminhões
    total_caminhoes = Caminhao.objects.filter(usuario=request.user).count()
    
    # Caminhões ativos
    caminhoes_ativos = Caminhao.objects.filter(
        usuario=request.user,
        status='ATIVO'
    ).count()
    
    # Total de carretas
    total_carretas = Carreta.objects.filter(usuario=request.user).count()
    
    # Carretas ativas
    carretas_ativas = Carreta.objects.filter(
        usuario=request.user,
        status='ATIVO'
    ).count()
    
    # === GRÁFICO DE RECEITAS E DESPESAS ===
    # Definir o período para o gráfico
    data_fim = hoje
    data_inicio = hoje.replace(day=1)
    data_inicio = data_inicio.replace(month=((data_inicio.month - periodo) % 12) or 12)
    if data_inicio.month > hoje.month:
        data_inicio = data_inicio.replace(year=data_inicio.year - 1)
    
    # Dados para o gráfico
    dados_grafico = []
    
    # Iterar pelos meses do período
    data_atual = data_inicio
    while data_atual <= data_fim:
        ano_mes = data_atual.year * 100 + data_atual.month  # Formato YYYYMM
        
        # Receitas do mês
        receitas = Frete.objects.filter(
            caminhao__usuario=request.user,
            data_saida__year=data_atual.year,
            data_saida__month=data_atual.month
        ).aggregate(
            total=Coalesce(Sum('valor_total'), Decimal('0'))
        )['total']
        
        # Despesas do mês
        despesas = Despesa.objects.filter(
            Q(caminhao__usuario=request.user) | 
            Q(carreta__usuario=request.user) | 
            Q(frete__caminhao__usuario=request.user) | 
            Q(empresa__usuario=request.user),
            data_vencimento__year=data_atual.year,
            data_vencimento__month=data_atual.month
        ).aggregate(
            total=Coalesce(Sum('valor'), Decimal('0'))
        )['total']
        
        # Adicionar ao gráfico
        dados_grafico.append({
            'mes': data_atual.strftime('%b/%Y'),
            'receitas': float(receitas),
            'despesas': float(despesas),
            'saldo': float(receitas - despesas)
        })
        
        # Avançar para o próximo mês
        if data_atual.month == 12:
            data_atual = data_atual.replace(year=data_atual.year + 1, month=1)
        else:
            data_atual = data_atual.replace(month=data_atual.month + 1)
    
    # === DESPESAS PENDENTES ===
    despesas_pendentes = Despesa.objects.filter(
        Q(caminhao__usuario=request.user) | 
        Q(carreta__usuario=request.user) | 
        Q(frete__caminhao__usuario=request.user) | 
        Q(empresa__usuario=request.user),
        data_pagamento__isnull=True,
        data_vencimento__lte=hoje + timedelta(days=7)
    ).order_by('data_vencimento')[:5]
    
    # === FRETES RECENTES ===
    fretes_recentes = Frete.objects.filter(
        caminhao__usuario=request.user
    ).order_by('-data_saida')[:5]
    
    # === CONTATOS ===
    # Total de contatos
    total_contatos = Contato.objects.filter(usuario=request.user).count()
    
    # Contatos por tipo
    contatos_por_tipo = Contato.objects.filter(
        usuario=request.user
    ).values('tipo').annotate(
        total=Count('id')
    ).order_by('tipo')
    
    # Converter para dicionário para fácil acesso no template
    contatos_dict = {item['tipo']: item['total'] for item in contatos_por_tipo}
    
    # Obter contagens específicas por tipo
    total_clientes = contatos_dict.get('CLIENTE', 0)
    total_fornecedores = contatos_dict.get('FORNECEDOR', 0)
    total_motoristas = contatos_dict.get('MOTORISTA', 0)
    total_funcionarios = contatos_dict.get('FUNCIONARIO', 0)
    
    # === CATEGORIAS DE DESPESAS ===
    # Top 5 categorias de despesas do mês
    top_categorias = Despesa.objects.filter(
        Q(caminhao__usuario=request.user) | 
        Q(carreta__usuario=request.user) | 
        Q(frete__caminhao__usuario=request.user) | 
        Q(empresa__usuario=request.user),
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual
    ).values(
        'categoria__nome'
    ).annotate(
        total=Sum('valor')
    ).order_by('-total')[:5]
    
    # Converter para formato adequado para o gráfico
    dados_categorias = []
    for cat in top_categorias:
        if cat['categoria__nome']:  # Verificar se o nome da categoria não é None
            dados_categorias.append({
                'categoria': cat['categoria__nome'],
                'valor': float(cat['total'])
            })
    
    # Converter para JSON para uso no JavaScript
    dados_grafico_json = json.dumps(dados_grafico)
    dados_categorias_json = json.dumps(dados_categorias)
    
    # Preparar dados específicos para os gráficos
    meses_labels = [item['mes'] for item in dados_grafico]
    dados_receitas = [item['receitas'] for item in dados_grafico]
    dados_despesas = [item['despesas'] for item in dados_grafico]
    
    categorias_labels = [item['categoria'] for item in dados_categorias]
    categorias_valores = [item['valor'] for item in dados_categorias]
    
    context = {
        'receitas_mes': receitas_mes,
        'despesas_mes': despesas_mes,
        'despesas_pagas_mes': despesas_pagas_mes,
        'despesas_a_pagar_mes': despesas_a_pagar_mes,
        'resultado_mes': saldo_mes,  # Renomeado para corresponder ao template
        'total_fretes': total_fretes,
        'fretes_em_andamento': fretes_andamento,  # Renomeado para corresponder ao template
        'fretes_concluidos_mes': fretes_concluidos,  # Renomeado para corresponder ao template
        'total_fretes_mes': Frete.objects.filter(
            caminhao__usuario=request.user,
            data_saida__year=ano_atual,
            data_saida__month=mes_atual
        ).count(),  # Adicionado total de fretes do mês
        'total_caminhoes': total_caminhoes,
        'total_caminhoes_ativos': caminhoes_ativos,  # Renomeado para corresponder ao template
        'total_carretas': total_carretas,
        'total_carretas_ativas': carretas_ativas,  # Renomeado para corresponder ao template
        'total_conjuntos_ativos': Conjunto.objects.filter(
            usuario=request.user,
            status='ATIVO'
        ).count(),  # Adicionado total de conjuntos ativos
        'despesas_pendentes': despesas_pendentes,
        'fretes_recentes': fretes_recentes,
        'total_contatos': total_contatos,
        'total_clientes': total_clientes,
        'total_fornecedores': total_fornecedores,
        'total_motoristas': total_motoristas,
        'total_funcionarios': total_funcionarios,
        'dados_grafico_json': dados_grafico_json,
        'dados_categorias_json': dados_categorias_json,
        'meses_labels': json.dumps(meses_labels),
        'dados_receitas': json.dumps(dados_receitas),
        'dados_despesas': json.dumps(dados_despesas),
        'categorias_labels': json.dumps(categorias_labels),
        'categorias_valores': json.dumps(categorias_valores),
        'periodo': periodo,
        'periodos_disponiveis': [3, 6, 12],  # Adicionado períodos disponíveis para o dropdown
        'data_atual': hoje,  # Adicionado data atual
        'nome_mes_atual': {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }[mes_atual]  # Adicionado nome do mês atual
    }
    
    return render(request, 'core/dashboard/dashboard.html', context)