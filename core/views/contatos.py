from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models.contato import Contato
from django.db.models import Count, Q

@login_required
def contatos(request):
    contatos = Contato.objects.filter(usuario=request.user).order_by('nome_completo')
    
    # Calcular estatísticas dos contatos
    total_contatos = contatos.count()
    total_clientes = contatos.filter(tipo='CLIENTE').count()
    total_fornecedores = contatos.filter(tipo='FORNECEDOR').count()
    total_funcionarios_motoristas = contatos.filter(
        Q(tipo='FUNCIONARIO') | Q(tipo='MOTORISTA')
    ).count()
    
    context = {
        'contatos': contatos,
        'total_contatos': total_contatos,
        'total_clientes': total_clientes,
        'total_fornecedores': total_fornecedores,
        'total_funcionarios_motoristas': total_funcionarios_motoristas,
    }
    
    return render(request, 'core/contatos/contatos.html', context)

@login_required
def contato_novo(request):
    if request.method == 'POST':
        # Validar campos obrigatórios
        campos_obrigatorios = ['nome_completo', 'tipo', 'cpf_cnpj', 'email', 'telefone']
        
        # Verificar tipo de contato - para clientes, todos os campos são obrigatórios
        tipo = request.POST.get('tipo')
        
        # Se for cliente, validar todos os campos obrigatórios para integração com Asaas
        if tipo == 'CLIENTE':
            for campo in campos_obrigatorios:
                if not request.POST.get(campo):
                    messages.error(request, f'O campo {campo.replace("_", " ").title()} é obrigatório para clientes.')
                    return render(request, 'core/contatos/contato_form.html', {'contato': request.POST})
                    
            # Validar formato do CPF/CNPJ
            cpf_cnpj = request.POST.get('cpf_cnpj', '').strip()
            if len(cpf_cnpj) not in [11, 14, 18]:  # 11 (CPF sem formatação), 14 (CNPJ sem formatação) ou 18 (formatado)
                messages.error(request, 'CPF/CNPJ inválido. Informe um CPF ou CNPJ válido.')
                return render(request, 'core/contatos/contato_form.html', {'contato': request.POST})
        else:
            # Para outros tipos, apenas nome e tipo são obrigatórios
            for campo in ['nome_completo', 'tipo']:
                if not request.POST.get(campo):
                    messages.error(request, f'O campo {campo.replace("_", " ").title()} é obrigatório.')
                    return render(request, 'core/contatos/contato_form.html', {'contato': request.POST})
        
        try:
            # Criar novo contato
            contato = Contato.objects.create(
                usuario=request.user,
                nome_completo=request.POST['nome_completo'].strip(),
                tipo=request.POST['tipo'],
                cpf_cnpj=request.POST.get('cpf_cnpj', '').strip(),
                email=request.POST.get('email', '').strip(),
                telefone=request.POST.get('telefone', '').strip(),
                cep=request.POST.get('cep', '').strip(),
                logradouro=request.POST.get('logradouro', '').strip(),
                numero=request.POST.get('numero', '').strip(),
                complemento=request.POST.get('complemento', '').strip(),
                bairro=request.POST.get('bairro', '').strip(),
                cidade=request.POST.get('cidade', '').strip(),
                estado=request.POST.get('estado', '')
            )
            messages.success(request, 'Contato criado com sucesso!')
            return redirect('core:contatos')
        except Exception as e:
            messages.error(request, f'Erro ao criar contato: {str(e)}')
            return render(request, 'core/contatos/contato_form.html', {'contato': request.POST})
    
    return render(request, 'core/contatos/contato_form.html')


@login_required
def contato_editar(request, pk):
    contato = Contato.objects.filter(usuario=request.user, pk=pk).first()
    if not contato:
        messages.error(request, 'Contato não encontrado.')
        return redirect('core:contatos')
    
    if request.method == 'POST':
        # Validar campos obrigatórios
        campos_obrigatorios = ['nome_completo', 'tipo', 'cpf_cnpj', 'email', 'telefone']
        
        # Verificar tipo de contato
        tipo = request.POST.get('tipo')
        
        # Se for cliente, validar todos os campos obrigatórios para integração com Asaas
        if tipo == 'CLIENTE':
            for campo in campos_obrigatorios:
                if not request.POST.get(campo):
                    messages.error(request, f'O campo {campo.replace("_", " ").title()} é obrigatório para clientes.')
                    # Manter os dados enviados no formulário
                    dados_form = {}
                    for field in request.POST:
                        dados_form[field] = request.POST[field]
                    return render(request, 'core/contatos/contato_form.html', {'contato': dados_form})
                    
            # Validar formato do CPF/CNPJ
            cpf_cnpj = request.POST.get('cpf_cnpj', '').strip()
            if len(cpf_cnpj) not in [11, 14, 18]:  # 11 (CPF sem formatação), 14 (CNPJ sem formatação) ou 18 (formatado)
                messages.error(request, 'CPF/CNPJ inválido. Informe um CPF ou CNPJ válido.')
                dados_form = {}
                for field in request.POST:
                    dados_form[field] = request.POST[field]
                return render(request, 'core/contatos/contato_form.html', {'contato': dados_form})
        
        try:
            # Atualizar campos do contato
            for field in request.POST:
                if hasattr(contato, field):
                    setattr(contato, field, request.POST[field])
            contato.save()
            messages.success(request, 'Contato atualizado com sucesso!')
            return redirect('core:contatos')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar contato: {str(e)}')
    
    return render(request, 'core/contatos/contato_form.html', {'contato': contato})

@login_required
def contato_excluir(request, pk):
    contato = Contato.objects.filter(usuario=request.user, pk=pk).first()
    if not contato:
        messages.error(request, 'Contato não encontrado.')
    else:
        try:
            contato.delete()
            messages.success(request, 'Contato excluído com sucesso!')
        except Exception as e:
            messages.error(request, 'Erro ao excluir contato. Por favor, tente novamente.')
    return redirect('core:contatos')