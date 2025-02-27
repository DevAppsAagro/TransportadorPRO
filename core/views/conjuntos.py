from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models.conjunto import Conjunto
from core.models.caminhao import Caminhao
from core.models.carreta import Carreta
from datetime import datetime

@login_required
def conjuntos(request):
    conjuntos = Conjunto.objects.filter(usuario=request.user)
    return render(request, 'core/veiculos/conjuntos/lista.html', {'conjuntos': conjuntos})

@login_required
def conjunto_novo(request):
    if request.method == 'POST':
        try:
            conjunto = Conjunto(
                data_configuracao=request.POST['data_configuracao'],
                caminhao=get_object_or_404(Caminhao, id=request.POST['caminhao']),
                carreta1=get_object_or_404(Carreta, id=request.POST['carreta1']),
                usuario=request.user
            )
            
            if request.POST.get('carreta2'):
                conjunto.carreta2 = get_object_or_404(Carreta, id=request.POST['carreta2'])
            
            if request.POST.get('carreta3'):
                conjunto.carreta3 = get_object_or_404(Carreta, id=request.POST['carreta3'])
            
            conjunto.save()
            messages.success(request, 'Conjunto cadastrado com sucesso!')
            return redirect('core:conjuntos')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar conjunto: {str(e)}')
    
    caminhoes = Caminhao.objects.filter(usuario=request.user, status='ATIVO')
    carretas = Carreta.objects.filter(usuario=request.user, status='ATIVO')
    return render(request, 'core/veiculos/conjuntos/form.html', {
        'caminhoes': caminhoes,
        'carretas': carretas
    })

@login_required
def conjunto_editar(request, id):
    conjunto = get_object_or_404(Conjunto, id=id, usuario=request.user)
    
    if request.method == 'POST':
        try:
            conjunto.data_configuracao = request.POST['data_configuracao']
            conjunto.caminhao = get_object_or_404(Caminhao, id=request.POST['caminhao'])
            conjunto.carreta1 = get_object_or_404(Carreta, id=request.POST['carreta1'])
            
            if request.POST.get('carreta2'):
                conjunto.carreta2 = get_object_or_404(Carreta, id=request.POST['carreta2'])
            else:
                conjunto.carreta2 = None
            
            if request.POST.get('carreta3'):
                conjunto.carreta3 = get_object_or_404(Carreta, id=request.POST['carreta3'])
            else:
                conjunto.carreta3 = None
            
            conjunto.save()
            messages.success(request, 'Conjunto atualizado com sucesso!')
            return redirect('core:conjuntos')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar conjunto: {str(e)}')
    
    caminhoes = Caminhao.objects.filter(usuario=request.user, status='ATIVO')
    carretas = Carreta.objects.filter(usuario=request.user, status='ATIVO')
    return render(request, 'core/veiculos/conjuntos/form.html', {
        'conjunto': conjunto,
        'caminhoes': caminhoes,
        'carretas': carretas
    })

@login_required
def conjunto_excluir(request, id):
    conjunto = get_object_or_404(Conjunto, id=id, usuario=request.user)
    try:
        conjunto.delete()
        messages.success(request, 'Conjunto excluído com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir conjunto: {str(e)}')
    return redirect('core:conjuntos')