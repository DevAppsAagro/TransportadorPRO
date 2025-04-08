from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from core.models.estimativa_custo_fixo import EstimativaCustoFixo, ItemCustoFixo
from core.models.conjunto import Conjunto
from decimal import Decimal
from django.utils import timezone
import datetime
import json

@login_required
def estimativa_custo_fixo_list(request):
    # Filtrar estimativas pelo usuário logado através do conjunto
    estimativas = EstimativaCustoFixo.objects.filter(conjunto__usuario=request.user).order_by('-data_estimativa')
    
    # Marcar as estimativas ativas
    for estimativa in estimativas:
        estimativa.ativa = estimativa.is_active
    
    return render(request, 'core/estimativa_custo_fixo/lista.html', {
        'estimativas': estimativas
    })

@login_required
def estimativa_custo_fixo_create(request):
    # Filtrar conjuntos pelo usuário logado
    conjuntos = Conjunto.objects.filter(usuario=request.user)
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        data_estimativa = request.POST.get('data_estimativa')
        conjunto_id = request.POST.get('conjunto')
        
        # Validar dados
        if not data_estimativa or not conjunto_id:
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
            return render(request, 'core/estimativa_custo_fixo/form.html', {
                'conjuntos': conjuntos,
                'tipos': ItemCustoFixo.TIPO_CHOICES,
                'today': today
            })
        
        try:
            conjunto = Conjunto.objects.get(id=conjunto_id)
            
            # Criar a estimativa
            estimativa = EstimativaCustoFixo(
                data_estimativa=data_estimativa,
                conjunto=conjunto
            )
            estimativa.save()  # Salvar primeiro para ter um ID
            
            # Processar itens
            itens_data = json.loads(request.POST.get('itens_data', '[]'))
            
            for item_data in itens_data:
                item = ItemCustoFixo(
                    estimativa=estimativa,
                    descricao=item_data.get('descricao', ''),
                    tipo=item_data.get('tipo', 'ANUAL'),
                    valor_total=Decimal(item_data.get('valor_total', '0'))
                )
                item.save()
            
            # Recalcular o custo total
            estimativa.calcular_custo_total_por_dia()
            
            messages.success(request, 'Estimativa de custo fixo criada com sucesso!')
            return redirect('core:estimativa_custo_fixo_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar estimativa: {str(e)}')
    
    return render(request, 'core/estimativa_custo_fixo/form.html', {
        'conjuntos': conjuntos,
        'tipos': ItemCustoFixo.TIPO_CHOICES,
        'today': today
    })

@login_required
def estimativa_custo_fixo_edit(request, id):
    # Buscar a estimativa garantindo que pertença ao usuário logado
    estimativa = get_object_or_404(EstimativaCustoFixo, pk=id, conjunto__usuario=request.user)
    # Filtrar conjuntos pelo usuário logado
    conjuntos = Conjunto.objects.filter(usuario=request.user)
    itens = estimativa.itens.all()
    
    if request.method == 'POST':
        data_estimativa = request.POST.get('data_estimativa')
        conjunto_id = request.POST.get('conjunto')
        
        # Validar dados
        if not data_estimativa or not conjunto_id:
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
            return render(request, 'core/estimativa_custo_fixo/form.html', {
                'estimativa': estimativa,
                'conjuntos': conjuntos,
                'itens': itens,
                'tipos': ItemCustoFixo.TIPO_CHOICES
            })
        
        try:
            conjunto = Conjunto.objects.get(id=conjunto_id)
            
            # Atualizar a estimativa
            estimativa.data_estimativa = data_estimativa
            estimativa.conjunto = conjunto
            estimativa.save()
            
            # Remover itens antigos
            estimativa.itens.all().delete()
            
            # Processar novos itens
            itens_data = json.loads(request.POST.get('itens_data', '[]'))
            
            for item_data in itens_data:
                item = ItemCustoFixo(
                    estimativa=estimativa,
                    descricao=item_data.get('descricao', ''),
                    tipo=item_data.get('tipo', 'ANUAL'),
                    valor_total=Decimal(item_data.get('valor_total', '0'))
                )
                item.save()
            
            # Recalcular o custo total
            estimativa.calcular_custo_total_por_dia()
            
            messages.success(request, 'Estimativa de custo fixo atualizada com sucesso!')
            return redirect('core:estimativa_custo_fixo_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar estimativa: {str(e)}')
    
    # Converter os valores decimais para string com vírgula para o padrão brasileiro
    estimativa_dict = {
        'id': estimativa.id,
        'conjunto_id': estimativa.conjunto_id,
        'data_estimativa': estimativa.data_estimativa,
        'custo_total_dia': str(estimativa.custo_total_dia).replace('.', ','),
    }
    
    # Converter os itens para dicionários com valores formatados com vírgula
    itens_formatados = []
    for item in itens:
        itens_formatados.append({
            'id': item.id,
            'descricao': item.descricao,
            'tipo': item.tipo,
            'valor_total': str(item.valor_total).replace('.', ','),
            'valor_por_dia': str(item.valor_por_dia).replace('.', ','),
        })
    
    return render(request, 'core/estimativa_custo_fixo/form.html', {
        'estimativa': estimativa_dict,
        'conjuntos': conjuntos,
        'itens': itens_formatados,
        'tipos': ItemCustoFixo.TIPO_CHOICES,
        'today': datetime.date.today().strftime('%Y-%m-%d')
    })

@login_required
def estimativa_custo_fixo_delete(request, id):
    # Buscar a estimativa garantindo que pertença ao usuário logado
    estimativa = get_object_or_404(EstimativaCustoFixo, pk=id, conjunto__usuario=request.user)
    
    try:
        estimativa.delete()
        messages.success(request, 'Estimativa de custo fixo excluída com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir estimativa: {str(e)}')
    
    return redirect('core:estimativa_custo_fixo_list')

@login_required
def detalhes_estimativa_custo_fixo(request, id):
    # Buscar a estimativa garantindo que pertença ao usuário logado
    estimativa = get_object_or_404(EstimativaCustoFixo, pk=id, conjunto__usuario=request.user)
    itens = estimativa.itens.all()
    
    # Marcar se está ativa
    estimativa.ativa = estimativa.is_active
    
    return render(request, 'core/estimativa_custo_fixo/detail.html', {
        'estimativa': estimativa,
        'itens': itens
    })

@login_required
def calcular_valor_por_dia(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            valor_mensal = Decimal(data.get('valor_mensal', 0))
            
            # Cálculo do valor por dia
            dias_mes = 30  # Média aproximada de dias por mês
            valor_por_dia = valor_mensal / dias_mes if valor_mensal > 0 else 0
            
            return JsonResponse({
                'valor_por_dia': float(valor_por_dia)
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)
