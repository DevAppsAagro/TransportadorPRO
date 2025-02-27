from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, F, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import datetime
from core.models.caminhao import Caminhao
from core.models.conjunto import Conjunto
from core.models.frete import Frete
from core.models.abastecimento import Abastecimento
from core.models.despesa import Despesa
from core.models.estimativa_pneus import EstimativaPneus
from core.models.estimativa_manutencao import EstimativaManutencao
from core.models.estimativa_custo_fixo import EstimativaCustoFixo
from core.models.categoria import Categoria
from core.models.subcategoria import Subcategoria
import json
from django.db.models import Q
from core.models.contato import Contato

@login_required
def relatorios(request):
    return render(request, 'core/relatorios.html')

@login_required
def relatorio_veiculo(request):
    caminhoes = Caminhao.objects.filter(status='ATIVO').order_by('placa')
    
    if request.method == 'POST':
        caminhao_id = request.POST.get('caminhao')
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        
        if caminhao_id and data_inicio and data_fim:
            # Converte as datas para o formato correto
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            
            # Busca o caminhão
            caminhao = get_object_or_404(Caminhao, id=caminhao_id)
            
            # Busca o conjunto ativo do caminhão
            conjunto = Conjunto.objects.filter(caminhao=caminhao, status='ATIVO').first()
            
            # Calcula o número de dias no período
            dias_periodo = (data_fim - data_inicio).days + 1
            
            # Busca os fretes do caminhão no período
            fretes = Frete.objects.filter(
                caminhao=caminhao,
                data_saida__gte=data_inicio,
                data_saida__lte=data_fim
            )
            
            # Calcula a quilometragem total no período
            km_total = sum(frete.km_total for frete in fretes)
            
            # Calcula a receita total (valor total dos fretes)
            receita_total = fretes.aggregate(
                total=Coalesce(Sum('valor_total'), Decimal('0'))
            )['total']
            
            # Calcula a comissão total do motorista
            comissao_total = fretes.aggregate(
                total=Coalesce(Sum('valor_comissao_motorista'), Decimal('0'))
            )['total']
            
            # Busca os abastecimentos do caminhão no período
            abastecimentos = Abastecimento.objects.filter(
                caminhao=caminhao,
                data__gte=data_inicio,
                data__lte=data_fim
            )
            
            # Calcula o total de diesel e o valor médio do litro
            total_diesel = abastecimentos.aggregate(
                total=Coalesce(Sum('litros'), Decimal('0'))
            )['total']
            
            valor_medio_diesel = Decimal('0')
            if total_diesel > 0:
                valor_medio_diesel = abastecimentos.aggregate(
                    total=Coalesce(Sum('total_valor'), Decimal('0'))
                )['total'] / total_diesel
            
            # Calcula a média de km/l
            media_km_l = Decimal('0')
            if total_diesel > 0:
                media_km_l = Decimal(km_total) / total_diesel
            
            # Busca as estimativas ativas
            estimativa_pneus = None
            estimativa_manutencao = None
            estimativa_custo_fixo = None
            
            if conjunto:
                # Estimativa de pneus
                estimativa_pneus = EstimativaPneus.objects.filter(
                    conjunto=conjunto
                ).order_by('-data_estimativa').first()
                
                # Estimativa de manutenção
                estimativa_manutencao = EstimativaManutencao.objects.filter(
                    conjunto=conjunto
                ).order_by('-data_estimativa').first()
                
                # Estimativa de custo fixo
                estimativa_custo_fixo = EstimativaCustoFixo.objects.filter(
                    conjunto=conjunto
                ).order_by('-data_estimativa').first()
            
            # Calcula os custos fixos estimados
            custos_fixos_estimados = {}
            
            # Depreciação do caminhão
            depreciacao_anual_caminhao = caminhao.calcular_depreciacao_anual()
            depreciacao_diaria_caminhao = Decimal(depreciacao_anual_caminhao) / Decimal('365')
            custos_fixos_estimados['depreciacao_caminhao'] = depreciacao_diaria_caminhao * Decimal(dias_periodo)
            
            # Depreciação da carreta
            depreciacao_anual_carreta = Decimal('0')
            if conjunto and conjunto.carreta1:
                carreta = conjunto.carreta1
                if carreta.vida_util > 0:
                    valor_depreciavel = carreta.valor_compra - carreta.valor_residual
                    depreciacao_anual_carreta = Decimal(valor_depreciavel / carreta.vida_util)
            
            depreciacao_diaria_carreta = Decimal(depreciacao_anual_carreta) / Decimal('365')
            custos_fixos_estimados['depreciacao_carreta'] = depreciacao_diaria_carreta * Decimal(dias_periodo)
            
            # Seguro e outros custos fixos
            custo_fixo_diario = Decimal('0')
            if estimativa_custo_fixo:
                custo_fixo_diario = estimativa_custo_fixo.custo_total_dia
            
            custos_fixos_estimados['seguro'] = custo_fixo_diario * Decimal(dias_periodo)
            
            # Manutenção e reparos planejados
            custo_manutencao_km = Decimal('0')
            if estimativa_manutencao:
                custo_manutencao_km = estimativa_manutencao.custo_total_km
            
            custos_fixos_estimados['manutencao'] = custo_manutencao_km * Decimal(km_total)
            
            # Pneus planejados
            custo_pneus_km = Decimal('0')
            if estimativa_pneus:
                custo_pneus_km = estimativa_pneus.custo_total_km
            
            custos_fixos_estimados['pneus'] = custo_pneus_km * Decimal(km_total)
            
            # Busca as despesas administrativas no período
            despesas_administrativas = Despesa.objects.filter(
                data__gte=data_inicio,
                data__lte=data_fim,
                categoria__alocacao='ADMINISTRATIVO'
            )
            
            total_despesas_admin = despesas_administrativas.aggregate(
                total=Coalesce(Sum('valor'), Decimal('0'))
            )['total']
            
            # Contagem de caminhões ativos para rateio
            total_caminhoes_ativos = Caminhao.objects.filter(status='ATIVO').count()
            if total_caminhoes_ativos > 0:
                custos_fixos_estimados['administrativo'] = total_despesas_admin / Decimal(total_caminhoes_ativos)
            else:
                custos_fixos_estimados['administrativo'] = Decimal('0')
            
            # Total de custos fixos estimados
            total_custos_fixos_estimados = Decimal(sum(custos_fixos_estimados.values()))
            
            # Busca as despesas variáveis realizadas no período
            despesas_variaveis = Despesa.objects.filter(
                data__gte=data_inicio,
                data__lte=data_fim,
                categoria__tipo='CUSTO_VARIAVEL',
                caminhao=caminhao
            )
            
            # Agrupa as despesas variáveis por categoria e subcategoria
            despesas_por_categoria = {}
            for despesa in despesas_variaveis:
                categoria_nome = despesa.categoria.nome
                subcategoria_nome = despesa.subcategoria.nome
                
                if categoria_nome not in despesas_por_categoria:
                    despesas_por_categoria[categoria_nome] = {}
                
                if subcategoria_nome not in despesas_por_categoria[categoria_nome]:
                    despesas_por_categoria[categoria_nome][subcategoria_nome] = Decimal('0')
                
                despesas_por_categoria[categoria_nome][subcategoria_nome] += despesa.valor
            
            # Total de custos variáveis realizados
            total_custos_variaveis = despesas_variaveis.aggregate(
                total=Coalesce(Sum('valor'), Decimal('0'))
            )['total']
            
            # Calcula os totais e métricas finais
            total_custos = total_custos_fixos_estimados + total_custos_variaveis
            
            # Métricas por km
            custo_fixo_km = Decimal('0')
            custo_variavel_km = Decimal('0')
            custo_total_km = Decimal('0')
            
            if km_total > 0:
                custo_fixo_km = total_custos_fixos_estimados / Decimal(km_total)
                custo_variavel_km = total_custos_variaveis / Decimal(km_total)
                custo_total_km = total_custos / Decimal(km_total)
            
            # Lucro operacional (sem considerar custos fixos)
            lucro_operacional = receita_total - total_custos_variaveis - comissao_total
            
            # Lucro líquido (considerando todos os custos)
            lucro_liquido = receita_total - total_custos - comissao_total
            
            # Prepara o contexto para o template
            context = {
                'caminhao': caminhao,
                'conjunto': conjunto,
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'dias_periodo': dias_periodo,
                'fretes': fretes,
                'km_total': km_total,
                'receita_total': receita_total,
                'comissao_total': comissao_total,
                'total_diesel': total_diesel,
                'valor_medio_diesel': valor_medio_diesel,
                'media_km_l': media_km_l,
                'custos_fixos_estimados': custos_fixos_estimados,
                'total_custos_fixos_estimados': total_custos_fixos_estimados,
                'despesas_por_categoria': despesas_por_categoria,
                'total_custos_variaveis': total_custos_variaveis,
                'total_custos': total_custos,
                'custo_fixo_km': custo_fixo_km,
                'custo_variavel_km': custo_variavel_km,
                'custo_total_km': custo_total_km,
                'lucro_operacional': lucro_operacional,
                'lucro_liquido': lucro_liquido,
            }
            
            return render(request, 'core/relatorios/veiculo_resultado.html', context)
    
    return render(request, 'core/relatorios/veiculo_form.html', {'caminhoes': caminhoes})

