from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from core.models.carreta import Carreta

@login_required
def lista_carretas(request):
    carretas = Carreta.objects.filter(usuario=request.user)
    return render(request, 'core/veiculos/carretas/lista.html', {'carretas': carretas})

@login_required
def criar_carreta(request):
    if request.method == 'POST':
        try:
            carreta = Carreta(
                usuario=request.user,
                placa=request.POST['placa'],
                marca=request.POST['marca'],
                modelo=request.POST['modelo'],
                ano=request.POST['ano'],
                chassi=request.POST['chassi'],
                renavam=request.POST['renavam'],
                valor_compra=request.POST['valor_compra'],
                vida_util=request.POST['vida_util'],
                valor_residual=request.POST['valor_residual'],
                capacidade_carga=request.POST['capacidade_carga'],
                quilometragem=request.POST.get('quilometragem', 0)
            )
            carreta.save()
            messages.success(request, 'Carreta cadastrada com sucesso!')
            return redirect('core:carretas')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar carreta: {str(e)}')
    return render(request, 'core/veiculos/carretas/form.html')

@login_required
def editar_carreta(request, id):
    carreta = get_object_or_404(Carreta, id=id, usuario=request.user)
    if request.method == 'POST':
        try:
            carreta.placa = request.POST['placa']
            carreta.marca = request.POST['marca']
            carreta.modelo = request.POST['modelo']
            carreta.ano = request.POST['ano']
            carreta.chassi = request.POST['chassi']
            carreta.renavam = request.POST['renavam']
            carreta.valor_compra = request.POST['valor_compra']
            carreta.vida_util = request.POST['vida_util']
            carreta.valor_residual = request.POST['valor_residual']
            carreta.capacidade_carga = request.POST['capacidade_carga']
            carreta.quilometragem = request.POST.get('quilometragem', carreta.quilometragem)
            carreta.save()
            messages.success(request, 'Carreta atualizada com sucesso!')
            return redirect('core:carretas')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar carreta: {str(e)}')
    return render(request, 'core/veiculos/carretas/form.html', {'carreta': carreta})

@login_required
def excluir_carreta(request, id):
    carreta = get_object_or_404(Carreta, id=id, usuario=request.user)
    try:
        carreta.delete()
        messages.success(request, 'Carreta excluída com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir carreta: {str(e)}')
    return redirect('core:carretas')