from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import date
import json

from core.models.despesa import Despesa
from core.models.categoria import Categoria
from core.models.subcategoria import Subcategoria
from core.models.caminhao import Caminhao
from core.models.carreta import Carreta
from core.models.frete import Frete
from core.models.empresa import Empresa
from core.models.contato import Contato

@login_required
def despesa_list(request):
    """Lista todas as despesas com filtros por status"""
    status_filter = request.GET.get('status', '')
    
    despesas = Despesa.objects.all().order_by('-data_vencimento')
    
    # Aplicar filtros
    if status_filter:
        hoje = date.today()
        if status_filter == 'PENDENTE':
            despesas = despesas.filter(data_pagamento__isnull=True, data_vencimento__gt=hoje)
        elif status_filter == 'VENCE_HOJE':
            despesas = despesas.filter(data_pagamento__isnull=True, data_vencimento=hoje)
        elif status_filter == 'VENCIDA':
            despesas = despesas.filter(data_pagamento__isnull=True, data_vencimento__lt=hoje)
        elif status_filter == 'PAGA':
            despesas = despesas.filter(data_pagamento__isnull=False)
    
    # Adicionar status calculado para cada despesa
    for despesa in despesas:
        despesa.status_calculado = despesa.status
        despesa.status_display_calculado = despesa.status_display
    
    return render(request, 'core/despesa/lista.html', {
        'despesas': despesas,
        'status_filter': status_filter
    })

@login_required
def despesa_create(request):
    """Cria uma nova despesa"""
    categorias = Categoria.objects.all()
    subcategorias = Subcategoria.objects.all()
    caminhoes = Caminhao.objects.all()
    carretas = Carreta.objects.all()
    fretes = Frete.objects.all()
    empresas = Empresa.objects.all()
    contatos = Contato.objects.all()
    
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            data = request.POST.get('data')
            data_vencimento = request.POST.get('data_vencimento')
            data_pagamento = request.POST.get('data_pagamento') or None
            valor = request.POST.get('valor')
            categoria_id = request.POST.get('categoria')
            subcategoria_id = request.POST.get('subcategoria')
            contato_id = request.POST.get('contato') or None
            observacao = request.POST.get('observacao', '')
            
            # Obter destino baseado na alocação da categoria
            categoria = Categoria.objects.get(id=categoria_id)
            alocacao = categoria.alocacao
            
            # Inicializar campos de destino
            caminhao_id = None
            carreta_id = None
            frete_id = None
            empresa_id = None
            
            if alocacao == 'VEICULO':
                caminhao_id = request.POST.get('caminhao') or None
                carreta_id = request.POST.get('carreta') or None
            elif alocacao == 'FRETE':
                frete_id = request.POST.get('frete') or None
            elif alocacao == 'ADMINISTRATIVO':
                empresa_id = request.POST.get('empresa') or None
            
            # Criar a despesa
            despesa = Despesa(
                data=data,
                data_vencimento=data_vencimento,
                data_pagamento=data_pagamento,
                valor=valor,
                categoria_id=categoria_id,
                subcategoria_id=subcategoria_id,
                caminhao_id=caminhao_id,
                carreta_id=carreta_id,
                frete_id=frete_id,
                empresa_id=empresa_id,
                contato_id=contato_id,
                observacao=observacao
            )
            despesa.save()
            
            messages.success(request, 'Despesa criada com sucesso!')
            return redirect('core:despesa_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar despesa: {str(e)}')
    
    return render(request, 'core/despesa/form.html', {
        'categorias': categorias,
        'subcategorias': subcategorias,
        'caminhoes': caminhoes,
        'carretas': carretas,
        'fretes': fretes,
        'empresas': empresas,
        'contatos': contatos
    })

