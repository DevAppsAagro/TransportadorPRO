from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models.empresa import Empresa
from django.forms import ModelForm
from core.utils.supabase_config import upload_file
import uuid
import logging

logger = logging.getLogger(__name__)

class EmpresaForm(ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'razao_social', 'nome_fantasia', 'cnpj', 'inscricao_estadual', 'inscricao_municipal',
            'company_type',  # Adicionado campo de tipo de empresa para integração com sistema de cobranças
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado',
            'telefone', 'celular', 'email', 'site', 'rntrc', 'antt', 'observacoes'
        ]

@login_required
def configuracoes_empresa(request):
    # Verifica se já existe uma empresa cadastrada para o usuário
    empresa = Empresa.objects.filter(usuario=request.user).first()
    
    if request.method == 'POST':
        # Processa o upload da logo, se houver
        logo_url = None
        if 'logo' in request.FILES:
            logo_file = request.FILES['logo']
            
            # Verifica o tamanho do arquivo (máximo 5MB)
            if logo_file.size > 5 * 1024 * 1024:
                messages.error(request, 'O arquivo é muito grande. O tamanho máximo permitido é 5MB.')
                return redirect('core:configuracoes_empresa')
            
            # Verifica o tipo do arquivo
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if logo_file.content_type not in allowed_types:
                messages.error(request, 'Tipo de arquivo não permitido. Use apenas JPEG, PNG ou GIF.')
                return redirect('core:configuracoes_empresa')
            
            try:
                # Gera um nome único para o arquivo
                file_extension = logo_file.name.split('.')[-1].lower()
                file_name = f"logo_{request.user.id}_{uuid.uuid4()}.{file_extension}"
                
                # Obtém o token de autenticação do usuário atual, se disponível
                auth_token = getattr(request, 'auth_token', None)
                
                # Faz o upload para o Supabase
                logo_url = upload_file(
                    file_data=logo_file.read(),
                    file_name=file_name,
                    auth_token=auth_token,
                    content_type=logo_file.content_type
                )
                
                if not logo_url:
                    messages.error(request, 'Erro ao fazer upload da logo. Por favor, tente novamente.')
                    return redirect('core:configuracoes_empresa')
                
                logger.info(f"Logo uploaded successfully: {logo_url}")
            except Exception as e:
                logger.error(f"Error uploading logo: {str(e)}")
                messages.error(request, 'Ocorreu um erro ao processar o arquivo. Por favor, tente novamente.')
                return redirect('core:configuracoes_empresa')
        
        # Processa o formulário
        if empresa:
            # Atualiza a empresa existente
            form = EmpresaForm(request.POST, instance=empresa)
        else:
            # Cria uma nova empresa
            form = EmpresaForm(request.POST)
        
        if form.is_valid():
            empresa_obj = form.save(commit=False)
            empresa_obj.usuario = request.user
            
            # Atualiza a URL da logo, se foi feito upload
            if logo_url:
                empresa_obj.logo = logo_url
                
            empresa_obj.save()
            messages.success(request, 'Configurações da empresa salvas com sucesso!')
            return redirect('core:configuracoes_empresa')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erro no campo {field}: {error}")
    else:
        if empresa:
            # Exibe o formulário com os dados da empresa existente
            form = EmpresaForm(instance=empresa)
        else:
            # Exibe o formulário vazio
            form = EmpresaForm()
    
    return render(request, 'core/empresa/form.html', {
        'form': form,
        'empresa': empresa
    })
