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
    # Filtrar estimativas pelo usuário logado através do conjunto
    estimativas = EstimativaPneus.objects.filter(conjunto__usuario=request.user).order_by('-data_estimativa')
    paginator = Paginator(estimativas, 10)
    page = request.GET.get('page')
    estimativas_paginadas = paginator.get_page(page)
    
    return render(request, 'core/estimativa_pneus/lista.html', {
        'estimativas': estimativas_paginadas
    })

@login_required
def estimativa_pneus_create(request):
    conjuntos = Conjunto.objects.filter(usuario=request.user)
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        try:
            data_estimativa = request.POST.get('data_estimativa')
            
            # Garantir que os valores decimais com vírgula sejam convertidos corretamente
            estimativa = EstimativaPneus(
                conjunto_id=request.POST.get('conjunto'),
                data_estimativa=data_estimativa,
                qtd_pneus_dianteiros=int(request.POST.get('qtd_pneus_dianteiros', 2)),
                qtd_pneus_traseiros=int(request.POST.get('qtd_pneus_traseiros', 8)),
                qtd_pneus_carreta=int(request.POST.get('qtd_pneus_carreta', 12)),
                preco_pneu_dianteiro=Decimal(request.POST.get('preco_pneu_dianteiro', '0').replace(',', '.')),
                preco_pneu_traseiro=Decimal(request.POST.get('preco_pneu_traseiro', '0').replace(',', '.')),
                preco_pneu_carreta=Decimal(request.POST.get('preco_pneu_carreta', '0').replace(',', '.')),
                km_vida_util_dianteiro=int(request.POST.get('km_vida_util_dianteiro', 0)),
                km_vida_util_traseiro=int(request.POST.get('km_vida_util_traseiro', 0)),
                km_vida_util_carreta=int(request.POST.get('km_vida_util_carreta', 0)),
                num_recapagens_dianteiro=int(request.POST.get('num_recapagens_dianteiro', 1)),
                num_recapagens_traseiro=int(request.POST.get('num_recapagens_traseiro', 2)),
                num_recapagens_carreta=int(request.POST.get('num_recapagens_carreta', 2)),
                custo_recapagem_dianteiro=Decimal(request.POST.get('custo_recapagem_dianteiro', '0').replace(',', '.')),
                custo_recapagem_traseiro=Decimal(request.POST.get('custo_recapagem_traseiro', '0').replace(',', '.')),
                custo_recapagem_carreta=Decimal(request.POST.get('custo_recapagem_carreta', '0').replace(',', '.'))
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
def estimativa_pneus_edit(request, id):
    estimativa = get_object_or_404(EstimativaPneus, pk=id)
    conjuntos = Conjunto.objects.filter(usuario=request.user)
    
    if request.method == 'POST':
        try:
            estimativa.conjunto_id = request.POST.get('conjunto')
            estimativa.data_estimativa = request.POST.get('data_estimativa')
            estimativa.qtd_pneus_dianteiros = int(request.POST.get('qtd_pneus_dianteiros', 2))
            estimativa.qtd_pneus_traseiros = int(request.POST.get('qtd_pneus_traseiros', 8))
            estimativa.qtd_pneus_carreta = int(request.POST.get('qtd_pneus_carreta', 12))
            
            # Garantir que os valores decimais sejam processados corretamente
            # O JavaScript já deve ter convertido vírgulas para pontos antes do envio
            estimativa.preco_pneu_dianteiro = Decimal(request.POST.get('preco_pneu_dianteiro', '0').replace(',', '.'))
            estimativa.preco_pneu_traseiro = Decimal(request.POST.get('preco_pneu_traseiro', '0').replace(',', '.'))
            estimativa.preco_pneu_carreta = Decimal(request.POST.get('preco_pneu_carreta', '0').replace(',', '.'))
            
            estimativa.km_vida_util_dianteiro = int(request.POST.get('km_vida_util_dianteiro', 0))
            estimativa.km_vida_util_traseiro = int(request.POST.get('km_vida_util_traseiro', 0))
            estimativa.km_vida_util_carreta = int(request.POST.get('km_vida_util_carreta', 0))
            estimativa.num_recapagens_dianteiro = int(request.POST.get('num_recapagens_dianteiro', 1))
            estimativa.num_recapagens_traseiro = int(request.POST.get('num_recapagens_traseiro', 2))
            estimativa.num_recapagens_carreta = int(request.POST.get('num_recapagens_carreta', 2))
            
            # Garantir que os valores decimais sejam processados corretamente
            estimativa.custo_recapagem_dianteiro = Decimal(request.POST.get('custo_recapagem_dianteiro', '0').replace(',', '.'))
            estimativa.custo_recapagem_traseiro = Decimal(request.POST.get('custo_recapagem_traseiro', '0').replace(',', '.'))
            estimativa.custo_recapagem_carreta = Decimal(request.POST.get('custo_recapagem_carreta', '0').replace(',', '.'))
            
            estimativa.save()
            messages.success(request, 'Estimativa atualizada com sucesso!')
            return redirect('core:estimativa_pneus_list')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar estimativa: {str(e)}')
    
    # Criar um dicionário com os valores formatados para o template
    # Agora vamos usar vírgula para exibição no padrão brasileiro
    estimativa_dict = {
        'id': estimativa.id,
        'conjunto_id': estimativa.conjunto_id,
        'data_estimativa': estimativa.data_estimativa,
        'qtd_pneus_dianteiros': estimativa.qtd_pneus_dianteiros,
        'qtd_pneus_traseiros': estimativa.qtd_pneus_traseiros,
        'qtd_pneus_carreta': estimativa.qtd_pneus_carreta,
        'preco_pneu_dianteiro': str(estimativa.preco_pneu_dianteiro).replace('.', ','),
        'preco_pneu_traseiro': str(estimativa.preco_pneu_traseiro).replace('.', ','),
        'preco_pneu_carreta': str(estimativa.preco_pneu_carreta).replace('.', ','),
        'km_vida_util_dianteiro': estimativa.km_vida_util_dianteiro,
        'km_vida_util_traseiro': estimativa.km_vida_util_traseiro,
        'km_vida_util_carreta': estimativa.km_vida_util_carreta,
        'num_recapagens_dianteiro': estimativa.num_recapagens_dianteiro,
        'num_recapagens_traseiro': estimativa.num_recapagens_traseiro,
        'num_recapagens_carreta': estimativa.num_recapagens_carreta,
        'custo_recapagem_dianteiro': str(estimativa.custo_recapagem_dianteiro).replace('.', ','),
        'custo_recapagem_traseiro': str(estimativa.custo_recapagem_traseiro).replace('.', ','),
        'custo_recapagem_carreta': str(estimativa.custo_recapagem_carreta).replace('.', ','),
    }
    
    return render(request, 'core/estimativa_pneus/form.html', {
        'estimativa': estimativa_dict,
        'conjuntos': conjuntos,
        'titulo': 'Editar Estimativa de Pneus',
        'today': datetime.date.today().strftime('%Y-%m-%d')
    })

@login_required
def detalhes_estimativa(request, id):
    estimativa = get_object_or_404(EstimativaPneus, pk=id)
    resultados = estimativa.calcular_custo_pneus()
    
    return render(request, 'core/estimativa_pneus/detail.html', {
        'estimativa': estimativa,
        'resultados': resultados
    })

@login_required
def estimativa_pneus_delete(request, id):
    estimativa = get_object_or_404(EstimativaPneus, pk=id)
    try:
        estimativa.delete()
        messages.success(request, 'Estimativa excluída com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir estimativa: {str(e)}')
    return redirect('core:estimativa_pneus_list')