@login_required
def despesa_edit(request, pk):
    """Edita uma despesa existente"""
    despesa = get_object_or_404(Despesa, pk=pk)
    categorias = Categoria.objects.all()
    subcategorias = Subcategoria.objects.all()
    caminhoes = Caminhao.objects.all()
    carretas = Carreta.objects.all()
    fretes = Frete.objects.all()
    empresas = Empresa.objects.all()
    contatos = Contato.objects.all()
    
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            despesa.data = request.POST.get('data')
            despesa.data_vencimento = request.POST.get('data_vencimento')
            despesa.data_pagamento = request.POST.get('data_pagamento') or None
            despesa.valor = request.POST.get('valor')
            despesa.categoria_id = request.POST.get('categoria')
            despesa.subcategoria_id = request.POST.get('subcategoria')
            despesa.contato_id = request.POST.get('contato') or None
            despesa.observacao = request.POST.get('observacao', '')
            
            # Obter destino baseado na alocação da categoria
            categoria = Categoria.objects.get(id=despesa.categoria_id)
            alocacao = categoria.alocacao
            
            # Inicializar campos de destino
            despesa.caminhao_id = None
            despesa.carreta_id = None
            despesa.frete_id = None
            despesa.empresa_id = None
            
            if alocacao == 'VEICULO':
                despesa.caminhao_id = request.POST.get('caminhao') or None
                despesa.carreta_id = request.POST.get('carreta') or None
            elif alocacao == 'FRETE':
                despesa.frete_id = request.POST.get('frete') or None
            elif alocacao == 'ADMINISTRATIVO':
                despesa.empresa_id = request.POST.get('empresa') or None
            
            despesa.save()
            
            messages.success(request, 'Despesa atualizada com sucesso!')
            return redirect('core:despesa_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar despesa: {str(e)}')
    
    return render(request, 'core/despesa/form.html', {
        'despesa': despesa,
        'categorias': categorias,
        'subcategorias': subcategorias,
        'caminhoes': caminhoes,
        'carretas': carretas,
        'fretes': fretes,
        'empresas': empresas,
        'contatos': contatos
    })

@login_required
def despesa_delete(request, pk):
    """Exclui uma despesa"""
    despesa = get_object_or_404(Despesa, pk=pk)
    
    if request.method == 'POST':
        try:
            despesa.delete()
            messages.success(request, 'Despesa excluída com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao excluir despesa: {str(e)}')
        
        return redirect('core:despesa_list')
    
    return render(request, 'core/despesa/confirm_delete.html', {
        'despesa': despesa
    })

@login_required
def despesa_detail(request, pk):
    """Exibe os detalhes de uma despesa"""
    despesa = get_object_or_404(Despesa, pk=pk)
    
    return render(request, 'core/despesa/detail.html', {
        'despesa': despesa
    })

@login_required
def registrar_pagamento(request, pk):
    """Registra o pagamento de uma despesa"""
    if request.method == 'POST':
        try:
            despesa = get_object_or_404(Despesa, pk=pk)
            data_pagamento = request.POST.get('data_pagamento')
            
            if data_pagamento:
                despesa.data_pagamento = data_pagamento
                despesa.save()
                messages.success(request, 'Pagamento registrado com sucesso!')
            else:
                messages.error(request, 'Data de pagamento é obrigatória.')
            
            return redirect('core:despesa_detail', pk=pk)
            
        except Exception as e:
            messages.error(request, f'Erro ao registrar pagamento: {str(e)}')
            return redirect('core:despesa_detail', pk=pk)
    
    return redirect('core:despesa_list')

@login_required
def get_subcategorias(request):
    """Retorna as subcategorias de uma categoria em formato JSON"""
    categoria_id = request.GET.get('categoria_id')
    subcategorias = Subcategoria.objects.filter(categoria_id=categoria_id).values('id', 'nome')
    return JsonResponse(list(subcategorias), safe=False)

@login_required
def get_destinos_por_alocacao(request):
    """Retorna os destinos disponíveis baseados na alocação da categoria"""
    categoria_id = request.GET.get('categoria_id')
    
    try:
        categoria = Categoria.objects.get(id=categoria_id)
        alocacao = categoria.alocacao
        
        if alocacao == 'VEICULO':
            caminhoes = list(Caminhao.objects.values('id', 'placa', 'marca', 'modelo'))
            carretas = list(Carreta.objects.values('id', 'placa', 'marca', 'modelo'))
            return JsonResponse({
                'alocacao': alocacao,
                'caminhoes': caminhoes,
                'carretas': carretas
            })
        elif alocacao == 'FRETE':
            fretes = list(Frete.objects.values('id', 'cliente__nome_completo', 'origem', 'destino', 'data_saida'))
            return JsonResponse({
                'alocacao': alocacao,
                'fretes': fretes
            })
        elif alocacao == 'ADMINISTRATIVO':
            empresas = list(Empresa.objects.values('id', 'nome', 'razao_social', 'cnpj'))
            return JsonResponse({
                'alocacao': alocacao,
                'empresas': empresas
            })
        
        return JsonResponse({'alocacao': alocacao})
        
    except Categoria.DoesNotExist:
        return JsonResponse({'error': 'Categoria não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