@login_required
def relatorio_frete(request, pk=None):
    """
    Gera um relatório detalhado para um frete específico, incluindo receitas, despesas e lucratividade.
    """
    # Se um ID de frete foi passado diretamente na URL
    if pk:
        frete = get_object_or_404(Frete, pk=pk)
        return gerar_relatorio_frete(request, frete)
    
    # Se estamos selecionando um frete através do formulário
    fretes = Frete.objects.all().order_by('-data_saida')
    
    if request.method == 'POST':
        frete_id = request.POST.get('frete')
        
        if frete_id:
            frete = get_object_or_404(Frete, pk=frete_id)
            return gerar_relatorio_frete(request, frete)
    
    return render(request, 'core/relatorios/frete_form.html', {'fretes': fretes})

def gerar_relatorio_frete(request, frete):
    """
    Função auxiliar que gera o relatório para um frete específico.
    """
    # Informações básicas do frete
    caminhao = frete.caminhao
    motorista = frete.motorista
    cliente = frete.cliente
    
    # Cálculos de quilometragem
    km_total = frete.km_total
    
    # Valores financeiros
    receita_bruta = frete.valor_total
    comissao_motorista = frete.valor_comissao_motorista
    receita_liquida = receita_bruta - comissao_motorista
    
    # Busca as despesas relacionadas a este frete
    despesas = Despesa.objects.filter(frete=frete)
    
    # Agrupa as despesas por categoria
    despesas_por_categoria = {}
    for despesa in despesas:
        categoria_nome = despesa.categoria.nome
        subcategoria_nome = despesa.subcategoria.nome
        
        if categoria_nome not in despesas_por_categoria:
            despesas_por_categoria[categoria_nome] = {}
        
        if subcategoria_nome not in despesas_por_categoria[categoria_nome]:
            despesas_por_categoria[categoria_nome][subcategoria_nome] = Decimal('0')
        
        despesas_por_categoria[categoria_nome][subcategoria_nome] += despesa.valor
    
    # Total de despesas
    total_despesas = despesas.aggregate(
        total=Coalesce(Sum('valor'), Decimal('0'))
    )['total']
    
    # Busca os abastecimentos relacionados a este frete (pela data e caminhão)
    abastecimentos = Abastecimento.objects.filter(
        caminhao=caminhao,
        data__gte=frete.data_saida,
        data__lte=frete.data_chegada if frete.data_chegada else frete.data_saida
    )
    
    # Cálculos de combustível
    total_diesel = abastecimentos.aggregate(
        total=Coalesce(Sum('litros'), Decimal('0'))
    )['total']
    
    total_valor_diesel = abastecimentos.aggregate(
        total=Coalesce(Sum('total_valor'), Decimal('0'))
    )['total']
    
    valor_medio_diesel = Decimal('0')
    if total_diesel > 0:
        valor_medio_diesel = total_valor_diesel / total_diesel
    
    media_km_l = Decimal('0')
    if total_diesel > 0:
        media_km_l = Decimal(km_total) / total_diesel
    
    # Custo do diesel por km
    custo_diesel_km = Decimal('0')
    if km_total > 0:
        custo_diesel_km = total_valor_diesel / Decimal(km_total)
    
    # Estimativas de custos fixos
    conjunto = None
    if caminhao:
        conjunto = Conjunto.objects.filter(caminhao=caminhao, status='ATIVO').first()
    
    # Dias de duração do frete
    dias_frete = 1  # Mínimo de 1 dia
    if frete.data_chegada:
        dias_frete = (frete.data_chegada - frete.data_saida).days + 1
    
    # Custos fixos estimados
    custos_fixos_estimados = {}
    
    # Depreciação do caminhão
    depreciacao_anual_caminhao = caminhao.calcular_depreciacao_anual()
    depreciacao_diaria_caminhao = Decimal(depreciacao_anual_caminhao) / Decimal('365')
    custos_fixos_estimados['depreciacao_caminhao'] = depreciacao_diaria_caminhao * Decimal(dias_frete)
    
    # Depreciação da carreta
    depreciacao_anual_carreta = Decimal('0')
    if conjunto and conjunto.carreta1:
        carreta = conjunto.carreta1
        if carreta.vida_util > 0:
            valor_depreciavel = carreta.valor_compra - carreta.valor_residual
            depreciacao_anual_carreta = Decimal(valor_depreciavel / carreta.vida_util)
    
    depreciacao_diaria_carreta = Decimal(depreciacao_anual_carreta) / Decimal('365')
    custos_fixos_estimados['depreciacao_carreta'] = depreciacao_diaria_carreta * Decimal(dias_frete)
    
    # Seguro e outros custos fixos
    custo_fixo_diario = Decimal('0')
    if conjunto:
        estimativa_custo_fixo = EstimativaCustoFixo.objects.filter(
            conjunto=conjunto
        ).order_by('-data_estimativa').first()
        
        if estimativa_custo_fixo:
            custo_fixo_diario = estimativa_custo_fixo.custo_total_dia
    
    custos_fixos_estimados['seguro'] = custo_fixo_diario * Decimal(dias_frete)
    
    # Manutenção e reparos planejados
    custo_manutencao_km = Decimal('0')
    if conjunto:
        estimativa_manutencao = EstimativaManutencao.objects.filter(
            conjunto=conjunto
        ).order_by('-data_estimativa').first()
        
        if estimativa_manutencao:
            custo_manutencao_km = estimativa_manutencao.custo_total_km
    
    custos_fixos_estimados['manutencao'] = custo_manutencao_km * Decimal(km_total)
    
    # Pneus planejados
    custo_pneus_km = Decimal('0')
    if conjunto:
        estimativa_pneus = EstimativaPneus.objects.filter(
            conjunto=conjunto
        ).order_by('-data_estimativa').first()
        
        if estimativa_pneus:
            custo_pneus_km = estimativa_pneus.custo_total_km
    
    custos_fixos_estimados['pneus'] = custo_pneus_km * Decimal(km_total)
    
    # Total de custos fixos estimados
    total_custos_fixos_estimados = Decimal(sum(custos_fixos_estimados.values()))
    
    # Custos variáveis (despesas + diesel)
    total_custos_variaveis = total_despesas + total_valor_diesel
    
    # Custo total (fixos + variáveis)
    total_custos = total_custos_fixos_estimados + total_custos_variaveis
    
    # Métricas por km
    custo_fixo_km = Decimal('0')
    custo_variavel_km = Decimal('0')
    custo_total_km = Decimal('0')
    
    if km_total > 0:
        custo_fixo_km = total_custos_fixos_estimados / Decimal(km_total)
        custo_variavel_km = total_custos_variaveis / Decimal(km_total)
        custo_total_km = total_custos / Decimal(km_total)
    
    # Lucro operacional (sem considerar custos fixos)
    lucro_operacional = receita_bruta - total_custos_variaveis - comissao_motorista
    
    # Lucro líquido (considerando todos os custos)
    lucro_liquido = receita_bruta - total_custos - comissao_motorista
    
    # Margem de lucro
    margem_lucro = Decimal('0')
    if receita_bruta > 0:
        margem_lucro = (lucro_liquido / receita_bruta) * 100
    
    # Prepara o contexto para o template
    context = {
        'frete': frete,
        'caminhao': caminhao,
        'motorista': motorista,
        'cliente': cliente,
        'km_total': km_total,
        'dias_frete': dias_frete,
        'receita_bruta': receita_bruta,
        'comissao_motorista': comissao_motorista,
        'receita_liquida': receita_liquida,
        'despesas': despesas,
        'despesas_por_categoria': despesas_por_categoria,
        'total_despesas': total_despesas,
        'abastecimentos': abastecimentos,
        'total_diesel': total_diesel,
        'total_valor_diesel': total_valor_diesel,
        'valor_medio_diesel': valor_medio_diesel,
        'media_km_l': media_km_l,
        'custo_diesel_km': custo_diesel_km,
        'custos_fixos_estimados': custos_fixos_estimados,
        'total_custos_fixos_estimados': total_custos_fixos_estimados,
        'total_custos_variaveis': total_custos_variaveis,
        'total_custos': total_custos,
        'custo_fixo_km': custo_fixo_km,
        'custo_variavel_km': custo_variavel_km,
        'custo_total_km': custo_total_km,
        'lucro_operacional': lucro_operacional,
        'lucro_liquido': lucro_liquido,
        'margem_lucro': margem_lucro,
    }
    
    return render(request, 'core/relatorios/frete_resultado.html', context)

