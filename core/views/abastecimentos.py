from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from core.models.abastecimento import Abastecimento
from core.models.caminhao import Caminhao
from core.models.contato import Contato
from core.models.frete import Frete

@login_required
def abastecimentos(request):
    # Filtrar abastecimentos pelo usuário logado através do caminhão
    abastecimentos_list = Abastecimento.objects.filter(caminhao__usuario=request.user).order_by('-data')
    total_valor = abastecimentos_list.aggregate(total=Sum('total_valor'))['total'] or 0
    return render(request, 'core/abastecimentos/lista.html', {
        'abastecimentos': abastecimentos_list,
        'total_valor': total_valor
    })

@login_required
def abastecimento_novo(request):
    if request.method == 'POST':
        try:
            caminhao = Caminhao.objects.get(id=request.POST['caminhao'])
            abastecimento = Abastecimento(
                data=request.POST['data'],
                data_vencimento=request.POST['data_vencimento'],
                data_pagamento=request.POST.get('data_pagamento'),
                caminhao=caminhao,
                situacao=request.POST['situacao'],
                litros=Decimal(request.POST['litros']),
                valor_litro=Decimal(request.POST['valor_litro']),
                motorista=Contato.objects.get(id=request.POST['motorista']),
                posto=Contato.objects.get(id=request.POST['posto']),
                km_abastecimento=request.POST['km_abastecimento']
            )
            if 'frete' in request.POST and request.POST['frete']:
                abastecimento.frete = Frete.objects.get(id=request.POST['frete'])
            abastecimento.save()
            
            # Atualiza a quilometragem do caminhão
            caminhao.quilometragem = request.POST['km_abastecimento']
            caminhao.save()
            messages.success(request, 'Abastecimento cadastrado com sucesso!')
            return redirect('core:abastecimentos')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar abastecimento: {str(e)}')
    
    context = {
        'caminhoes': Caminhao.objects.all(),
        'motoristas': Contato.objects.filter(tipo='MOTORISTA'),
        'postos': Contato.objects.filter(tipo='POSTO'),
        'fretes': Frete.objects.filter(status='EM_ANDAMENTO')
    }
    return render(request, 'core/abastecimentos/form.html', context)

@login_required
def abastecimento_editar(request, id):
    abastecimento = get_object_or_404(Abastecimento, pk=id)
    
    if request.method == 'POST':
        try:
            caminhao = Caminhao.objects.get(id=request.POST['caminhao'])
            abastecimento.data = request.POST['data']
            abastecimento.data_vencimento = request.POST['data_vencimento']
            abastecimento.data_pagamento = request.POST.get('data_pagamento')
            abastecimento.caminhao = caminhao
            abastecimento.situacao = request.POST['situacao']
            abastecimento.litros = Decimal(request.POST['litros'])
            abastecimento.valor_litro = Decimal(request.POST['valor_litro'])
            abastecimento.motorista = Contato.objects.get(id=request.POST['motorista'])
            abastecimento.posto = Contato.objects.get(id=request.POST['posto'])
            abastecimento.km_abastecimento = request.POST['km_abastecimento']
            
            if 'frete' in request.POST and request.POST['frete']:
                abastecimento.frete = Frete.objects.get(id=request.POST['frete'])
            else:
                abastecimento.frete = None
                
            abastecimento.save()
            
            # Atualiza a quilometragem do caminhão
            caminhao.quilometragem = request.POST['km_abastecimento']
            caminhao.save()
            messages.success(request, 'Abastecimento atualizado com sucesso!')
            return redirect('core:abastecimentos')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar abastecimento: {str(e)}')
    
    context = {
        'abastecimento': abastecimento,
        'caminhoes': Caminhao.objects.all(),
        'motoristas': Contato.objects.filter(tipo='MOTORISTA'),
        'postos': Contato.objects.filter(tipo='POSTO'),
        'fretes': Frete.objects.filter(status='EM_ANDAMENTO')
    }
    return render(request, 'core/abastecimentos/form.html', context)

@login_required
def abastecimento_excluir(request, id):
    abastecimento = get_object_or_404(Abastecimento, pk=id)
    try:
        abastecimento.delete()
        messages.success(request, 'Abastecimento excluído com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir abastecimento: {str(e)}')
    return redirect('core:abastecimentos')