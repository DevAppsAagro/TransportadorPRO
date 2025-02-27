from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.models import Empresa
from django.contrib import messages
from core.utils.supabase_config import upload_file
import uuid
import logging

logger = logging.getLogger(__name__)

@login_required
def empresa(request):
    # Tenta buscar a empresa do usuário logado
    empresa_instance = Empresa.objects.filter(usuario=request.user).first()

    if request.method == 'POST':
        # Processa o upload da logo, se houver
        if 'logo' in request.FILES:
            logo_file = request.FILES['logo']
            
            # Verifica o tamanho do arquivo (máximo 5MB)
            if logo_file.size > 5 * 1024 * 1024:
                messages.error(request, 'O arquivo é muito grande. O tamanho máximo permitido é 5MB.')
                return redirect('core:empresa')
            
            # Verifica o tipo do arquivo
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if logo_file.content_type not in allowed_types:
                messages.error(request, 'Tipo de arquivo não permitido. Use apenas JPEG, PNG ou GIF.')
                return redirect('core:empresa')
            
            try:
                file_extension = logo_file.name.split('.')[-1].lower()
                file_name = f"{uuid.uuid4()}.{file_extension}"
                logo_url = upload_file(logo_file.read(), file_name, content_type=logo_file.content_type)
                
                if logo_url:
                    logger.info(f"Logo uploaded successfully: {logo_url}")
                    if empresa_instance:
                        empresa_instance.logo = logo_url
                    else:
                        empresa_instance = Empresa(usuario=request.user, logo=logo_url)
                else:
                    messages.error(request, 'Erro ao fazer upload da logo. Por favor, tente novamente.')
                    return redirect('core:empresa')
            except Exception as e:
                logger.error(f"Error uploading logo: {str(e)}")
                messages.error(request, 'Ocorreu um erro ao processar o arquivo. Por favor, tente novamente.')
                return redirect('core:empresa')

        # Atualiza ou cria uma nova empresa
        try:
            if empresa_instance:
                # Atualiza os dados da empresa existente
                for field in request.POST:
                    if hasattr(empresa_instance, field) and field != 'logo':
                        setattr(empresa_instance, field, request.POST[field])
                empresa_instance.save()
            else:
                # Cria uma nova empresa associada ao usuário logado
                empresa_instance = Empresa.objects.create(
                    usuario=request.user,
                    razao_social=request.POST['razao_social'],
                    nome_fantasia=request.POST['nome_fantasia'],
                    cnpj=request.POST['cnpj'],
                    inscricao_estadual=request.POST.get('inscricao_estadual', ''),
                    inscricao_municipal=request.POST.get('inscricao_municipal', ''),
                    cep=request.POST['cep'],
                    logradouro=request.POST['endereco'],
                    numero=request.POST['numero'],
                    complemento=request.POST.get('complemento', ''),
                    bairro=request.POST['bairro'],
                    cidade=request.POST['cidade'],
                    estado=request.POST['estado'],
                    telefone=request.POST['telefone'],
                    celular=request.POST.get('celular', ''),
                    email=request.POST['email'],
                    site=request.POST.get('site', ''),
                    rntrc=request.POST.get('rntrc', ''),
                    antt=request.POST.get('antt', ''),
                    observacoes=request.POST.get('observacoes', '')
                )
            messages.success(request, 'Dados da empresa salvos com sucesso!')
        except Exception as e:
            logger.error(f"Error saving company data: {str(e)}")
            messages.error(request, 'Erro ao salvar os dados da empresa. Por favor, tente novamente.')
        
        return redirect('core:empresa')

    # Prepara o contexto para o template
    context = {}
    if empresa_instance:
        context['empresa'] = empresa_instance

    return render(request, 'core/empresa/empresa.html', context)