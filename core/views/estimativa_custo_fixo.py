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
    estimativas = EstimativaCustoFixo.objects.all().order_by('-data_estimativa')
    
    # Marcar as estimativas ativas
    for estimativa in estimativas:
        estimativa.ativa = estimativa.is_active
    
    return render(request, 'core/estimativa_custo_fixo/lista.html', {
        'estimativas': estimativas
    })

@login_required
def estimativa_custo_fixo_create(request):
    conjuntos = Conjunto.objects.all()
    
    if request.method == 'POST':
        data_estimativa = request.POST.get('data_estimativa')
        conjunto_id = request.POST.get('conjunto')
        
        # Validar dados
        if not data_estimativa or not conjunto_id:
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
            return render(request, 'core/estimativa_custo_fixo/form.html', {
                'conjuntos': conjuntos,
                'tipos': ItemCustoFixo.TIPO_CHOICES
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
        'tipos': ItemCustoFixo.TIPO_CHOICES
    })

@login_required
def estimativa_custo_fixo_edit(request, pk):
    estimativa = get_object_or_404(EstimativaCustoFixo, pk=pk)
    conjuntos = Conjunto.objects.all()
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
    
    return render(request, 'core/estimativa_custo_fixo/form.html', {
        'estimativa': estimativa,
        'conjuntos': conjuntos,
        'itens': itens,
        'tipos': ItemCustoFixo.TIPO_CHOICES
    })

@login_required
def estimativa_custo_fixo_delete(request, pk):
    estimativa = get_object_or_404(EstimativaCustoFixo, pk=pk)
    
    try:
        estimativa.delete()
        messages.success(request, 'Estimativa de custo fixo excluída com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir estimativa: {str(e)}')
    
    return redirect('core:estimativa_custo_fixo_list')

@login_required
def detalhes_estimativa_custo_fixo(request, pk):
    estimativa = get_object_or_404(EstimativaCustoFixo, pk=pk)
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
            valor_total = Decimal(data.get('valor_total', '0'))
            tipo = data.get('tipo', 'ANUAL')
            
            if tipo == 'ANUAL':
                valor_por_dia = valor_total / Decimal('365')
            elif tipo == 'MENSAL':
                valor_por_dia = valor_total / Decimal('30')
            else:
                valor_por_dia = Decimal('0')
            
            return JsonResponse({
                'valor_por_dia': float(valor_por_dia.quantize(Decimal('0.0001')))
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)
