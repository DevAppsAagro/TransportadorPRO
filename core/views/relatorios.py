from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, F, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import datetime, timedelta
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
from core.models.empresa import Empresa
import json
from django.db.models import Q
from core.models.contato import Contato
from django.template.defaulttags import register

# Registrar filtro personalizado para divisão
@register.filter
def div(value, arg):
    try:
        return Decimal(value) / Decimal(arg)
    except (ValueError, ZeroDivisionError):
        return Decimal('0')

@login_required
def relatorios(request):
    return render(request, 'core/relatorios.html')

@login_required
def relatorio_veiculo(request):
    caminhoes = Caminhao.objects.filter(status='ATIVO', usuario=request.user).order_by('placa')
    
    if request.method == 'POST':
        caminhao_id = request.POST.get('caminhao')
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        
        if caminhao_id and data_inicio and data_fim:
            # Converte as datas para o formato correto
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            
            # Busca o caminhão e verifica se pertence ao usuário
            caminhao = get_object_or_404(Caminhao, id=caminhao_id, usuario=request.user)
            
            # Busca a empresa do usuário
            empresa = Empresa.objects.filter(usuario=request.user).first()
            
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
            
            # Calcula o peso total das cargas no período
            total_peso = fretes.aggregate(
                total=Coalesce(Sum('peso_carga'), Decimal('0'))
            )['total']
            
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
            
            # Adicionar os gastos com abastecimento aos custos variáveis
            total_abastecimentos = abastecimentos.aggregate(
                total=Coalesce(Sum('total_valor'), Decimal('0'))
            )['total']
            
            # Calcular o total de litros abastecidos
            total_litros = abastecimentos.aggregate(
                total=Coalesce(Sum('litros'), Decimal('0'))
            )['total']
            
            # Adicionar abastecimentos ao dicionário de despesas por categoria
            if total_abastecimentos > 0:
                if 'Combustível' not in despesas_por_categoria:
                    despesas_por_categoria['Combustível'] = {}
                if 'Diesel' not in despesas_por_categoria['Combustível']:
                    despesas_por_categoria['Combustível']['Diesel'] = Decimal('0')
                despesas_por_categoria['Combustível']['Diesel'] += total_abastecimentos
                
                # Atualizar o total de custos variáveis
                total_custos_variaveis += total_abastecimentos
            
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
            lucro_operacional = receita_total - total_custos_variaveis
            
            # Lucro líquido (considerando todos os custos)
            lucro_liquido = receita_total - total_custos
            
            # Preparar listas formatadas para o template
            custos_fixos = []
            total_custos_fixos_mensal = Decimal('0')
            
            # Adicionar itens de custo fixo
            if custos_fixos_estimados.get('depreciacao_caminhao', Decimal('0')) > 0:
                valor_periodo = custos_fixos_estimados['depreciacao_caminhao']
                valor_mensal = valor_periodo / (dias_periodo / Decimal('30')) if dias_periodo > 0 else Decimal('0')
                total_custos_fixos_mensal += valor_mensal
                custos_fixos.append({
                    'nome': 'Depreciação do Caminhão',
                    'is_category': False,
                    'valor_mensal': valor_mensal,
                    'valor_periodo': valor_periodo,
                    'percentual': (valor_periodo / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
            
            if custos_fixos_estimados.get('depreciacao_carreta', Decimal('0')) > 0:
                valor_periodo = custos_fixos_estimados['depreciacao_carreta']
                valor_mensal = valor_periodo / (dias_periodo / Decimal('30')) if dias_periodo > 0 else Decimal('0')
                total_custos_fixos_mensal += valor_mensal
                custos_fixos.append({
                    'nome': 'Depreciação da Carreta',
                    'is_category': False,
                    'valor_mensal': valor_mensal,
                    'valor_periodo': valor_periodo,
                    'percentual': (valor_periodo / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
            
            if custos_fixos_estimados.get('seguro', Decimal('0')) > 0:
                valor_periodo = custos_fixos_estimados['seguro']
                valor_mensal = valor_periodo / (dias_periodo / Decimal('30')) if dias_periodo > 0 else Decimal('0')
                total_custos_fixos_mensal += valor_mensal
                custos_fixos.append({
                    'nome': 'Seguro e Outros Custos Fixos',
                    'is_category': False,
                    'valor_mensal': valor_mensal,
                    'valor_periodo': valor_periodo,
                    'percentual': (valor_periodo / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
            
            if custos_fixos_estimados.get('manutencao', Decimal('0')) > 0:
                valor_periodo = custos_fixos_estimados['manutencao']
                valor_mensal = valor_periodo / (dias_periodo / Decimal('30')) if dias_periodo > 0 else Decimal('0')
                total_custos_fixos_mensal += valor_mensal
                custos_fixos.append({
                    'nome': 'Manutenção Planejada',
                    'is_category': False,
                    'valor_mensal': valor_mensal,
                    'valor_periodo': valor_periodo,
                    'percentual': (valor_periodo / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
            
            if custos_fixos_estimados.get('pneus', Decimal('0')) > 0:
                valor_periodo = custos_fixos_estimados['pneus']
                valor_mensal = valor_periodo / (dias_periodo / Decimal('30')) if dias_periodo > 0 else Decimal('0')
                total_custos_fixos_mensal += valor_mensal
                custos_fixos.append({
                    'nome': 'Pneus',
                    'is_category': False,
                    'valor_mensal': valor_mensal,
                    'valor_periodo': valor_periodo,
                    'percentual': (valor_periodo / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
            
            if custos_fixos_estimados.get('administrativo', Decimal('0')) > 0:
                valor_periodo = custos_fixos_estimados['administrativo']
                valor_mensal = valor_periodo / (dias_periodo / Decimal('30')) if dias_periodo > 0 else Decimal('0')
                total_custos_fixos_mensal += valor_mensal
                custos_fixos.append({
                    'nome': 'Custos Administrativos',
                    'is_category': False,
                    'valor_mensal': valor_mensal,
                    'valor_periodo': valor_periodo,
                    'percentual': (valor_periodo / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
            
            # Preparar custos variáveis para o template
            custos_variaveis = []
            
            # Adicionar categorias e subcategorias de custos variáveis
            for categoria_nome, subcategorias in despesas_por_categoria.items():
                # Adicionar categoria principal
                total_categoria = sum(subcategorias.values())
                custos_variaveis.append({
                    'nome': categoria_nome,
                    'is_category': True,
                    'valor_total': total_categoria,
                    'valor_km': total_categoria / Decimal(km_total) if km_total > 0 else Decimal('0'),
                    'percentual': (total_categoria / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
                
                # Adicionar subcategorias
                for subcategoria_nome, valor in subcategorias.items():
                    custos_variaveis.append({
                        'nome': subcategoria_nome,
                        'is_category': False,
                        'valor_total': valor,
                        'valor_km': valor / Decimal(km_total) if km_total > 0 else Decimal('0'),
                        'percentual': (valor / total_custos) * 100 if total_custos > 0 else Decimal('0')
                    })
            
            # Calcular percentuais para os totais
            percentual_custos_fixos = (total_custos_fixos_estimados / total_custos) * 100 if total_custos > 0 else Decimal('0')
            percentual_custos_variaveis = (total_custos_variaveis / total_custos) * 100 if total_custos > 0 else Decimal('0')
            
            # Prepara o contexto para o template
            context = {
                'caminhao': caminhao,
                'conjunto': conjunto,
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'dias_periodo': dias_periodo,
                'fretes': fretes,
                'km_total': km_total,
                'total_peso': total_peso,
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
                'empresa': empresa,
                'custos_fixos': custos_fixos,
                'custos_variaveis': custos_variaveis,
                'total_custos_fixos_mensal': total_custos_fixos_mensal,
                'percentual_custos_fixos': percentual_custos_fixos,
                'percentual_custos_variaveis': percentual_custos_variaveis,
                'total_abastecimentos': total_abastecimentos,
                'total_litros': total_litros,
                'abastecimentos': abastecimentos,
            }
            
            return render(request, 'core/relatorios/veiculo_resultado.html', context)
    
    return render(request, 'core/relatorios/veiculo_form.html', {'caminhoes': caminhoes})

@login_required
def relatorio_veiculo_print(request):
    """
    Versão de impressão do relatório de veículo.
    """
    if request.method == 'GET':
        caminhao_id = request.GET.get('caminhao_id') or request.GET.get('id')
        data_inicio = request.GET.get('data_inicio')
        data_fim = request.GET.get('data_fim')
        
        if caminhao_id and data_inicio and data_fim:
            # Converte as datas para o formato correto
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            
            # Busca o caminhão e verifica se pertence ao usuário
            caminhao = get_object_or_404(Caminhao, id=caminhao_id, usuario=request.user)
            
            # Busca a empresa do usuário
            empresa = Empresa.objects.filter(usuario=request.user).first()
            
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
            
            # Calcula o peso total das cargas no período
            total_peso = fretes.aggregate(
                total=Coalesce(Sum('peso_carga'), Decimal('0'))
            )['total']
            
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
            
            # Adicionar os gastos com abastecimento aos custos variáveis
            total_abastecimentos = abastecimentos.aggregate(
                total=Coalesce(Sum('total_valor'), Decimal('0'))
            )['total']
            
            # Calcular o total de litros abastecidos
            total_litros = abastecimentos.aggregate(
                total=Coalesce(Sum('litros'), Decimal('0'))
            )['total']
            
            # Adicionar abastecimentos ao dicionário de despesas por categoria
            if total_abastecimentos > 0:
                if 'Combustível' not in despesas_por_categoria:
                    despesas_por_categoria['Combustível'] = {}
                if 'Diesel' not in despesas_por_categoria['Combustível']:
                    despesas_por_categoria['Combustível']['Diesel'] = Decimal('0')
                despesas_por_categoria['Combustível']['Diesel'] += total_abastecimentos
                
                # Atualizar o total de custos variáveis
                total_custos_variaveis += total_abastecimentos
            
            # Calcula os totais e métricas finais
            total_custos = total_custos_fixos_estimados + total_custos_variaveis
            
            # Lucro bruto (receita - custos)
            lucro_bruto = receita_total - total_custos
            
            # Margem de lucro (lucro / receita)
            margem_lucro = Decimal('0')
            if receita_total > 0:
                margem_lucro = (lucro_bruto / receita_total) * 100
            
            # Custo por km
            custo_por_km = Decimal('0')
            if km_total > 0:
                custo_por_km = total_custos / Decimal(km_total)
            
            # Receita por km
            receita_por_km = Decimal('0')
            if km_total > 0:
                receita_por_km = receita_total / Decimal(km_total)
            
            # Lucro por km
            lucro_por_km = Decimal('0')
            if km_total > 0:
                lucro_por_km = lucro_bruto / Decimal(km_total)
            
            # Lucro operacional (sem considerar custos fixos)
            lucro_operacional = receita_total - total_custos_variaveis
            
            # Lucro líquido (considerando todos os custos)
            lucro_liquido = receita_total - total_custos
            
            # Preparar listas formatadas para o template
            custos_fixos = []
            total_custos_fixos_mensal = Decimal('0')
            
            # Adicionar itens de custo fixo
            if custos_fixos_estimados.get('depreciacao_caminhao', Decimal('0')) > 0:
                valor_periodo = custos_fixos_estimados['depreciacao_caminhao']
                valor_mensal = valor_periodo / (dias_periodo / Decimal('30')) if dias_periodo > 0 else Decimal('0')
                total_custos_fixos_mensal += valor_mensal
                custos_fixos.append({
                    'nome': 'Depreciação do Caminhão',
                    'is_category': False,
                    'valor_mensal': valor_mensal,
                    'valor_periodo': valor_periodo,
                    'percentual': (valor_periodo / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
            
            if custos_fixos_estimados.get('depreciacao_carreta', Decimal('0')) > 0:
                valor_periodo = custos_fixos_estimados['depreciacao_carreta']
                valor_mensal = valor_periodo / (dias_periodo / Decimal('30')) if dias_periodo > 0 else Decimal('0')
                total_custos_fixos_mensal += valor_mensal
                custos_fixos.append({
                    'nome': 'Depreciação da Carreta',
                    'is_category': False,
                    'valor_mensal': valor_mensal,
                    'valor_periodo': valor_periodo,
                    'percentual': (valor_periodo / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
            
            if custos_fixos_estimados.get('seguro', Decimal('0')) > 0:
                valor_periodo = custos_fixos_estimados['seguro']
                valor_mensal = valor_periodo / (dias_periodo / Decimal('30')) if dias_periodo > 0 else Decimal('0')
                total_custos_fixos_mensal += valor_mensal
                custos_fixos.append({
                    'nome': 'Seguro e Outros Custos Fixos',
                    'is_category': False,
                    'valor_mensal': valor_mensal,
                    'valor_periodo': valor_periodo,
                    'percentual': (valor_periodo / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
            
            if custos_fixos_estimados.get('manutencao', Decimal('0')) > 0:
                valor_periodo = custos_fixos_estimados['manutencao']
                valor_mensal = valor_periodo / (dias_periodo / Decimal('30')) if dias_periodo > 0 else Decimal('0')
                total_custos_fixos_mensal += valor_mensal
                custos_fixos.append({
                    'nome': 'Manutenção Planejada',
                    'is_category': False,
                    'valor_mensal': valor_mensal,
                    'valor_periodo': valor_periodo,
                    'percentual': (valor_periodo / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
            
            if custos_fixos_estimados.get('pneus', Decimal('0')) > 0:
                valor_periodo = custos_fixos_estimados['pneus']
                valor_mensal = valor_periodo / (dias_periodo / Decimal('30')) if dias_periodo > 0 else Decimal('0')
                total_custos_fixos_mensal += valor_mensal
                custos_fixos.append({
                    'nome': 'Pneus',
                    'is_category': False,
                    'valor_mensal': valor_mensal,
                    'valor_periodo': valor_periodo,
                    'percentual': (valor_periodo / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
            
            if custos_fixos_estimados.get('administrativo', Decimal('0')) > 0:
                valor_periodo = custos_fixos_estimados['administrativo']
                valor_mensal = valor_periodo / (dias_periodo / Decimal('30')) if dias_periodo > 0 else Decimal('0')
                total_custos_fixos_mensal += valor_mensal
                custos_fixos.append({
                    'nome': 'Custos Administrativos',
                    'is_category': False,
                    'valor_mensal': valor_mensal,
                    'valor_periodo': valor_periodo,
                    'percentual': (valor_periodo / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
            
            # Preparar custos variáveis para o template
            custos_variaveis = []
            
            # Adicionar categorias e subcategorias de custos variáveis
            for categoria_nome, subcategorias in despesas_por_categoria.items():
                # Adicionar categoria principal
                total_categoria = sum(subcategorias.values())
                custos_variaveis.append({
                    'nome': categoria_nome,
                    'is_category': True,
                    'valor_total': total_categoria,
                    'valor_km': total_categoria / Decimal(km_total) if km_total > 0 else Decimal('0'),
                    'percentual': (total_categoria / total_custos) * 100 if total_custos > 0 else Decimal('0')
                })
                
                # Adicionar subcategorias
                for subcategoria_nome, valor in subcategorias.items():
                    custos_variaveis.append({
                        'nome': subcategoria_nome,
                        'is_category': False,
                        'valor_total': valor,
                        'valor_km': valor / Decimal(km_total) if km_total > 0 else Decimal('0'),
                        'percentual': (valor / total_custos) * 100 if total_custos > 0 else Decimal('0')
                    })
            
            # Calcular percentuais para os totais
            percentual_custos_fixos = (total_custos_fixos_estimados / total_custos) * 100 if total_custos > 0 else Decimal('0')
            percentual_custos_variaveis = (total_custos_variaveis / total_custos) * 100 if total_custos > 0 else Decimal('0')
            
            # Prepara o contexto para o template
            context = {
                'caminhao': caminhao,
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'dias_periodo': dias_periodo,
                'fretes': fretes,
                'km_total': km_total,
                'total_peso': total_peso,
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
                'lucro_bruto': lucro_bruto,
                'margem_lucro': margem_lucro,
                'custo_por_km': custo_por_km,
                'receita_por_km': receita_por_km,
                'lucro_por_km': lucro_por_km,
                'relatorio_gerado': True,
                
                # Adicionando dados formatados para custos fixos
                'custos_fixos': [
                    {
                        'nome': 'Depreciação do Caminhão',
                        'is_category': True,
                        'valor_mensal': custos_fixos_estimados.get('depreciacao_caminhao', 0) / Decimal(dias_periodo) * 30,
                        'valor_periodo': custos_fixos_estimados.get('depreciacao_caminhao', 0),
                        'percentual': (custos_fixos_estimados.get('depreciacao_caminhao', 0) / total_custos * 100) if total_custos else 0
                    },
                    {
                        'nome': 'Depreciação da Carreta',
                        'is_category': True,
                        'valor_mensal': custos_fixos_estimados.get('depreciacao_carreta', 0) / Decimal(dias_periodo) * 30,
                        'valor_periodo': custos_fixos_estimados.get('depreciacao_carreta', 0),
                        'percentual': (custos_fixos_estimados.get('depreciacao_carreta', 0) / total_custos * 100) if total_custos else 0
                    },
                    {
                        'nome': 'Seguro e Outros Custos Fixos',
                        'is_category': True,
                        'valor_mensal': custos_fixos_estimados.get('seguro', 0) / Decimal(dias_periodo) * 30,
                        'valor_periodo': custos_fixos_estimados.get('seguro', 0),
                        'percentual': (custos_fixos_estimados.get('seguro', 0) / total_custos * 100) if total_custos else 0
                    },
                    {
                        'nome': 'Manutenção Planejada',
                        'is_category': True,
                        'valor_mensal': custos_fixos_estimados.get('manutencao', 0) / Decimal(dias_periodo) * 30,
                        'valor_periodo': custos_fixos_estimados.get('manutencao', 0),
                        'percentual': (custos_fixos_estimados.get('manutencao', 0) / total_custos * 100) if total_custos else 0
                    },
                    {
                        'nome': 'Pneus',
                        'is_category': True,
                        'valor_mensal': custos_fixos_estimados.get('pneus', 0) / Decimal(dias_periodo) * 30,
                        'valor_periodo': custos_fixos_estimados.get('pneus', 0),
                        'percentual': (custos_fixos_estimados.get('pneus', 0) / total_custos * 100) if total_custos else 0
                    },
                    {
                        'nome': 'Custos Administrativos',
                        'is_category': True,
                        'valor_mensal': custos_fixos_estimados.get('administrativo', 0) / Decimal(dias_periodo) * 30,
                        'valor_periodo': custos_fixos_estimados.get('administrativo', 0),
                        'percentual': (custos_fixos_estimados.get('administrativo', 0) / total_custos * 100) if total_custos else 0
                    }
                ],
                'total_custos_fixos_mensal': sum([custos_fixos_estimados.get(k, 0) for k in custos_fixos_estimados]) / Decimal(dias_periodo) * 30,
                'total_custos_fixos': total_custos_fixos_estimados,
                'percentual_custos_fixos': (total_custos_fixos_estimados / total_custos * 100) if total_custos else 0,
                
                # Adicionando dados formatados para custos variáveis
                'custos_variaveis': [
                    {
                        'nome': categoria,
                        'is_category': True,
                        'valor_total': sum(subcategorias.values()),
                        'valor_km': (sum(subcategorias.values()) / Decimal(km_total)) if km_total else 0,
                        'percentual': (sum(subcategorias.values()) / total_custos * 100) if total_custos else 0
                    }
                    for categoria, subcategorias in despesas_por_categoria.items()
                ] + [
                    {
                        'nome': f"{categoria} - {subcategoria}",
                        'is_category': False,
                        'valor_total': valor,
                        'valor_km': (valor / Decimal(km_total)) if km_total else 0,
                        'percentual': (valor / total_custos * 100) if total_custos else 0
                    }
                    for categoria, subcategorias in despesas_por_categoria.items()
                    for subcategoria, valor in subcategorias.items()
                ],
                'custo_variavel_km': custo_por_km - (total_custos_fixos_estimados / Decimal(km_total) if km_total else 0),
                'percentual_custos_variaveis': (total_custos_variaveis / total_custos * 100) if total_custos else 0,
                
                # Adicionando métricas financeiras no formato esperado
                'metricas': {
                    'receita_total': receita_total,
                    'custos_totais': total_custos,
                    'lucro_total': lucro_bruto,
                    'margem_lucro': margem_lucro,
                    'receita_por_km': receita_por_km,
                    'custo_por_km': custo_por_km,
                    'lucro_por_km': lucro_por_km,
                    'km_percorridos': km_total
                },
                'lucro_operacional': lucro_operacional,
                'lucro_liquido': lucro_liquido,
                'empresa': empresa,
                'total_abastecimentos': total_abastecimentos,
                'total_litros': total_litros,
                'abastecimentos': abastecimentos,
            }
            
            return render(request, 'core/relatorios/veiculo_resultado_print.html', context)
    
    return render(request, 'core/relatorios/veiculo_resultado_print.html', {'relatorio_gerado': False})

@login_required
def relatorio_frete(request, pk=None):
    if pk:
        # Buscar o frete específico, garantindo que pertença ao usuário logado
        frete = get_object_or_404(Frete, pk=pk, caminhao__usuario=request.user)
        return gerar_relatorio_frete(request, frete)
    
    # Processar o formulário quando enviado via POST
    if request.method == 'POST':
        frete_id = request.POST.get('frete')
        if frete_id:
            frete = get_object_or_404(Frete, pk=frete_id, caminhao__usuario=request.user)
            return gerar_relatorio_frete(request, frete)
    
    # Listar todos os fretes para seleção, filtrando pelo usuário logado
    fretes = Frete.objects.filter(caminhao__usuario=request.user).order_by('-data_saida')
    
    return render(request, 'core/relatorios/frete_form.html', {
        'fretes': fretes
    })

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
    lucro_operacional = receita_bruta - total_custos_variaveis
    
    # Lucro líquido (considerando todos os custos)
    lucro_liquido = receita_bruta - total_custos
    
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
    # Filtrar apenas clientes do usuário logado
    clientes = Contato.objects.filter(tipo='CLIENTE', usuario=request.user).order_by('nome_completo')
    
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
            
            # Busca o cliente e verifica se pertence ao usuário
            cliente = get_object_or_404(Contato, id=cliente_id, usuario=request.user)
            
            # Busca os fretes do cliente no período, filtrando pelo usuário logado
            fretes = Frete.objects.filter(
                cliente=cliente,
                data_saida__gte=data_inicio,
                data_saida__lte=data_fim,
                caminhao__usuario=request.user
            ).order_by('-data_saida')
            
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
def relatorio_cliente_print(request):
    """
    Versão de impressão do relatório de fretes por cliente.
    """
    # Obtém os parâmetros da URL
    cliente_id = request.GET.get('cliente_id') or request.GET.get('cliente')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    if not all([cliente_id, data_inicio, data_fim]):
        return redirect('core:relatorios')
    
    # Converte as datas para o formato correto
    try:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    except ValueError:
        return redirect('core:relatorios')
    
    # Busca o cliente e verifica se pertence ao usuário
    cliente = get_object_or_404(Contato, id=cliente_id, usuario=request.user)
    
    # Busca os fretes do cliente no período, filtrando pelo usuário logado
    fretes = Frete.objects.filter(
        cliente=cliente,
        data_saida__gte=data_inicio,
        data_saida__lte=data_fim,
        caminhao__usuario=request.user
    ).order_by('-data_saida')
    
    # Calcula totais
    total_fretes = fretes.count()
    valor_total = fretes.aggregate(total=Coalesce(Sum('valor_total'), Decimal('0')))['total']
    
    # Calcula fretes concluídos e em andamento
    fretes_concluidos = fretes.filter(data_chegada__isnull=False).count()
    fretes_andamento = fretes.filter(data_chegada__isnull=True).count()
    
    # Calcula peso total transportado
    peso_total = fretes.aggregate(total=Coalesce(Sum('peso_carga'), Decimal('0')))['total']
    
    # Calcula médias
    valor_medio = valor_total / total_fretes if total_fretes > 0 else Decimal('0')
    peso_medio = peso_total / total_fretes if total_fretes > 0 else Decimal('0')
    
    # Busca a empresa do usuário
    from core.models import Empresa
    empresa = Empresa.objects.filter(usuario=request.user).first()
    
    # Contexto para o template
    context = {
        'cliente': cliente,
        'fretes': fretes,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'fretes_count': total_fretes,
        'valor_total': valor_total,
        'fretes_concluidos': fretes_concluidos,
        'fretes_andamento': fretes_andamento,
        'peso_total': peso_total,
        'valor_medio': valor_medio,
        'peso_medio': peso_medio,
        'empresa': empresa,  # Adicionando a empresa ao contexto
    }
    
    return render(request, 'core/relatorios/relatorio_cliente_print.html', context)

@login_required
def fluxo_caixa(request):
    """
    Gera um relatório de fluxo de caixa mensal, mostrando receitas, despesas, 
    saldo mensal e saldo acumulado para cada mês do ano selecionado.
    """
    # Obter o ano selecionado (padrão: ano atual)
    ano_selecionado = request.GET.get('ano', datetime.now().year)
    try:
        ano_selecionado = int(ano_selecionado)
    except ValueError:
        ano_selecionado = datetime.now().year
    
    # Verificar se deve considerar custos fixos estimados
    considerar_estimados = request.GET.get('considerar_estimados') == 'on'
    
    # Lista de anos disponíveis (últimos 5 anos)
    ano_atual = datetime.now().year
    anos_disponiveis = list(range(ano_atual - 4, ano_atual + 1))
    
    # Dados do fluxo de caixa por mês
    fluxo_caixa_mensal = []
    saldo_acumulado = 0
    
    for mes in range(1, 13):
        # Receitas do mês (fretes)
        receitas = Frete.objects.filter(
            caminhao__usuario=request.user,
            data_saida__year=ano_selecionado,
            data_saida__month=mes
        ).aggregate(
            total=Coalesce(Sum('valor_total'), Decimal('0'))
        )['total']
        
        # Despesas do mês
        despesas = Despesa.objects.filter(
            Q(caminhao__usuario=request.user) | 
            Q(carreta__usuario=request.user) | 
            Q(frete__caminhao__usuario=request.user) | 
            Q(empresa__usuario=request.user),
            data_vencimento__year=ano_selecionado,
            data_vencimento__month=mes
        ).aggregate(
            total=Coalesce(Sum('valor'), Decimal('0'))
        )['total']
        
        # Adicionar custos fixos estimados se solicitado
        custos_fixos_estimados = Decimal('0')
        if considerar_estimados:
            # Buscar estimativas de custos fixos do usuário através dos conjuntos
            conjuntos_usuario = Conjunto.objects.filter(
                caminhao__usuario=request.user
            )
            
            # Buscar as estimativas mais recentes para cada conjunto
            estimativas_custo_fixo = EstimativaCustoFixo.objects.filter(
                conjunto__in=conjuntos_usuario
            )
            
            # Calcular o custo mensal total das estimativas
            for estimativa in estimativas_custo_fixo:
                # Custo diário * 30 dias = custo mensal aproximado
                custos_fixos_estimados += estimativa.custo_total_dia * Decimal('30')
            
            # Adicionar às despesas
            despesas += custos_fixos_estimados
        
        # Saldo do mês
        saldo_mes = receitas - despesas
        
        # Atualiza o saldo acumulado
        saldo_acumulado += saldo_mes
        
        # Adiciona os dados do mês ao fluxo de caixa
        fluxo_caixa_mensal.append({
            'mes': {
                1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
                5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
            }[mes],
            'receitas': receitas,
            'despesas': despesas - custos_fixos_estimados,  # Despesas sem os custos fixos
            'custos_fixos_estimados': custos_fixos_estimados,  # Custos fixos separados
            'saldo_mes': saldo_mes,
            'saldo_acumulado': saldo_acumulado
        })
    
    # Prepara o contexto para o template
    context = {
        'fluxo_caixa_mensal': fluxo_caixa_mensal,
        'anos_disponiveis': anos_disponiveis,
        'anos': anos_disponiveis,  # Para compatibilidade com o template
        'ano_selecionado': ano_selecionado,
        'considerar_estimados': considerar_estimados,
        
        # Totais para os cards
        'total_receitas': sum(item['receitas'] for item in fluxo_caixa_mensal),
        'total_despesas': sum(item['despesas'] for item in fluxo_caixa_mensal),
        'saldo_anual': sum(item['saldo_mes'] for item in fluxo_caixa_mensal),
        'saldo_acumulado_final': fluxo_caixa_mensal[-1]['saldo_acumulado'] if fluxo_caixa_mensal else Decimal('0'),
        
        # Dados para o gráfico
        'chart_labels': json.dumps([item['mes'] for item in fluxo_caixa_mensal]),
        'chart_receitas': json.dumps([float(item['receitas']) for item in fluxo_caixa_mensal]),
        'chart_despesas': json.dumps([float(item['despesas']) for item in fluxo_caixa_mensal]),
        'chart_saldo_mensal': json.dumps([float(item['saldo_mes']) for item in fluxo_caixa_mensal]),
        'chart_saldo_acumulado': json.dumps([float(item['saldo_acumulado']) for item in fluxo_caixa_mensal]),
    }
    
    return render(request, 'core/relatorios/fluxo_caixa.html', context)

@login_required
def dre(request):
    """
    Gera um Demonstrativo de Resultado do Exercício (DRE), mostrando receitas, despesas e resultados
    com opção de visualizar por regime de caixa (o que foi efetivamente pago/recebido) ou
    regime de competência (o que foi contabilizado no período, independente do pagamento).
    """
    # Obter parâmetros do formulário
    ano_selecionado = request.GET.get('ano')
    mes_selecionado = request.GET.get('mes')
    regime = request.GET.get('regime', 'competencia')  # Padrão: regime de competência
    
    # Valores padrão para data (mês atual)
    hoje = datetime.now().date()
    ano_atual = hoje.year
    mes_atual = hoje.month
    
    # Lista de anos disponíveis (últimos 5 anos)
    anos_disponiveis = list(range(ano_atual - 4, ano_atual + 1))
    
    # Lista de meses
    meses = [
        {'valor': 1, 'nome': 'Janeiro'},
        {'valor': 2, 'nome': 'Fevereiro'},
        {'valor': 3, 'nome': 'Março'},
        {'valor': 4, 'nome': 'Abril'},
        {'valor': 5, 'nome': 'Maio'},
        {'valor': 6, 'nome': 'Junho'},
        {'valor': 7, 'nome': 'Julho'},
        {'valor': 8, 'nome': 'Agosto'},
        {'valor': 9, 'nome': 'Setembro'},
        {'valor': 10, 'nome': 'Outubro'},
        {'valor': 11, 'nome': 'Novembro'},
        {'valor': 12, 'nome': 'Dezembro'}
    ]
    
    # Se o ano não foi especificado, usa o ano atual
    if not ano_selecionado:
        ano_selecionado = ano_atual
    else:
        try:
            ano_selecionado = int(ano_selecionado)
        except ValueError:
            ano_selecionado = ano_atual
    
    # Se o mês não foi especificado, usa o mês atual
    if not mes_selecionado:
        mes_selecionado = mes_atual
    else:
        try:
            mes_selecionado = int(mes_selecionado)
            if mes_selecionado < 1 or mes_selecionado > 12:
                mes_selecionado = mes_atual
        except ValueError:
            mes_selecionado = mes_atual
    
    # Calcula o primeiro e último dia do mês selecionado
    primeiro_dia_mes = datetime(ano_selecionado, mes_selecionado, 1).date()
    if mes_selecionado == 12:
        ultimo_dia_mes = datetime(ano_selecionado + 1, 1, 1).date() - timedelta(days=1)
    else:
        ultimo_dia_mes = datetime(ano_selecionado, mes_selecionado + 1, 1).date() - timedelta(days=1)
    
    # Define as datas de início e fim
    data_inicio_dt = primeiro_dia_mes
    data_fim_dt = ultimo_dia_mes
    data_inicio = primeiro_dia_mes.strftime('%Y-%m-%d')
    data_fim = ultimo_dia_mes.strftime('%Y-%m-%d')
    
    # Filtros de data para receitas e despesas
    if regime == 'caixa':
        # No regime de caixa, considera a data de recebimento/pagamento
        filtro_data_receitas = Q(data_recebimento__gte=data_inicio_dt, data_recebimento__lte=data_fim_dt)
        filtro_data_despesas = Q(data_pagamento__gte=data_inicio_dt, data_pagamento__lte=data_fim_dt)
    else:
        # No regime de competência, considera a data de saída do frete e a data de vencimento da despesa
        filtro_data_receitas = Q(data_saida__gte=data_inicio_dt, data_saida__lte=data_fim_dt)
        filtro_data_despesas = Q(data_vencimento__gte=data_inicio_dt, data_vencimento__lte=data_fim_dt)
    
    # === RECEITAS ===
    # Receitas de fretes
    receitas_fretes = Frete.objects.filter(filtro_data_receitas, caminhao__usuario=request.user)
    
    # Se o regime for de caixa, considera apenas os fretes pagos
    if regime == 'caixa':
        receitas_fretes = receitas_fretes.filter(data_recebimento__isnull=False)
    
    total_receitas = receitas_fretes.aggregate(total=Coalesce(Sum('valor_total'), Decimal('0')))['total']
    
    # === DESPESAS ===
    # Filtro adicional para despesas no regime de caixa
    if regime == 'caixa':
        filtro_data_despesas = filtro_data_despesas & Q(data_pagamento__isnull=False)
    
    # Filtrar despesas pelo usuário logado
    filtro_usuario = Q(caminhao__usuario=request.user) | Q(carreta__usuario=request.user) | Q(frete__caminhao__usuario=request.user) | Q(empresa__usuario=request.user)
    
    # Despesas por categoria
    despesas_por_categoria = Despesa.objects.filter(filtro_usuario, filtro_data_despesas).values(
        'categoria__nome'
    ).annotate(
        total=Sum('valor')
    ).order_by('categoria__nome')
    
    chart_labels = []
    chart_values = []
    
    for item in despesas_por_categoria:
        chart_labels.append(item['categoria__nome'])
        chart_values.append(float(item['total']))
    
    total_despesas = sum(item['total'] for item in despesas_por_categoria)
    
    # === RESULTADOS ===
    resultados = {
        'receita_liquida': total_receitas,
        'despesas_totais': total_despesas,
        'resultado_liquido': total_receitas - total_despesas,
        'margem': (total_receitas - total_despesas) / total_receitas * 100 if total_receitas > 0 else Decimal('0')
    }
    
    # Prepara o contexto para o template
    context = {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'regime': regime,
        'anos': anos_disponiveis,
        'meses': meses,
        'ano_selecionado': ano_selecionado,
        'mes_selecionado': mes_selecionado,
        'receitas': {'total': total_receitas},
        'despesas': {'total': total_despesas},
        'despesas_por_categoria': despesas_por_categoria,
        'resultados': resultados,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values)
    }
    
    return render(request, 'core/relatorios/dre.html', context)

@login_required
def relatorio_manutencao(request):
    """
    Gera um relatório de manutenções realizadas em um período específico,
    agrupadas por veículo e tipo de manutenção.
    """
    # Filtrar apenas veículos do usuário logado
    caminhoes = Caminhao.objects.filter(usuario=request.user, status='ATIVO').order_by('placa')
    carretas = Carreta.objects.filter(usuario=request.user, status='ATIVO').order_by('placa')
    
    if request.method == 'POST':
        veiculo_tipo = request.POST.get('veiculo_tipo')
        veiculo_id = request.POST.get('veiculo_id')
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        
        if veiculo_tipo and veiculo_id and data_inicio and data_fim:
            # Converte as datas para o formato correto
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            
            # Busca as manutenções do veículo no período
            if veiculo_tipo == 'caminhao':
                veiculo = get_object_or_404(Caminhao, id=veiculo_id, usuario=request.user)
                manutencoes = Manutencao.objects.filter(
                    caminhao=veiculo,
                    data__gte=data_inicio,
                    data__lte=data_fim
                ).order_by('-data')
                
                veiculo_nome = f"Caminhão {veiculo.marca} {veiculo.modelo} - Placa: {veiculo.placa}"
            else:
                veiculo = get_object_or_404(Carreta, id=veiculo_id, usuario=request.user)
                manutencoes = Manutencao.objects.filter(
                    carreta=veiculo,
                    data__gte=data_inicio,
                    data__lte=data_fim
                ).order_by('-data')
                
                veiculo_nome = f"Carreta {veiculo.marca} {veiculo.modelo} - Placa: {veiculo.placa}"
            
            # Agrupa as manutenções por tipo
            manutencoes_por_tipo = {}
            for manutencao in manutencoes:
                tipo_nome = manutencao.tipo.nome
                
                if tipo_nome not in manutencoes_por_tipo:
                    manutencoes_por_tipo[tipo_nome] = []
                
                manutencoes_por_tipo[tipo_nome].append(manutencao)
            
            # Prepara o contexto para o template
            context = {
                'veiculo_nome': veiculo_nome,
                'manutencoes_por_tipo': manutencoes_por_tipo,
                'data_inicio': data_inicio,
                'data_fim': data_fim,
            }
            
            return render(request, 'core/relatorios/manutencao_resultado.html', context)
    
    return render(request, 'core/relatorios/manutencao_form.html', {
        'caminhoes': caminhoes,
        'carretas': carretas
    })

@login_required
def relatorio_despesa(request):
    """
    Gera um relatório de despesas por categoria em um período específico.
    """
    # Obter parâmetros do formulário
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Valores padrão para data (mês atual)
    hoje = datetime.now().date()
    primeiro_dia_mes = hoje.replace(day=1)
    ultimo_dia_mes = (primeiro_dia_mes.replace(month=primeiro_dia_mes.month % 12 + 1, day=1) - timedelta(days=1)) if primeiro_dia_mes.month < 12 else primeiro_dia_mes.replace(year=primeiro_dia_mes.year + 1, month=1, day=1) - timedelta(days=1)
    
    # Se as datas não foram especificadas, usa o mês atual
    if not data_inicio:
        data_inicio = primeiro_dia_mes.strftime('%Y-%m-%d')
    if not data_fim:
        data_fim = ultimo_dia_mes.strftime('%Y-%m-%d')
    
    # Converte as datas para o formato correto
    try:
        data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d').date()
    except ValueError:
        data_inicio_dt = primeiro_dia_mes
        data_fim_dt = ultimo_dia_mes
        data_inicio = primeiro_dia_mes.strftime('%Y-%m-%d')
        data_fim = ultimo_dia_mes.strftime('%Y-%m-%d')
    
    # Filtro de usuário
    filtro_usuario = Q(caminhao__usuario=request.user) | Q(carreta__usuario=request.user) | Q(frete__caminhao__usuario=request.user) | Q(empresa__usuario=request.user)
    
    # Despesas por categoria
    despesas_por_categoria = Despesa.objects.filter(
        data_vencimento__gte=data_inicio_dt,
        data_vencimento__lte=data_fim_dt
    ).filter(
        filtro_usuario
    ).values(
        'categoria__nome'
    ).annotate(
        total=Sum('valor')
    ).order_by('-total')
    
    chart_labels = []
    chart_values = []
    
    for item in despesas_por_categoria:
        chart_labels.append(item['categoria__nome'])
        chart_values.append(float(item['total']))
    
    total_despesas = sum(item['total'] for item in despesas_por_categoria)
    
    # Prepara o contexto para o template
    context = {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'despesas_por_categoria': despesas_por_categoria,
        'total_despesas': total_despesas,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values)
    }
    
    return render(request, 'core/relatorios/despesas.html', context)
