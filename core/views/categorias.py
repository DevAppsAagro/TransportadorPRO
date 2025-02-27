from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ..models.categoria import Categoria
from ..models.subcategoria import Subcategoria

@login_required
def categorias(request):
    categorias = Categoria.objects.filter(Q(usuario=request.user) | Q(usuario__isnull=True))
    return render(request, 'core/categorias/categorias.html', {'categorias': categorias})

@login_required
def categoria_nova(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        tipo = request.POST.get('tipo')
        alocacao = request.POST.get('alocacao')
        
        categoria = Categoria.objects.create(
            nome=nome,
            tipo=tipo,
            alocacao=alocacao,
            usuario=request.user
        )
        
        messages.success(request, 'Categoria criada com sucesso!')
        return redirect('core:categorias')
    
    return render(request, 'core/categorias/categoria_form.html')

@login_required
def categoria_editar(request, id):
    categoria = get_object_or_404(Categoria, pk=id)
    
    if request.method == 'POST':
        categoria.nome = request.POST.get('nome')
        categoria.tipo = request.POST.get('tipo')
        categoria.alocacao = request.POST.get('alocacao')
        categoria.save()
        
        messages.success(request, 'Categoria atualizada com sucesso!')
        return redirect('core:categorias')
    
    return render(request, 'core/categorias/categoria_form.html', {'categoria': categoria})

@login_required
def categoria_excluir(request, id):
    categoria = get_object_or_404(Categoria, pk=id)
    categoria.delete()
    messages.success(request, 'Categoria excluída com sucesso!')
    return redirect('core:categorias')

@login_required
def subcategorias(request):
    subcategorias = Subcategoria.objects.filter(Q(categoria__usuario=request.user) | Q(categoria__usuario__isnull=True))
    return render(request, 'core/categorias/subcategorias.html', {'subcategorias': subcategorias})

@login_required
def subcategoria_nova(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        categoria_id = request.POST.get('categoria')
        categoria = get_object_or_404(Categoria, pk=categoria_id)
        
        subcategoria = Subcategoria.objects.create(
            nome=nome,
            categoria=categoria
        )
        
        messages.success(request, 'Subcategoria criada com sucesso!')
        return redirect('core:subcategorias')
    
    categorias = Categoria.objects.filter(Q(usuario=request.user) | Q(usuario__isnull=True))
    return render(request, 'core/categorias/subcategoria_form.html', {'categorias': categorias})

@login_required
def subcategoria_editar(request, id):
    subcategoria = get_object_or_404(Subcategoria, pk=id)
    
    if request.method == 'POST':
        subcategoria.nome = request.POST.get('nome')
        categoria_id = request.POST.get('categoria')
        subcategoria.categoria = get_object_or_404(Categoria, pk=categoria_id)
        subcategoria.save()
        
        messages.success(request, 'Subcategoria atualizada com sucesso!')
        return redirect('core:subcategorias')
    
    categorias = Categoria.objects.filter(Q(usuario=request.user) | Q(usuario__isnull=True))
    return render(request, 'core/categorias/subcategoria_form.html', {
        'subcategoria': subcategoria,
        'categorias': categorias
    })

@login_required
def subcategoria_excluir(request, id):
    subcategoria = get_object_or_404(Subcategoria, pk=id)
    subcategoria.delete()
    messages.success(request, 'Subcategoria excluída com sucesso!')
    return redirect('core:subcategorias')