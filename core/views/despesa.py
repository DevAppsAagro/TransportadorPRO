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
    
    # Filtrar despesas pelo usuário logado através dos relacionamentos
    # Uma despesa pode estar relacionada a um caminhão, carreta, frete ou empresa
    # Todos esses modelos têm um campo 'usuario'
    despesas = Despesa.objects.filter(
        Q(caminhao__usuario=request.user) | 
        Q(carreta__usuario=request.user) | 
        Q(frete__caminhao__usuario=request.user) | 
        Q(empresa__usuario=request.user)
    ).distinct().order_by('-data_vencimento')
    
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
    # Filtrar por usuário
    categorias = Categoria.objects.filter(Q(usuario=request.user) | Q(usuario__isnull=True))
    subcategorias = Subcategoria.objects.filter(categoria__in=categorias)
    caminhoes = Caminhao.objects.filter(usuario=request.user)
    carretas = Carreta.objects.filter(usuario=request.user)
    fretes = Frete.objects.filter(caminhao__usuario=request.user)
    empresas = Empresa.objects.filter(usuario=request.user)
    contatos = Contato.objects.filter(usuario=request.user)
    
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
                # Verificar se o caminhão pertence ao usuário
                if request.POST.get('caminhao'):
                    caminhao = get_object_or_404(Caminhao, id=request.POST.get('caminhao'), usuario=request.user)
                    caminhao_id = caminhao.id
                # Verificar se a carreta pertence ao usuário
                if request.POST.get('carreta'):
                    carreta = get_object_or_404(Carreta, id=request.POST.get('carreta'), usuario=request.user)
                    carreta_id = carreta.id
            elif alocacao == 'FRETE':
                # Verificar se o frete pertence ao usuário
                if request.POST.get('frete'):
                    frete = get_object_or_404(Frete, id=request.POST.get('frete'), caminhao__usuario=request.user)
                    frete_id = frete.id
            elif alocacao == 'ADMINISTRATIVO':
                # Verificar se a empresa pertence ao usuário
                if request.POST.get('empresa'):
                    empresa = get_object_or_404(Empresa, id=request.POST.get('empresa'), usuario=request.user)
                    empresa_id = empresa.id
            
            # Verificar se o contato pertence ao usuário
            if contato_id:
                contato = get_object_or_404(Contato, id=contato_id, usuario=request.user)
                contato_id = contato.id
            
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
    # Garantir que a despesa pertence ao usuário
    despesa = get_object_or_404(
        Despesa, 
        filter=Q(pk=pk) & (
            Q(caminhao__usuario=request.user) | 
            Q(carreta__usuario=request.user) | 
            Q(frete__caminhao__usuario=request.user) | 
            Q(empresa__usuario=request.user)
        )
    )
    
    # Filtrar por usuário
    categorias = Categoria.objects.filter(Q(usuario=request.user) | Q(usuario__isnull=True))
    subcategorias = Subcategoria.objects.filter(categoria__in=categorias)
    caminhoes = Caminhao.objects.filter(usuario=request.user)
    carretas = Carreta.objects.filter(usuario=request.user)
    fretes = Frete.objects.filter(caminhao__usuario=request.user)
    empresas = Empresa.objects.filter(usuario=request.user)
    contatos = Contato.objects.filter(usuario=request.user)
    
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            despesa.data = request.POST.get('data')
            despesa.data_vencimento = request.POST.get('data_vencimento')
            despesa.data_pagamento = request.POST.get('data_pagamento') or None
            despesa.valor = request.POST.get('valor')
            despesa.categoria_id = request.POST.get('categoria')
            despesa.subcategoria_id = request.POST.get('subcategoria')
            despesa.observacao = request.POST.get('observacao', '')
            
            # Obter destino baseado na alocação da categoria
            categoria = Categoria.objects.get(id=despesa.categoria_id)
            alocacao = categoria.alocacao
            
            # Inicializar campos de destino
            despesa.caminhao_id = None
            despesa.carreta_id = None
            despesa.frete_id = None
            despesa.empresa_id = None
            despesa.contato_id = None
            
            # Verificar se o contato pertence ao usuário
            contato_id = request.POST.get('contato')
            if contato_id:
                contato = get_object_or_404(Contato, id=contato_id, usuario=request.user)
                despesa.contato_id = contato.id
            
            if alocacao == 'VEICULO':
                # Verificar se o caminhão pertence ao usuário
                if request.POST.get('caminhao'):
                    caminhao = get_object_or_404(Caminhao, id=request.POST.get('caminhao'), usuario=request.user)
                    despesa.caminhao_id = caminhao.id
                # Verificar se a carreta pertence ao usuário
                if request.POST.get('carreta'):
                    carreta = get_object_or_404(Carreta, id=request.POST.get('carreta'), usuario=request.user)
                    despesa.carreta_id = carreta.id
            elif alocacao == 'FRETE':
                # Verificar se o frete pertence ao usuário
                if request.POST.get('frete'):
                    frete = get_object_or_404(Frete, id=request.POST.get('frete'), caminhao__usuario=request.user)
                    despesa.frete_id = frete.id
            elif alocacao == 'ADMINISTRATIVO':
                # Verificar se a empresa pertence ao usuário
                if request.POST.get('empresa'):
                    empresa = get_object_or_404(Empresa, id=request.POST.get('empresa'), usuario=request.user)
                    despesa.empresa_id = empresa.id
            
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
    # Garantir que a despesa pertence ao usuário
    despesa = get_object_or_404(
        Despesa, 
        filter=Q(pk=pk) & (
            Q(caminhao__usuario=request.user) | 
            Q(carreta__usuario=request.user) | 
            Q(frete__caminhao__usuario=request.user) | 
            Q(empresa__usuario=request.user)
        )
    )
    
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
    # Garantir que a despesa pertence ao usuário
    despesa = get_object_or_404(
        Despesa, 
        filter=Q(pk=pk) & (
            Q(caminhao__usuario=request.user) | 
            Q(carreta__usuario=request.user) | 
            Q(frete__caminhao__usuario=request.user) | 
            Q(empresa__usuario=request.user)
        )
    )
    
    return render(request, 'core/despesa/detail.html', {
        'despesa': despesa
    })

