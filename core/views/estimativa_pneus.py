from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models.estimativa_pneus import EstimativaPneus
from core.models.conjunto import Conjunto
from django.core.paginator import Paginator
from decimal import Decimal
from django.utils import timezone
import datetime

@login_required
def estimativa_pneus_list(request):
    estimativas = EstimativaPneus.objects.all().order_by('-data_estimativa')
    paginator = Paginator(estimativas, 10)
    page = request.GET.get('page')
    estimativas_paginadas = paginator.get_page(page)
    
    return render(request, 'core/estimativa_pneus/lista.html', {
        'estimativas': estimativas_paginadas
    })

@login_required
def estimativa_pneus_create(request):
    conjuntos = Conjunto.objects.all()
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        try:
            data_estimativa = request.POST.get('data_estimativa')
            
            estimativa = EstimativaPneus(
                conjunto_id=request.POST.get('conjunto'),
                data_estimativa=data_estimativa,
                qtd_pneus_dianteiros=int(request.POST.get('qtd_pneus_dianteiros', 2)),
                qtd_pneus_traseiros=int(request.POST.get('qtd_pneus_traseiros', 8)),
                qtd_pneus_carreta=int(request.POST.get('qtd_pneus_carreta', 12)),
                preco_pneu_dianteiro=Decimal(request.POST.get('preco_pneu_dianteiro', '0')),
                preco_pneu_traseiro=Decimal(request.POST.get('preco_pneu_traseiro', '0')),
                preco_pneu_carreta=Decimal(request.POST.get('preco_pneu_carreta', '0')),
                km_vida_util_dianteiro=int(request.POST.get('km_vida_util_dianteiro', 0)),
                km_vida_util_traseiro=int(request.POST.get('km_vida_util_traseiro', 0)),
                km_vida_util_carreta=int(request.POST.get('km_vida_util_carreta', 0)),
                num_recapagens_dianteiro=int(request.POST.get('num_recapagens_dianteiro', 1)),
                num_recapagens_traseiro=int(request.POST.get('num_recapagens_traseiro', 2)),
                num_recapagens_carreta=int(request.POST.get('num_recapagens_carreta', 2)),
                custo_recapagem_dianteiro=Decimal(request.POST.get('custo_recapagem_dianteiro', '0')),
                custo_recapagem_traseiro=Decimal(request.POST.get('custo_recapagem_traseiro', '0')),
                custo_recapagem_carreta=Decimal(request.POST.get('custo_recapagem_carreta', '0'))
            )
            estimativa.save()
            messages.success(request, 'Estimativa criada com sucesso!')
            return redirect('core:estimativa_pneus_list')
        except Exception as e:
            messages.error(request, f'Erro ao criar estimativa: {str(e)}')
    
    return render(request, 'core/estimativa_pneus/form.html', {
        'conjuntos': conjuntos,
        'titulo': 'Nova Estimativa de Pneus',
        'today': today
    })

@login_required
def estimativa_pneus_edit(request, pk):
    estimativa = get_object_or_404(EstimativaPneus, pk=pk)
    conjuntos = Conjunto.objects.all()
    
    if request.method == 'POST':
        try:
            estimativa.conjunto_id = request.POST.get('conjunto')
            estimativa.data_estimativa = request.POST.get('data_estimativa')
            estimativa.qtd_pneus_dianteiros = int(request.POST.get('qtd_pneus_dianteiros', 2))
            estimativa.qtd_pneus_traseiros = int(request.POST.get('qtd_pneus_traseiros', 8))
            estimativa.qtd_pneus_carreta = int(request.POST.get('qtd_pneus_carreta', 12))
            estimativa.preco_pneu_dianteiro = Decimal(request.POST.get('preco_pneu_dianteiro', '0'))
            estimativa.preco_pneu_traseiro = Decimal(request.POST.get('preco_pneu_traseiro', '0'))
            estimativa.preco_pneu_carreta = Decimal(request.POST.get('preco_pneu_carreta', '0'))
            estimativa.km_vida_util_dianteiro = int(request.POST.get('km_vida_util_dianteiro', 0))
            estimativa.km_vida_util_traseiro = int(request.POST.get('km_vida_util_traseiro', 0))
            estimativa.km_vida_util_carreta = int(request.POST.get('km_vida_util_carreta', 0))
            estimativa.num_recapagens_dianteiro = int(request.POST.get('num_recapagens_dianteiro', 1))
            estimativa.num_recapagens_traseiro = int(request.POST.get('num_recapagens_traseiro', 2))
            estimativa.num_recapagens_carreta = int(request.POST.get('num_recapagens_carreta', 2))
            estimativa.custo_recapagem_dianteiro = Decimal(request.POST.get('custo_recapagem_dianteiro', '0'))
            estimativa.custo_recapagem_traseiro = Decimal(request.POST.get('custo_recapagem_traseiro', '0'))
            estimativa.custo_recapagem_carreta = Decimal(request.POST.get('custo_recapagem_carreta', '0'))
            
            estimativa.save()
            messages.success(request, 'Estimativa atualizada com sucesso!')
            return redirect('core:estimativa_pneus_list')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar estimativa: {str(e)}')
    
    return render(request, 'core/estimativa_pneus/form.html', {
        'estimativa': estimativa,
        'conjuntos': conjuntos,
        'titulo': 'Editar Estimativa de Pneus',
        'today': datetime.date.today().strftime('%Y-%m-%d')
    })

@login_required
def detalhes_estimativa(request, pk):
    estimativa = get_object_or_404(EstimativaPneus, pk=pk)
    resultados = estimativa.calcular_custo_pneus()
    
    return render(request, 'core/estimativa_pneus/detail.html', {
        'estimativa': estimativa,
        'resultados': resultados
    })

@login_required
def estimativa_pneus_delete(request, pk):
    estimativa = get_object_or_404(EstimativaPneus, pk=pk)
    try:
        estimativa.delete()
        messages.success(request, 'Estimativa excluída com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir estimativa: {str(e)}')
    return redirect('core:estimativa_pneus_list')