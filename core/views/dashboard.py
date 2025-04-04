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
from core.models.abastecimento import Abastecimento
import json

@login_required
def dashboard(request):
    # Data atual e períodos
    hoje = datetime.now().date()
    
    # Obter mês e ano do filtro ou usar o atual
    mes_filtro = request.GET.get('mes')
    ano_filtro = request.GET.get('ano')
    
    try:
        mes_atual = int(mes_filtro) if mes_filtro else hoje.month
        ano_atual = int(ano_filtro) if ano_filtro else hoje.year
        
        # Validar mês e ano
        if mes_atual < 1 or mes_atual > 12:
            mes_atual = hoje.month
        if ano_atual < 2000 or ano_atual > 2100:
            ano_atual = hoje.year
    except (ValueError, TypeError):
        mes_atual = hoje.month
        ano_atual = hoje.year
    
    # Criar data de referência com o mês e ano selecionados
    data_referencia = hoje.replace(year=ano_atual, month=mes_atual, day=1)
    
    # Calcular o último dia do mês selecionado
    if mes_atual == 12:
        ultimo_dia_mes = data_referencia.replace(year=ano_atual + 1, month=1, day=1) - timedelta(days=1)
    else:
        ultimo_dia_mes = data_referencia.replace(month=mes_atual + 1, day=1) - timedelta(days=1)
    
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
    
    # Despesas do mês (incluindo despesas e abastecimentos)
    despesas_mes_despesas = Despesa.objects.filter(
        Q(caminhao__usuario=request.user) | 
        Q(carreta__usuario=request.user) | 
        Q(frete__caminhao__usuario=request.user) | 
        Q(empresa__usuario=request.user),
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual
    ).aggregate(
        total=Coalesce(Sum('valor'), Decimal('0'))
    )['total']
    
    # Abastecimentos do mês
    abastecimentos_mes = Abastecimento.objects.filter(
        caminhao__usuario=request.user,
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual
    ).aggregate(
        total=Coalesce(Sum('total_valor'), Decimal('0'))
    )['total']
    
    # Total de abastecimentos do mês (valor para exibir no template)
    total_abastecimentos_mes = abastecimentos_mes
    
    # Total de despesas (despesas + abastecimentos)
    despesas_mes = despesas_mes_despesas + abastecimentos_mes
    
    # Cálculo do lucro do mês (receitas - despesas)
    lucro_mes = receitas_mes - despesas_mes
    
    # Despesas pagas do mês (incluindo despesas e abastecimentos)
    despesas_pagas_mes_despesas = Despesa.objects.filter(
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
    
    # Abastecimentos pagos do mês
    abastecimentos_pagos_mes = Abastecimento.objects.filter(
        caminhao__usuario=request.user,
        data_pagamento__isnull=False,
        data_pagamento__year=ano_atual,
        data_pagamento__month=mes_atual
    ).aggregate(
        total=Coalesce(Sum('total_valor'), Decimal('0'))
    )['total']
    
    # Total de despesas pagas (despesas + abastecimentos)
    despesas_pagas_mes = despesas_pagas_mes_despesas + abastecimentos_pagos_mes
    
    # Despesas a pagar do mês (incluindo despesas e abastecimentos)
    despesas_a_pagar_mes_despesas = Despesa.objects.filter(
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
    
    # Abastecimentos a pagar do mês
    abastecimentos_a_pagar_mes = Abastecimento.objects.filter(
        caminhao__usuario=request.user,
        data_pagamento__isnull=True,
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual
    ).aggregate(
        total=Coalesce(Sum('total_valor'), Decimal('0'))
    )['total']
    
    # Total de despesas a pagar (despesas + abastecimentos)
    despesas_a_pagar_mes = despesas_a_pagar_mes_despesas + abastecimentos_a_pagar_mes
    
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
    
    # Conjuntos ativos (caminhão + carreta)
    # Um conjunto é considerado quando um caminhão está associado a uma carreta no modelo Conjunto
    from core.models.conjunto import Conjunto
    conjuntos_ativos = Conjunto.objects.filter(
        usuario=request.user,
        status='ATIVO',
        caminhao__status='ATIVO'
    ).count()
    
    # === NOVAS MÉTRICAS ===
    # Quantidade rodada por caminhão no mês atual
    km_por_caminhao = []
    caminhoes = Caminhao.objects.filter(usuario=request.user, status='ATIVO')
    for caminhao in caminhoes:
        # Calcular km rodados no mês (diferença entre km final e inicial dos fretes)
        fretes_caminhao = Frete.objects.filter(
            caminhao=caminhao,
            data_saida__year=ano_atual,
            data_saida__month=mes_atual,
            data_chegada__isnull=False  # Apenas fretes concluídos
        )
        
        km_rodados = 0
        for frete in fretes_caminhao:
            if frete.km_chegada and frete.km_saida:
                km_rodados += (frete.km_chegada - frete.km_saida)
        
        if km_rodados > 0:
            km_por_caminhao.append({
                'caminhao': caminhao.placa,
                'km_rodados': km_rodados
            })
    
    # Ordenar por km rodados (decrescente)
    km_por_caminhao = sorted(km_por_caminhao, key=lambda x: x['km_rodados'], reverse=True)[:5]
    
    # Média de km/l por veículo no mês atual
    media_kml_por_caminhao = []
    for caminhao in caminhoes:
        # Obter todos os abastecimentos do mês
        abastecimentos_caminhao = Abastecimento.objects.filter(
            caminhao=caminhao,
            data__year=ano_atual,
            data__month=mes_atual
        )
        
        total_litros = 0
        for abastecimento in abastecimentos_caminhao:
            total_litros += abastecimento.litros
        
        # Calcular km rodados no mês
        fretes_caminhao = Frete.objects.filter(
            caminhao=caminhao,
            data_saida__year=ano_atual,
            data_saida__month=mes_atual,
            data_chegada__isnull=False  # Apenas fretes concluídos
        )
        
        km_rodados = 0
        for frete in fretes_caminhao:
            if frete.km_chegada and frete.km_saida:
                km_rodados += (frete.km_chegada - frete.km_saida)
        
        # Calcular média de km/l
        if total_litros > 0 and km_rodados > 0:
            media_kml = km_rodados / float(total_litros)
            media_kml_por_caminhao.append({
                'caminhao': caminhao.placa,
                'media_kml': round(media_kml, 2)
            })
    
    # Ordenar por média de km/l (decrescente)
    media_kml_por_caminhao = sorted(media_kml_por_caminhao, key=lambda x: x['media_kml'], reverse=True)[:5]
    
    # Receitas por veículo no mês atual
    receitas_por_caminhao = []
    for caminhao in caminhoes:
        # Calcular receitas dos fretes no mês
        receita_total = Frete.objects.filter(
            caminhao=caminhao,
            data_saida__year=ano_atual,
            data_saida__month=mes_atual
        ).aggregate(
            total=Coalesce(Sum('valor_total'), Decimal('0'))
        )['total']
        
        if receita_total > 0:
            receitas_por_caminhao.append({
                'caminhao': caminhao.placa,
                'receita': float(receita_total)
            })
    
    # Ordenar por receita (decrescente)
    receitas_por_caminhao = sorted(receitas_por_caminhao, key=lambda x: x['receita'], reverse=True)[:5]
    
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
        
        # Despesas do mês (incluindo despesas e abastecimentos)
        despesas_mes_despesas = Despesa.objects.filter(
            Q(caminhao__usuario=request.user) | 
            Q(carreta__usuario=request.user) | 
            Q(frete__caminhao__usuario=request.user) | 
            Q(empresa__usuario=request.user),
            data_vencimento__year=data_atual.year,
            data_vencimento__month=data_atual.month
        ).aggregate(
            total=Coalesce(Sum('valor'), Decimal('0'))
        )['total']
        
        # Abastecimentos do mês
        abastecimentos_mes = Abastecimento.objects.filter(
            caminhao__usuario=request.user,
            data_vencimento__year=data_atual.year,
            data_vencimento__month=data_atual.month
        ).aggregate(
            total=Coalesce(Sum('total_valor'), Decimal('0'))
        )['total']
        
        # Total de despesas (despesas + abastecimentos)
        despesas = despesas_mes_despesas + abastecimentos_mes
        
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
    # Top 5 categorias de despesas do mês (despesas regulares)
    top_categorias_despesas = Despesa.objects.filter(
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
    
    # Calculando o total de abastecimentos para adicionar como categoria
    total_abastecimentos = Abastecimento.objects.filter(
        caminhao__usuario=request.user,
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual
    ).aggregate(
        total=Coalesce(Sum('total_valor'), Decimal('0'))
    )['total']
    
    # Criando uma lista para armazenar todas as categorias
    top_categorias = list(top_categorias_despesas)
    
    # Adicionando abastecimentos como uma categoria se houver valor
    if total_abastecimentos > 0:
        top_categorias.append({
            'categoria__nome': 'Abastecimentos',
            'total': total_abastecimentos
        })
        
    # Reordenando a lista por valor total
    top_categorias = sorted(top_categorias, key=lambda x: x['total'], reverse=True)[:5]
    
    # Converter para formato adequado para o gráfico
    dados_categorias = []
    for cat in top_categorias:
        if cat['categoria__nome']:  # Verificar se o nome da categoria não é None
            dados_categorias.append({
                'categoria': cat['categoria__nome'],
                'valor': float(cat['total'])
            })
    
    # Extrair labels e valores para o gráfico
    categorias_labels = [item['categoria'] for item in dados_categorias]
    categorias_valores = [item['valor'] for item in dados_categorias]
    
    # Contagem de abastecimentos do mês
    abastecimentos_count_mes = Abastecimento.objects.filter(
        caminhao__usuario=request.user,
        data__year=ano_atual,
        data__month=mes_atual
    ).count()
    
    # === FRETES ===
    # Total de fretes do mês
    total_fretes_mes = Frete.objects.filter(
        caminhao__usuario=request.user,
        data_saida__year=ano_atual,
        data_saida__month=mes_atual
    ).count()
    
    # Fretes em andamento
    fretes_em_andamento = Frete.objects.filter(
        caminhao__usuario=request.user,
        status='EM_ANDAMENTO'
    ).count()
    
    # Fretes concluídos no mês
    fretes_concluidos_mes = Frete.objects.filter(
        caminhao__usuario=request.user,
        status='CONCLUIDO',
        data_chegada__year=ano_atual,
        data_chegada__month=mes_atual
    ).count()
    
    # Preparar dados para o gráfico de receitas e despesas
    dados_grafico = []
    # Obter dados dos últimos 6 meses
    for i in range(periodo - 1, -1, -1):
        # Calcular mês e ano
        mes_graf = mes_atual - i
        ano_graf = ano_atual
        
        # Ajustar mês e ano se necessário
        while mes_graf <= 0:
            mes_graf += 12
            ano_graf -= 1
            
        # Obter receitas do mês
        receitas_mes_graf = Frete.objects.filter(
            caminhao__usuario=request.user,
            data_saida__year=ano_graf,
            data_saida__month=mes_graf
        ).aggregate(
            total=Coalesce(Sum('valor_total'), Decimal('0'))
        )['total']
        
        # Obter despesas do mês
        despesas_mes_graf = Despesa.objects.filter(
            Q(caminhao__usuario=request.user) | 
            Q(carreta__usuario=request.user) | 
            Q(frete__caminhao__usuario=request.user) | 
            Q(empresa__usuario=request.user),
            data_vencimento__year=ano_graf,
            data_vencimento__month=mes_graf
        ).aggregate(
            total=Coalesce(Sum('valor'), Decimal('0'))
        )['total']
        
        # Obter abastecimentos do mês
        abastecimentos_mes_graf = Abastecimento.objects.filter(
            caminhao__usuario=request.user,
            data_vencimento__year=ano_graf,
            data_vencimento__month=mes_graf
        ).aggregate(
            total=Coalesce(Sum('total_valor'), Decimal('0'))
        )['total']
        
        # Total de despesas
        despesas_total_graf = despesas_mes_graf + abastecimentos_mes_graf
        
        # Nome do mês
        nome_mes = {
            1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
            5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
            9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
        }[mes_graf]
        
        # Adicionar dados ao gráfico
        dados_grafico.append({
            'mes': nome_mes,
            'receitas': float(receitas_mes_graf),
            'despesas': float(despesas_total_graf)
        })
    
    # Preparar dados específicos para os gráficos
    meses_labels = [item['mes'] for item in dados_grafico]
    dados_receitas = [item['receitas'] for item in dados_grafico]
    dados_despesas = [item['despesas'] for item in dados_grafico]
    
    # Preparar dados para o gráfico de receitas e despesas
    dados_grafico_receitas_despesas = []
    for i, mes in enumerate(meses_labels):
        dados_grafico_receitas_despesas.append({
            'mes': mes,
            'receitas': dados_receitas[i],
            'despesas': dados_despesas[i]
        })
    
    # Preparar dados para o gráfico de categorias
    dados_grafico_categorias = []
    for i, categoria in enumerate(categorias_labels):
        if i < len(categorias_valores):
            dados_grafico_categorias.append({
                'categoria': categoria,
                'valor': categorias_valores[i]
            })
    
    # Preparar strings JSON para uso no template
    dados_grafico_json = json.dumps(dados_grafico)
    dados_categorias_json = json.dumps(dados_grafico_categorias)
    
    # Preparar contexto para o template
    context = {
        # Dados financeiros
        'receitas_mes': receitas_mes,
        'despesas_mes': despesas_mes,
        'despesas_pagas_mes': despesas_pagas_mes,
        'despesas_a_pagar_mes': despesas_a_pagar_mes,
        'lucro_mes': lucro_mes,
        'resultado_mes': saldo_mes,
        'total_abastecimentos_mes': total_abastecimentos_mes,
        'dados_grafico_receitas_despesas': json.dumps(dados_grafico_receitas_despesas),
        'dados_grafico_categorias': json.dumps(dados_grafico_categorias),
        'meses_labels': json.dumps(meses_labels),
        'dados_receitas': json.dumps(dados_receitas),
        'dados_despesas': json.dumps(dados_despesas),
        'categorias_labels': json.dumps(categorias_labels if 'categorias_labels' in locals() else []),
        'categorias_valores': json.dumps(categorias_valores if 'categorias_valores' in locals() else []),
        
        # Resumo de fretes
        'total_fretes_mes': total_fretes_mes,
        'fretes_em_andamento': fretes_em_andamento,
        'fretes_concluidos_mes': fretes_concluidos_mes,
        
        # Resumo de veículos
        'total_caminhoes_ativos': caminhoes_ativos,
        'total_carretas_ativas': carretas_ativas,
        'total_conjuntos_ativos': conjuntos_ativos,
        
        # Resumo de contatos
        'total_contatos': total_contatos,
        'total_clientes': total_clientes,
        'total_fornecedores': total_fornecedores,
        'total_motoristas': total_motoristas,
        'total_funcionarios': total_funcionarios,
        
        # Novas métricas
        'km_por_caminhao': km_por_caminhao,
        'media_kml_por_caminhao': media_kml_por_caminhao,
        'receitas_por_caminhao': receitas_por_caminhao,
        
        'dados_grafico_json': dados_grafico_json,
        'dados_categorias_json': dados_categorias_json,
        'meses_labels': json.dumps(meses_labels),
        'dados_receitas': json.dumps(dados_receitas),
        'dados_despesas': json.dumps(dados_despesas),
        'categorias_labels': json.dumps(categorias_labels),
        'categorias_valores': json.dumps(categorias_valores),
        'periodo': periodo,
        'periodos_disponiveis': [3, 6, 12],  # Períodos disponíveis para o dropdown
        'data_atual': hoje,  # Data atual do sistema
        'data_referencia': data_referencia,  # Data de referência com o mês e ano selecionados
        'mes_atual': mes_atual,  # Mês selecionado
        'ano_atual': ano_atual,  # Ano selecionado
        'nome_mes_atual': {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }[mes_atual],  # Nome do mês selecionado
        'anos_disponiveis': range(2020, hoje.year + 1),  # Lista de anos disponíveis
    }
    
    return render(request, 'core/dashboard/dashboard.html', context)