@login_required
def registrar_pagamento(request, pk):
    """Registra o pagamento de uma despesa"""
    if request.method == 'POST':
        try:
            # Garantir que a despesa pertence ao usuário
            despesa = get_object_or_404(
                Despesa, 
                filter=Q(pk=pk) & (
                    Q(caminhao__usuario=request.user) | 
                    Q(carreta__usuario=request.user) | 
                    Q(frete__caminhao__usuario=request.user) | 
                    Q(empresa__usuario=request.user)
                )
            )
            
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
    
    # Verificar se a categoria pertence ao usuário ou é padrão (usuário nulo)
    categoria = get_object_or_404(
        Categoria, 
        filter=Q(id=categoria_id) & (
            Q(usuario=request.user) | Q(usuario__isnull=True)
        )
    )
    
    subcategorias = Subcategoria.objects.filter(categoria_id=categoria_id).values('id', 'nome')
    return JsonResponse(list(subcategorias), safe=False)

@login_required
def get_destinos_por_alocacao(request):
    """Retorna os destinos disponíveis baseados na alocação da categoria"""
    categoria_id = request.GET.get('categoria_id')
    
    try:
        # Verificar se a categoria pertence ao usuário ou é padrão (usuário nulo)
        categoria = get_object_or_404(
            Categoria, 
            filter=Q(id=categoria_id) & (
                Q(usuario=request.user) | Q(usuario__isnull=True)
            )
        )
        
        alocacao = categoria.alocacao
        
        if alocacao == 'VEICULO':
            # Filtrar por usuário
            caminhoes = list(Caminhao.objects.filter(usuario=request.user).values('id', 'placa', 'marca', 'modelo'))
            carretas = list(Carreta.objects.filter(usuario=request.user).values('id', 'placa', 'marca', 'modelo'))
            return JsonResponse({
                'alocacao': alocacao,
                'caminhoes': caminhoes,
                'carretas': carretas
            })
        elif alocacao == 'FRETE':
            # Filtrar por usuário
            fretes = list(Frete.objects.filter(caminhao__usuario=request.user).values('id', 'cliente__nome_completo', 'origem', 'destino', 'data_saida'))
            return JsonResponse({
                'alocacao': alocacao,
                'fretes': fretes
            })
        elif alocacao == 'ADMINISTRATIVO':
            # Filtrar por usuário
            empresas = list(Empresa.objects.filter(usuario=request.user).values('id', 'nome_fantasia', 'razao_social', 'cnpj'))
            return JsonResponse({
                'alocacao': alocacao,
                'empresas': empresas
            })
        
        return JsonResponse({'alocacao': alocacao})
        
    except Categoria.DoesNotExist:
        return JsonResponse({'error': 'Categoria não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
