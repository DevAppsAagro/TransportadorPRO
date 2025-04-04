from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from django.http import JsonResponse
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
def abastecimento_detalhe(request, id):
    # Obter o abastecimento pelo ID
    abastecimento = get_object_or_404(Abastecimento, id=id, caminhao__usuario=request.user)
    return render(request, 'core/abastecimentos/detalhe.html', {
        'abastecimento': abastecimento
    })

@login_required
def abastecimento_novo(request):
    if request.method == 'POST':
        try:
            caminhao = Caminhao.objects.get(id=request.POST['caminhao'], usuario=request.user)
            abastecimento = Abastecimento(
                data=request.POST['data'],
                data_vencimento=request.POST['data_vencimento'],
                data_pagamento=request.POST.get('data_pagamento'),
                caminhao=caminhao,
                situacao=request.POST['situacao'],
                tipo_combustivel=request.POST['tipo_combustivel'],
                litros=Decimal(request.POST['litros']),
                valor_litro=Decimal(request.POST['valor_litro']),
                motorista=Contato.objects.get(id=request.POST['motorista'], usuario=request.user),
                posto=Contato.objects.get(id=request.POST['posto'], usuario=request.user),
                km_abastecimento=request.POST['km_abastecimento']
            )
            if 'frete' in request.POST and request.POST['frete']:
                abastecimento.frete = Frete.objects.get(id=request.POST['frete'], caminhao__usuario=request.user)
            abastecimento.save()
            
            # Atualiza a quilometragem do caminhão
            caminhao.quilometragem = request.POST['km_abastecimento']
            caminhao.save()
            messages.success(request, 'Abastecimento cadastrado com sucesso!')
            return redirect('core:abastecimentos')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar abastecimento: {str(e)}')
    
    context = {
        'caminhoes': Caminhao.objects.filter(usuario=request.user),
        'motoristas': Contato.objects.filter(tipo='MOTORISTA', usuario=request.user),
        'postos': Contato.objects.filter(tipo='POSTO', usuario=request.user),
        'fretes': Frete.objects.filter(caminhao__usuario=request.user).order_by('-data_saida')[:10]
    }
    return render(request, 'core/abastecimentos/form.html', context)

@login_required
def abastecimento_editar(request, id):
    # Garantir que o usuário só possa editar seus próprios abastecimentos
    abastecimento = get_object_or_404(Abastecimento, pk=id, caminhao__usuario=request.user)
    
    if request.method == 'POST':
        try:
            caminhao = Caminhao.objects.get(id=request.POST['caminhao'], usuario=request.user)
            abastecimento.data = request.POST['data']
            abastecimento.data_vencimento = request.POST['data_vencimento']
            abastecimento.data_pagamento = request.POST.get('data_pagamento')
            abastecimento.caminhao = caminhao
            abastecimento.situacao = request.POST['situacao']
            abastecimento.tipo_combustivel = request.POST['tipo_combustivel']
            abastecimento.litros = Decimal(request.POST['litros'])
            abastecimento.valor_litro = Decimal(request.POST['valor_litro'])
            abastecimento.motorista = Contato.objects.get(id=request.POST['motorista'], usuario=request.user)
            abastecimento.posto = Contato.objects.get(id=request.POST['posto'], usuario=request.user)
            abastecimento.km_abastecimento = request.POST['km_abastecimento']
            
            if 'frete' in request.POST and request.POST['frete']:
                abastecimento.frete = Frete.objects.get(id=request.POST['frete'], caminhao__usuario=request.user)
            else:
                abastecimento.frete = None
                
            abastecimento.save()
            messages.success(request, 'Abastecimento atualizado com sucesso!')
            return redirect('core:abastecimentos')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar abastecimento: {str(e)}')
    
    context = {
        'abastecimento': abastecimento,
        'caminhoes': Caminhao.objects.filter(usuario=request.user),
        'motoristas': Contato.objects.filter(tipo='MOTORISTA', usuario=request.user),
        'postos': Contato.objects.filter(tipo='POSTO', usuario=request.user),
        'fretes': Frete.objects.filter(caminhao__usuario=request.user).order_by('-data_saida')[:10]
    }
    return render(request, 'core/abastecimentos/form.html', context)

@login_required
def abastecimento_excluir(request, id):
    # Garantir que o usuário só possa excluir seus próprios abastecimentos
    abastecimento = get_object_or_404(Abastecimento, pk=id, caminhao__usuario=request.user)
    try:
        abastecimento.delete()
        messages.success(request, 'Abastecimento excluído com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir abastecimento: {str(e)}')
    return redirect('core:abastecimentos')

@login_required
def buscar_frete_por_id(request, id):
    try:
        # Garantir que o usuário só possa ver seus próprios fretes
        frete = get_object_or_404(Frete, pk=id, caminhao__usuario=request.user)
        
        # Retornar os dados do frete em formato JSON
        return JsonResponse({
            'id': frete.id,
            'origem': frete.origem,
            'destino': frete.destino,
            'data_saida': frete.data_saida.strftime('%Y-%m-%d'),
            'status': frete.status,
            'caminhao_id': frete.caminhao.id,
            'caminhao_placa': frete.caminhao.placa,
            'caminhao_modelo': frete.caminhao.modelo
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)

@login_required
def buscar_fretes_por_caminhao(request, caminhao_id):
    print(f"Buscando fretes para o caminhão {caminhao_id}")
    try:
        # Buscar o caminhão sem verificar o usuário (temporariamente para debug)
        caminhao = get_object_or_404(Caminhao, pk=caminhao_id)
        
        # Buscar os 50 fretes mais recentes deste caminhão
        fretes = Frete.objects.filter(caminhao=caminhao).order_by('-data_saida')[:50]
        
        # Preparar os dados para retornar em formato JSON
        fretes_data = []
        for frete in fretes:
            fretes_data.append({
                'id': frete.id,
                'origem': frete.origem,
                'destino': frete.destino,
                'data_saida': frete.data_saida.strftime('%Y-%m-%d'),
                'status': frete.status,
                'caminhao_id': frete.caminhao.id,
                'caminhao_placa': frete.caminhao.placa,
                'caminhao_modelo': frete.caminhao.modelo
            })
        
        return JsonResponse({'fretes': fretes_data})
    except Exception as e:
        print(f"Erro ao buscar fretes: {str(e)}")
        return JsonResponse({'error': str(e)}, status=404)