@login_required
def relatorio_cliente(request):
    """
    Gera um relatório de fretes por cliente, mostrando todos os fretes realizados
    para um cliente específico em um determinado período.
    """
    # Buscar todos os clientes
    clientes = Contato.objects.filter(tipo='CLIENTE').order_by('nome_completo')
    
    context = {
        'clientes': clientes,
        'relatorio_gerado': False
    }
    
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente')
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        
        if cliente_id and data_inicio and data_fim:
            # Converte as datas para o formato correto
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            
            # Busca o cliente
            cliente = get_object_or_404(Contato, id=cliente_id, tipo='CLIENTE')
            
            # Busca os fretes do cliente no período
            fretes = Frete.objects.filter(
                cliente=cliente,
                data_saida__gte=data_inicio,
                data_saida__lte=data_fim
            ).order_by('data_saida')
            
            # Calcula totais
            total_fretes = fretes.count()
            total_valor = fretes.aggregate(total=Coalesce(Sum('valor_total'), Decimal('0')))['total']
            
            # Calcula fretes concluídos e em andamento
            fretes_concluidos = fretes.filter(data_chegada__isnull=False).count()
            fretes_em_andamento = fretes.filter(data_chegada__isnull=True).count()
            
            # Calcula peso total transportado
            peso_total = fretes.aggregate(total=Coalesce(Sum('peso_carga'), Decimal('0')))['total']
            
            # Calcula totais por tipo de carga
            cargas_resumo = []
            tipos_carga = {}
            
            # Primeiro, agrupa os fretes por tipo de carga
            for frete in fretes:
                carga_id = frete.carga.id
                if carga_id not in tipos_carga:
                    tipos_carga[carga_id] = {
                        'carga': frete.carga,
                        'peso_total': Decimal('0'),
                        'quantidade_convertida': Decimal('0'),
                        'fretes': 0
                    }
                
                tipos_carga[carga_id]['peso_total'] += frete.peso_carga
                tipos_carga[carga_id]['quantidade_convertida'] = tipos_carga[carga_id]['peso_total'] / frete.carga.fator_multiplicacao
                tipos_carga[carga_id]['fretes'] += 1
            
            # Converte o dicionário para lista para uso no template
            cargas_resumo = list(tipos_carga.values())
            
            # Adiciona informação de carga convertida a cada frete
            for frete in fretes:
                frete.quantidade_convertida = frete.peso_carga / frete.carga.fator_multiplicacao
                frete.unidade_medida = frete.carga.unidade_medida
            
            # Adiciona informações ao contexto
            context.update({
                'relatorio_gerado': True,
                'cliente': cliente,
                'fretes': fretes,
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'total_fretes': total_fretes,
                'total_valor': total_valor,
                'fretes_concluidos': fretes_concluidos,
                'fretes_em_andamento': fretes_em_andamento,
                'peso_total': peso_total,
                'cargas_resumo': cargas_resumo
            })
    
    return render(request, 'core/relatorios/relatorio_cliente.html', context)

