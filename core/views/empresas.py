from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import Empresa
from core.utils.supabase_config import upload_file
import uuid
import logging

logger = logging.getLogger(__name__)

@login_required
def empresas_list(request):
    """Lista todas as empresas cadastradas"""
    empresas = Empresa.objects.all().order_by('razao_social')
    return render(request, 'core/empresa/lista.html', {'empresas': empresas})

@login_required
def empresa_create(request):
    """Cria uma nova empresa"""
    if request.method == 'POST':
        try:
            # Processa o upload da logo, se houver
            logo_url = None
            if 'logo' in request.FILES:
                logo_file = request.FILES['logo']
                
                # Verifica o tamanho do arquivo (máximo 5MB)
                if logo_file.size > 5 * 1024 * 1024:
                    messages.error(request, 'O arquivo é muito grande. O tamanho máximo permitido é 5MB.')
                    return redirect('core:empresa_create')
                
                # Verifica o tipo do arquivo
                allowed_types = ['image/jpeg', 'image/png', 'image/gif']
                if logo_file.content_type not in allowed_types:
                    messages.error(request, 'Tipo de arquivo não permitido. Use apenas JPEG, PNG ou GIF.')
                    return redirect('core:empresa_create')
                
                try:
                    file_extension = logo_file.name.split('.')[-1].lower()
                    file_name = f"{uuid.uuid4()}.{file_extension}"
                    logo_url = upload_file(logo_file.read(), file_name, content_type=logo_file.content_type)
                    
                    if not logo_url:
                        messages.error(request, 'Erro ao fazer upload da logo. Por favor, tente novamente.')
                        return redirect('core:empresa_create')
                except Exception as e:
                    logger.error(f"Error uploading logo: {str(e)}")
                    messages.error(request, 'Ocorreu um erro ao processar o arquivo. Por favor, tente novamente.')
                    return redirect('core:empresa_create')
            
            # Cria a nova empresa
            empresa = Empresa(
                usuario=request.user,
                razao_social=request.POST['razao_social'],
                nome_fantasia=request.POST.get('nome_fantasia', ''),
                logo=logo_url,
                cnpj=request.POST['cnpj'],
                inscricao_estadual=request.POST.get('inscricao_estadual', ''),
                inscricao_municipal=request.POST.get('inscricao_municipal', ''),
                cep=request.POST['cep'],
                logradouro=request.POST['logradouro'],
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
            empresa.save()
            
            messages.success(request, 'Empresa criada com sucesso!')
            return redirect('core:empresas_list')
        except Exception as e:
            logger.error(f"Error creating company: {str(e)}")
            messages.error(request, f'Erro ao criar empresa: {str(e)}')
    
    return render(request, 'core/empresa/form.html')

@login_required
def empresa_edit(request, pk):
    """Edita uma empresa existente"""
    empresa = get_object_or_404(Empresa, pk=pk)
    
    if request.method == 'POST':
        try:
            # Processa o upload da logo, se houver
            if 'logo' in request.FILES:
                logo_file = request.FILES['logo']
                
                # Verifica o tamanho do arquivo (máximo 5MB)
                if logo_file.size > 5 * 1024 * 1024:
                    messages.error(request, 'O arquivo é muito grande. O tamanho máximo permitido é 5MB.')
                    return redirect('core:empresa_edit', pk=pk)
                
                # Verifica o tipo do arquivo
                allowed_types = ['image/jpeg', 'image/png', 'image/gif']
                if logo_file.content_type not in allowed_types:
                    messages.error(request, 'Tipo de arquivo não permitido. Use apenas JPEG, PNG ou GIF.')
                    return redirect('core:empresa_edit', pk=pk)
                
                try:
                    file_extension = logo_file.name.split('.')[-1].lower()
                    file_name = f"{uuid.uuid4()}.{file_extension}"
                    logo_url = upload_file(logo_file.read(), file_name, content_type=logo_file.content_type)
                    
                    if logo_url:
                        empresa.logo = logo_url
                    else:
                        messages.error(request, 'Erro ao fazer upload da logo. Por favor, tente novamente.')
                        return redirect('core:empresa_edit', pk=pk)
                except Exception as e:
                    logger.error(f"Error uploading logo: {str(e)}")
                    messages.error(request, 'Ocorreu um erro ao processar o arquivo. Por favor, tente novamente.')
                    return redirect('core:empresa_edit', pk=pk)
            
            # Atualiza os dados da empresa
            empresa.razao_social = request.POST['razao_social']
            empresa.nome_fantasia = request.POST.get('nome_fantasia', '')
            empresa.cnpj = request.POST['cnpj']
            empresa.inscricao_estadual = request.POST.get('inscricao_estadual', '')
            empresa.inscricao_municipal = request.POST.get('inscricao_municipal', '')
            empresa.cep = request.POST['cep']
            empresa.logradouro = request.POST['logradouro']
            empresa.numero = request.POST['numero']
            empresa.complemento = request.POST.get('complemento', '')
            empresa.bairro = request.POST['bairro']
            empresa.cidade = request.POST['cidade']
            empresa.estado = request.POST['estado']
            empresa.telefone = request.POST['telefone']
            empresa.celular = request.POST.get('celular', '')
            empresa.email = request.POST['email']
            empresa.site = request.POST.get('site', '')
            empresa.rntrc = request.POST.get('rntrc', '')
            empresa.antt = request.POST.get('antt', '')
            empresa.observacoes = request.POST.get('observacoes', '')
            
            empresa.save()
            
            messages.success(request, 'Empresa atualizada com sucesso!')
            return redirect('core:empresas_list')
        except Exception as e:
            logger.error(f"Error updating company: {str(e)}")
            messages.error(request, f'Erro ao atualizar empresa: {str(e)}')
    
    return render(request, 'core/empresa/form.html', {'empresa': empresa})

@login_required
def empresa_delete(request, pk):
    """Exclui uma empresa"""
    empresa = get_object_or_404(Empresa, pk=pk)
    
    if request.method == 'POST':
        try:
            empresa.delete()
            messages.success(request, 'Empresa excluída com sucesso!')
        except Exception as e:
            logger.error(f"Error deleting company: {str(e)}")
            messages.error(request, f'Erro ao excluir empresa: {str(e)}')
        
        return redirect('core:empresas_list')
    
    return render(request, 'core/empresa/confirm_delete.html', {'empresa': empresa})

@login_required
def empresa_detail(request, pk):
    """Exibe os detalhes de uma empresa"""
    empresa = get_object_or_404(Empresa, pk=pk)
    return render(request, 'core/empresa/detail.html', {'empresa': empresa})
