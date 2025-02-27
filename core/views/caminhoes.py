from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models.caminhao import Caminhao
from datetime import datetime

@login_required
def caminhoes(request):
    caminhoes = Caminhao.objects.filter(usuario=request.user)
    return render(request, 'core/veiculos/caminhoes/lista.html', {'caminhoes': caminhoes})

@login_required
def caminhao_novo(request):
    if request.method == 'POST':
        try:
            caminhao = Caminhao(
                placa=request.POST['placa'].upper(),
                marca=request.POST['marca'],
                modelo=request.POST['modelo'],
                ano=int(request.POST['ano']),
                chassi=request.POST['chassi'],
                renavam=request.POST['renavam'],
                valor_compra=float(request.POST['valor_compra']),
                vida_util=int(request.POST['vida_util']),
                valor_residual=float(request.POST['valor_residual']),
                capacidade_carga=float(request.POST['capacidade_carga']),
                usuario=request.user
            )
            
            if request.POST.get('ultima_manutencao'):
                caminhao.ultima_manutencao = request.POST['ultima_manutencao']
            
            caminhao.save()
            messages.success(request, 'Caminhão cadastrado com sucesso!')
            return redirect('core:caminhoes')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar caminhão: {str(e)}')
    
    return render(request, 'core/veiculos/caminhoes/form.html')

@login_required
def caminhao_editar(request, id):
    caminhao = get_object_or_404(Caminhao, id=id, usuario=request.user)
    
    if request.method == 'POST':
        try:
            caminhao.placa = request.POST['placa'].upper()
            caminhao.marca = request.POST['marca']
            caminhao.modelo = request.POST['modelo']
            caminhao.ano = int(request.POST['ano'])
            caminhao.chassi = request.POST['chassi']
            caminhao.renavam = request.POST['renavam']
            caminhao.valor_compra = float(request.POST['valor_compra'])
            caminhao.vida_util = int(request.POST['vida_util'])
            caminhao.valor_residual = float(request.POST['valor_residual'])
            caminhao.capacidade_carga = float(request.POST['capacidade_carga'])
            
            if request.POST.get('ultima_manutencao'):
                caminhao.ultima_manutencao = request.POST['ultima_manutencao']
            else:
                caminhao.ultima_manutencao = None
            
            caminhao.save()
            messages.success(request, 'Caminhão atualizado com sucesso!')
            return redirect('core:caminhoes')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar caminhão: {str(e)}')
    
    return render(request, 'core/veiculos/caminhoes/form.html', {'caminhao': caminhao})

@login_required
def caminhao_excluir(request, id):
    caminhao = get_object_or_404(Caminhao, id=id, usuario=request.user)
    try:
        caminhao.delete()
        messages.success(request, 'Caminhão excluído com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir caminhão: {str(e)}')
    return redirect('core:caminhoes')

@login_required
def caminhao_detalhes(request, id):
    caminhao = get_object_or_404(Caminhao, id=id, usuario=request.user)
    return render(request, 'core/veiculos/caminhoes/detalhes.html', {'caminhao': caminhao})