@login_required
def fluxo_caixa(request):
    """
    Gera um relatório de fluxo de caixa mensal, mostrando receitas, despesas, 
    saldo mensal e saldo acumulado para cada mês do ano selecionado.
    """
    # Obtém o ano atual
    ano_atual = datetime.now().year
    
    # Lista de anos para o filtro (últimos 5 anos + ano atual)
    anos = list(range(ano_atual - 5, ano_atual + 1))
    
    # Obtém o ano selecionado do formulário ou usa o ano atual como padrão
    ano_selecionado = int(request.GET.get('ano', ano_atual))
    
    # Verifica se deve considerar custos fixos estimados
    considerar_estimados = request.GET.get('considerar_estimados', 'off') == 'on'
    
    # Inicializa os dados do fluxo de caixa
    fluxo_caixa = []
    saldo_acumulado = Decimal('0')
    
    # Se estamos no primeiro mês do ano, precisamos buscar o saldo acumulado dos anos anteriores
    if ano_selecionado > 0:
        # Receitas de anos anteriores
        receitas_anteriores = Frete.objects.filter(
            data_saida__year__lt=ano_selecionado
        ).aggregate(
            total=Coalesce(Sum('valor_total'), Decimal('0'))
        )['total']
        
        # Despesas de anos anteriores (despesas pagas)
        despesas_anteriores = Despesa.objects.filter(
            data_vencimento__year__lt=ano_selecionado,
            data_pagamento__isnull=False
        ).aggregate(
            total=Coalesce(Sum('valor'), Decimal('0'))
        )['total']
        
        # Calcula o saldo acumulado dos anos anteriores
        saldo_acumulado = receitas_anteriores - despesas_anteriores
    
    # Dados para o gráfico
    chart_labels = []
    chart_receitas = []
    chart_despesas = []
    chart_saldo_mensal = []
    chart_saldo_acumulado = []
    
    # Para cada mês do ano
    for mes in range(1, 13):
        # Nome do mês
        nome_mes = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }[mes]
        
        # Receitas do mês (fretes com data de saída no mês)
        receitas_mes = Frete.objects.filter(
            data_saida__year=ano_selecionado,
            data_saida__month=mes
        ).aggregate(
            total=Coalesce(Sum('valor_total'), Decimal('0'))
        )['total']
        
        # Despesas pagas no mês
        despesas_pagas = Despesa.objects.filter(
            data_vencimento__year=ano_selecionado,
            data_vencimento__month=mes,
            data_pagamento__isnull=False
        ).aggregate(
            total=Coalesce(Sum('valor'), Decimal('0'))
        )['total']
        
        # Despesas a pagar no mês (para competência de caixa)
        hoje = datetime.now().date()
        despesas_a_pagar = Despesa.objects.filter(
            data_vencimento__year=ano_selecionado,
            data_vencimento__month=mes,
            data_pagamento__isnull=True
        ).aggregate(
            total=Coalesce(Sum('valor'), Decimal('0'))
        )['total']
        
        # Total de despesas do mês (pagas + a pagar)
        despesas_mes = despesas_pagas + despesas_a_pagar
        
        # Custos fixos estimados (se solicitado)
        custos_fixos_estimados = Decimal('0')
        if considerar_estimados:
            # Busca todos os conjuntos ativos
            conjuntos_ativos = Conjunto.objects.filter(status='ATIVO')
            
            # Para cada conjunto, busca a estimativa de custo fixo mais recente
            for conjunto in conjuntos_ativos:
                estimativa = EstimativaCustoFixo.objects.filter(
                    conjunto=conjunto
                ).order_by('-data_estimativa').first()
                
                if estimativa:
                    # Adiciona o custo fixo mensal estimado
                    custos_fixos_estimados += estimativa.custo_total_dia * Decimal('30')  # Aproximação para um mês
        
        # Adiciona os custos fixos estimados às despesas do mês (se solicitado)
        if considerar_estimados:
            despesas_mes += custos_fixos_estimados
        
        # Calcula o saldo do mês
        saldo_mes = receitas_mes - despesas_mes
        
        # Atualiza o saldo acumulado
        saldo_acumulado += saldo_mes
        
        # Adiciona os dados do mês ao fluxo de caixa
        fluxo_caixa.append({
            'mes': nome_mes,
            'receitas': receitas_mes,
            'despesas': despesas_mes,
            'custos_fixos_estimados': custos_fixos_estimados if considerar_estimados else None,
            'saldo_mes': saldo_mes,
            'saldo_acumulado': saldo_acumulado
        })
        
        # Adiciona os dados para o gráfico
        chart_labels.append(nome_mes)
        chart_receitas.append(float(receitas_mes))
        chart_despesas.append(float(despesas_mes))
        chart_saldo_mensal.append(float(saldo_mes))
        chart_saldo_acumulado.append(float(saldo_acumulado))
    
    # Prepara o contexto para o template
    context = {
        'fluxo_caixa': fluxo_caixa,
        'anos': anos,
        'ano_selecionado': ano_selecionado,
        'considerar_estimados': considerar_estimados,
        'chart_labels': chart_labels,
        'chart_receitas': chart_receitas,
        'chart_despesas': chart_despesas,
        'chart_saldo_mensal': chart_saldo_mensal,
        'chart_saldo_acumulado': chart_saldo_acumulado,
    }
    
    return render(request, 'core/relatorios/fluxo_caixa.html', context)


