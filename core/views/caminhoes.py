from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models.caminhao import Caminhao
from datetime import datetime

# Função para converter valores formatados no padrão brasileiro para float
def converter_para_float(valor_str):
    if not valor_str:
        return 0.0
    # Remove os pontos de milhar e substitui a vírgula decimal por ponto
    valor_str = valor_str.replace('.', '').replace(',', '.')
    return float(valor_str)

@login_required
def caminhoes(request):
    caminhoes = Caminhao.objects.filter(usuario=request.user)
    return render(request, 'core/veiculos/caminhoes/lista.html', {'caminhoes': caminhoes})

@login_required
def caminhao_novo(request):
    if request.method == 'POST':
        try:
            # Obter valores do formulário
            placa = request.POST['placa'].upper()
            chassi = request.POST['chassi']
            renavam = request.POST['renavam']
            
            # Verificar se já existe caminhão com a mesma placa, chassi ou renavam PARA ESTE USUÁRIO
            if Caminhao.objects.filter(placa=placa, usuario=request.user).exists():
                messages.error(request, f'Você já cadastrou um caminhão com a placa {placa}.')
                return render(request, 'core/veiculos/caminhoes/form.html', {'form_data': request.POST})
            
            if Caminhao.objects.filter(chassi=chassi, usuario=request.user).exists():
                messages.error(request, f'Você já cadastrou um caminhão com o chassi {chassi}.')
                return render(request, 'core/veiculos/caminhoes/form.html', {'form_data': request.POST})
            
            if Caminhao.objects.filter(renavam=renavam, usuario=request.user).exists():
                messages.error(request, f'Você já cadastrou um caminhão com o renavam {renavam}.')
                return render(request, 'core/veiculos/caminhoes/form.html', {'form_data': request.POST})
            
            # Converter valores monetários do formato brasileiro para float
            valor_compra = converter_para_float(request.POST['valor_compra'])
            valor_residual = converter_para_float(request.POST['valor_residual'])
            capacidade_carga = converter_para_float(request.POST['capacidade_carga'])
            
            caminhao = Caminhao(
                placa=placa,
                marca=request.POST['marca'],
                modelo=request.POST['modelo'],
                ano=int(request.POST['ano']),
                chassi=chassi,
                renavam=renavam,
                valor_compra=valor_compra,
                vida_util=int(request.POST['vida_util']),
                valor_residual=valor_residual,
                capacidade_carga=capacidade_carga,
                usuario=request.user
            )
            
            caminhao.save()
            messages.success(request, 'Caminhão cadastrado com sucesso!')
            return redirect('core:caminhoes')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar caminhão: {str(e)}')
    
    return render(request, 'core/veiculos/caminhoes/form.html')

@login_required
def caminhao_editar(request, id):
    try:
        caminhao = Caminhao.objects.get(id=id, usuario=request.user)
    except Caminhao.DoesNotExist:
        messages.error(request, 'Caminhão não encontrado.')
        return redirect('core:caminhoes')
    
    if request.method == 'POST':
        try:
            # Obter valores do formulário
            placa = request.POST['placa'].upper()
            chassi = request.POST['chassi']
            renavam = request.POST['renavam']
            
            # Verificar se já existe outro caminhão com a mesma placa, chassi ou renavam PARA ESTE USUÁRIO
            if Caminhao.objects.filter(placa=placa, usuario=request.user).exclude(id=id).exists():
                messages.error(request, f'Você já cadastrou outro caminhão com a placa {placa}.')
                return render(request, 'core/veiculos/caminhoes/form.html', {'caminhao': caminhao, 'form_data': request.POST})
            
            if Caminhao.objects.filter(chassi=chassi, usuario=request.user).exclude(id=id).exists():
                messages.error(request, f'Você já cadastrou outro caminhão com o chassi {chassi}.')
                return render(request, 'core/veiculos/caminhoes/form.html', {'caminhao': caminhao, 'form_data': request.POST})
            
            if Caminhao.objects.filter(renavam=renavam, usuario=request.user).exclude(id=id).exists():
                messages.error(request, f'Você já cadastrou outro caminhão com o renavam {renavam}.')
                return render(request, 'core/veiculos/caminhoes/form.html', {'caminhao': caminhao, 'form_data': request.POST})
            
            # Converter valores monetários do formato brasileiro para float
            valor_compra = converter_para_float(request.POST['valor_compra'])
            valor_residual = converter_para_float(request.POST['valor_residual'])
            capacidade_carga = converter_para_float(request.POST['capacidade_carga'])
            
            caminhao.placa = placa
            caminhao.marca = request.POST['marca']
            caminhao.modelo = request.POST['modelo']
            caminhao.ano = int(request.POST['ano'])
            caminhao.chassi = chassi
            caminhao.renavam = renavam
            caminhao.valor_compra = valor_compra
            caminhao.vida_util = int(request.POST['vida_util'])
            caminhao.valor_residual = valor_residual
            caminhao.capacidade_carga = capacidade_carga
            
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