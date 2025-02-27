from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models.empresa import Empresa
from django.forms import ModelForm

class EmpresaForm(ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'razao_social', 'nome_fantasia', 'cnpj', 'inscricao_estadual', 'inscricao_municipal',
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado',
            'telefone', 'celular', 'email', 'site', 'rntrc', 'antt', 'observacoes'
        ]

@login_required
def configuracoes_empresa(request):
    # Verifica se já existe uma empresa cadastrada para o usuário
    empresa = Empresa.objects.filter(usuario=request.user).first()
    
    if request.method == 'POST':
        if empresa:
            # Atualiza a empresa existente
            form = EmpresaForm(request.POST, instance=empresa)
        else:
            # Cria uma nova empresa
            form = EmpresaForm(request.POST)
        
        if form.is_valid():
            empresa_obj = form.save(commit=False)
            empresa_obj.usuario = request.user
            empresa_obj.save()
            messages.success(request, 'Configurações da empresa salvas com sucesso!')
            return redirect('core:configuracoes_empresa')
    else:
        if empresa:
            # Exibe o formulário com os dados da empresa existente
            form = EmpresaForm(instance=empresa)
        else:
            # Exibe o formulário vazio
            form = EmpresaForm()
    
    return render(request, 'core/configuracoes/empresa.html', {
        'form': form,
        'empresa': empresa
    })