@login_required
def dre(request):
    """
    Gera um Demonstrativo de Resultado do Exercício (DRE), mostrando receitas, despesas e resultados
    com opção de visualizar por regime de caixa (o que foi efetivamente pago/recebido) ou
    regime de competência (o que foi contabilizado no período, independente do pagamento).
    """
    # Obtém o ano atual
    ano_atual = datetime.now().year
    
    # Lista de anos para o filtro (últimos 5 anos + ano atual)
    anos = list(range(ano_atual - 5, ano_atual + 1))
    
    # Obtém o ano selecionado do formulário ou usa o ano atual como padrão
    ano_selecionado = int(request.GET.get('ano', ano_atual))
    
    # Obtém o mês selecionado do formulário ou usa todos os meses como padrão
    mes_selecionado = request.GET.get('mes', 'todos')
    
    # Obtém o regime selecionado (caixa ou competência)
    regime = request.GET.get('regime', 'competencia')
    
    # Lista de meses para o filtro
    meses = [
        {'valor': 'todos', 'nome': 'Todos os meses'},
        {'valor': '1', 'nome': 'Janeiro'},
        {'valor': '2', 'nome': 'Fevereiro'},
        {'valor': '3', 'nome': 'Março'},
        {'valor': '4', 'nome': 'Abril'},
        {'valor': '5', 'nome': 'Maio'},
        {'valor': '6', 'nome': 'Junho'},
        {'valor': '7', 'nome': 'Julho'},
        {'valor': '8', 'nome': 'Agosto'},
        {'valor': '9', 'nome': 'Setembro'},
        {'valor': '10', 'nome': 'Outubro'},
        {'valor': '11', 'nome': 'Novembro'},
        {'valor': '12', 'nome': 'Dezembro'}
    ]
    
    # Inicializa os filtros de data
    filtro_data_receitas = Q(data_saida__year=ano_selecionado)
    filtro_data_despesas = Q(data_vencimento__year=ano_selecionado)
    
    # Se um mês específico foi selecionado, adiciona ao filtro
    if mes_selecionado != 'todos':
        filtro_data_receitas &= Q(data_saida__month=int(mes_selecionado))
        filtro_data_despesas &= Q(data_vencimento__month=int(mes_selecionado))
    
    # Inicializa as variáveis para armazenar os resultados
    receitas = {}
    despesas = {}
    resultados = {}
    
    # === RECEITAS ===
    # Receitas de fretes
    receitas_fretes = Frete.objects.filter(filtro_data_receitas)
    
    # Se o regime for de caixa, considera apenas os fretes pagos
    if regime == 'caixa':
        receitas_fretes = receitas_fretes.filter(status_pagamento='PAGO')
    
    total_receitas_fretes = receitas_fretes.aggregate(
        total=Coalesce(Sum('valor_total'), Decimal('0'))
    )['total']
    
    receitas['fretes'] = total_receitas_fretes
    receitas['total'] = total_receitas_fretes
    
    # === DESPESAS ===
    # Despesas por categoria
    categorias_despesa = Categoria.objects.all()
    
    total_despesas = Decimal('0')
    
    for categoria in categorias_despesa:
        nome_categoria = categoria.nome
        
        # Filtra despesas por categoria
        query_despesas = Despesa.objects.filter(filtro_data_despesas, categoria=categoria)
        
        # Se o regime for de caixa, considera apenas as despesas pagas
        if regime == 'caixa':
            query_despesas = query_despesas.filter(data_pagamento__isnull=False)
        
        valor_categoria = query_despesas.aggregate(
            total=Coalesce(Sum('valor'), Decimal('0'))
        )['total']
        
        # Só adiciona a categoria se tiver despesas no período
        if valor_categoria > 0:
            despesas[nome_categoria] = valor_categoria
            total_despesas += valor_categoria
    
    despesas['total'] = total_despesas
    
    # === RESULTADOS ===
    resultados['receita_liquida'] = receitas['total']
    resultados['despesas_totais'] = despesas['total']
    resultados['resultado_liquido'] = resultados['receita_liquida'] - resultados['despesas_totais']
    resultados['margem'] = (resultados['resultado_liquido'] / resultados['receita_liquida'] * 100) if resultados['receita_liquida'] > 0 else Decimal('0')
    
    # Prepara os dados para o gráfico
    despesas_ordenadas = {k: v for k, v in despesas.items() if k != 'total'}
    despesas_ordenadas = dict(sorted(despesas_ordenadas.items(), key=lambda item: item[1], reverse=True))
    
    chart_labels = list(despesas_ordenadas.keys())
    chart_values = [float(despesas_ordenadas[categoria]) for categoria in chart_labels]
    
    # Prepara o contexto para o template
    context = {
        'anos': anos,
        'ano_selecionado': ano_selecionado,
        'meses': meses,
        'mes_selecionado': mes_selecionado,
        'regime': regime,
        'receitas': receitas,
        'despesas': despesas,
        'resultados': resultados,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values)
    }
    
    return render(request, 'core/relatorios/dre.html', context)
