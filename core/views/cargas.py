from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from core.models.carga import Carga

@login_required
def cargas(request):
    cargas = Carga.objects.filter(usuario=request.user)
    return render(request, 'core/cargas/lista.html', {'cargas': cargas})

@login_required
def carga_nova(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        unidade_medida = request.POST.get('unidade_medida')
        fator_multiplicacao = request.POST.get('fator_multiplicacao')
        
        try:
            carga = Carga.objects.create(
                nome=nome,
                unidade_medida=unidade_medida,
                fator_multiplicacao=fator_multiplicacao,
                usuario=request.user
            )
            messages.success(request, 'Carga criada com sucesso!')
            return redirect('core:cargas')
        except Exception as e:
            messages.error(request, f'Erro ao criar carga: {str(e)}')
    
    return render(request, 'core/cargas/form.html')

@login_required
def carga_editar(request, id):
    carga = get_object_or_404(Carga, pk=id, usuario=request.user)
    
    if request.method == 'POST':
        try:
            carga.nome = request.POST.get('nome')
            carga.unidade_medida = request.POST.get('unidade_medida')
            carga.fator_multiplicacao = request.POST.get('fator_multiplicacao')
            carga.save()
            
            messages.success(request, 'Carga atualizada com sucesso!')
            return redirect('core:cargas')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar carga: {str(e)}')
    
    return render(request, 'core/cargas/form.html', {'carga': carga})

@login_required
def carga_excluir(request, id):
    carga = get_object_or_404(Carga, pk=id, usuario=request.user)
    
    try:
        carga.delete()
        messages.success(request, 'Carga excluída com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir carga: {str(e)}')
    
    return redirect('core:cargas')