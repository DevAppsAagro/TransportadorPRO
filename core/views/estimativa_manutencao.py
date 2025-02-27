from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from core.models.estimativa_manutencao import EstimativaManutencao, ItemManutencao
from core.models.conjunto import Conjunto
from decimal import Decimal
from django.utils import timezone
import datetime
import json

@login_required
def estimativa_manutencao_list(request):
    # Filtrar estimativas pelo usuário logado através do conjunto
    estimativas = EstimativaManutencao.objects.filter(conjunto__usuario=request.user).order_by('-data_estimativa')
    
    # Marcar as estimativas ativas
    for estimativa in estimativas:
        estimativa.ativa = estimativa.is_active
    
    return render(request, 'core/estimativa_manutencao/lista.html', {
        'estimativas': estimativas
    })

@login_required
def estimativa_manutencao_create(request):
    conjuntos = Conjunto.objects.all()
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        try:
            # Criar a estimativa principal
            estimativa = EstimativaManutencao(
                conjunto_id=request.POST.get('conjunto'),
                data_estimativa=request.POST.get('data_estimativa')
            )
            # Salvamos primeiro para obter um ID
            estimativa.save()
            
            # Processar os itens de manutenção
            descricoes = request.POST.getlist('descricao[]')
            duracoes_km = request.POST.getlist('duracao_km[]')
            custos_totais = request.POST.getlist('custo_total[]')
            
            # Lista para armazenar todos os itens
            itens_criados = []
            
            for i in range(len(descricoes)):
                if descricoes[i] and duracoes_km[i] and custos_totais[i]:
                    item = ItemManutencao(
                        estimativa=estimativa,
                        descricao=descricoes[i],
                        duracao_km=int(duracoes_km[i]),
                        custo_total=Decimal(custos_totais[i].replace(',', '.'))
                    )
                    item.save()
                    itens_criados.append(item)
            
            # Atualizamos o custo total manualmente após criar todos os itens
            if itens_criados:
                total_custo_km = sum(item.custo_por_km for item in itens_criados)
                EstimativaManutencao.objects.filter(pk=estimativa.pk).update(custo_total_km=total_custo_km)
                # Atualizamos o objeto em memória também
                estimativa.custo_total_km = total_custo_km
            
            messages.success(request, 'Estimativa de manutenção criada com sucesso!')
            return redirect('core:estimativa_manutencao_list')
        except Exception as e:
            messages.error(request, f'Erro ao criar estimativa: {str(e)}')
    
    return render(request, 'core/estimativa_manutencao/form.html', {
        'conjuntos': conjuntos,
        'titulo': 'Nova Estimativa de Manutenção',
        'today': today
    })

@login_required
def estimativa_manutencao_edit(request, pk):
    estimativa = get_object_or_404(EstimativaManutencao, pk=pk)
    conjuntos = Conjunto.objects.all()
    itens = estimativa.itens_manutencao.all()
    
    if request.method == 'POST':
        try:
            # Atualizar a estimativa principal
            estimativa.conjunto_id = request.POST.get('conjunto')
            estimativa.data_estimativa = request.POST.get('data_estimativa')
            estimativa.save()
            
            # Excluir todos os itens existentes
            estimativa.itens_manutencao.all().delete()
            
            # Processar os novos itens de manutenção
            descricoes = request.POST.getlist('descricao[]')
            duracoes_km = request.POST.getlist('duracao_km[]')
            custos_totais = request.POST.getlist('custo_total[]')
            
            # Lista para armazenar todos os itens
            itens_criados = []
            
            for i in range(len(descricoes)):
                if descricoes[i] and duracoes_km[i] and custos_totais[i]:
                    item = ItemManutencao(
                        estimativa=estimativa,
                        descricao=descricoes[i],
                        duracao_km=int(duracoes_km[i]),
                        custo_total=Decimal(custos_totais[i].replace(',', '.'))
                    )
                    item.save()
                    itens_criados.append(item)
            
            # Atualizamos o custo total manualmente após criar todos os itens
            if itens_criados:
                total_custo_km = sum(item.custo_por_km for item in itens_criados)
                EstimativaManutencao.objects.filter(pk=estimativa.pk).update(custo_total_km=total_custo_km)
                # Atualizamos o objeto em memória também
                estimativa.custo_total_km = total_custo_km
            else:
                # Se não houver itens, zeramos o custo total
                EstimativaManutencao.objects.filter(pk=estimativa.pk).update(custo_total_km=Decimal('0.0000'))
                estimativa.custo_total_km = Decimal('0.0000')
            
            messages.success(request, 'Estimativa de manutenção atualizada com sucesso!')
            return redirect('core:estimativa_manutencao_list')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar estimativa: {str(e)}')
    
    return render(request, 'core/estimativa_manutencao/form.html', {
        'estimativa': estimativa,
        'itens': itens,
        'conjuntos': conjuntos,
        'titulo': 'Editar Estimativa de Manutenção'
    })

@login_required
def detalhes_estimativa_manutencao(request, pk):
    estimativa = get_object_or_404(EstimativaManutencao, pk=pk)
    itens = estimativa.itens_manutencao.all()
    
    # Verificar se esta é a estimativa ativa (mais recente) para este conjunto
    estimativa.ativa = estimativa.is_active
    
    return render(request, 'core/estimativa_manutencao/detail.html', {
        'estimativa': estimativa,
        'itens': itens
    })

@login_required
def estimativa_manutencao_delete(request, pk):
    estimativa = get_object_or_404(EstimativaManutencao, pk=pk)
    
    try:
        estimativa.delete()
        messages.success(request, 'Estimativa de manutenção excluída com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir estimativa: {str(e)}')
    
    return redirect('core:estimativa_manutencao_list')
