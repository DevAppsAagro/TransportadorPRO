import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction

from ..models import PerfilUsuario, Caminhao


def is_admin(user):
    """Verifica se o usuário é administrador"""
    try:
        # Verificar primeiro se o usuário está autenticado
        if not user.is_authenticated:
            return False
            
        # Verificações alternativas para determinar se é admin
        if user.is_superuser or user.is_staff:
            return True
            
        # Verificar se o perfil existe e se é admin
        if hasattr(user, 'perfil'):
            return user.perfil.is_admin
        
        return False
    except Exception as e:
        # Log do erro para depuração
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao verificar permissões de administrador para {user}: {str(e)}")
        return False


@login_required
@user_passes_test(is_admin)
def listar_motoristas(request):
    """Lista todos os motoristas cadastrados"""
    # Filtrar apenas os motoristas criados pelo usuário logado ou, se não houver criador especificado
    motoristas = User.objects.filter(
        perfil__tipo_usuario='MOTORISTA'
    ).filter(
        perfil__criado_por=request.user
    )
    
    return render(request, 'core/motoristas/lista.html', {
        'motoristas': motoristas
    })


@login_required
@user_passes_test(is_admin)
def detalhe_motorista(request, pk):
    """Exibe os detalhes de um motorista"""
    motorista = get_object_or_404(
        User, 
        pk=pk, 
        perfil__tipo_usuario='MOTORISTA',
        perfil__criado_por=request.user
    )
    
    from datetime import date
    context = {
        'motorista': motorista,
        'today': date.today()
    }
    
    return render(request, 'core/motoristas/detalhe.html', context)


@login_required
@user_passes_test(is_admin)
def criar_motorista(request):
    """Cria um novo motorista"""
    caminhoes = Caminhao.objects.filter(usuario=request.user)
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        sobrenome = request.POST.get('sobrenome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        cnh = request.POST.get('cnh')
        categoria_cnh = request.POST.get('categoria_cnh')
        validade_cnh = request.POST.get('validade_cnh') or None
        caminhao_id = request.POST.get('caminhao') or None
        
        # Verificar se já existe um usuário com esse email
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Já existe um usuário com esse email!')
            return render(request, 'core/motoristas/form.html', {
                'caminhoes': caminhoes
            })
        
        # Gerar uma senha aleatória
        senha = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        try:
            with transaction.atomic():
                # Criar usuário
                username = email.split('@')[0]
                # Verificar se já existe um usuário com esse username e adicionar números se necessário
                base_username = username
                count = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{count}"
                    count += 1
                
                usuario = User.objects.create_user(
                    username=username,
                    email=email,
                    password=senha,
                    first_name=nome,
                    last_name=sobrenome
                )
                
                # Criar perfil para o motorista
                perfil = PerfilUsuario.objects.create(
                    usuario=usuario,
                    tipo_usuario='MOTORISTA',
                    telefone=telefone,
                    criado_por=request.user,
                    cnh=cnh,
                    categoria_cnh=categoria_cnh,
                    validade_cnh=validade_cnh
                )
                
                # Associar ao caminhão se fornecido
                if caminhao_id:
                    caminhao = get_object_or_404(Caminhao, id=caminhao_id, usuario=request.user)
                    perfil.caminhao_atual = caminhao
                    perfil.save()
                
                # Enviar email com as credenciais
                try:
                    assunto = 'Acesso ao sistema TransportadorPRO - Área de Motoristas'
                    mensagem = f"""
                    Olá {nome},
                    
                    Seu acesso ao sistema TransportadorPRO foi criado com sucesso!
                    
                    Para acessar o sistema, utilize os seguintes dados:
                    
                    URL: https://motorista.transportadorpro.com
                    Usuário: {username}
                    Senha: {senha}
                    
                    Recomendamos que você altere sua senha após o primeiro acesso.
                    
                    Atenciosamente,
                    Equipe TransportadorPRO
                    """
                    
                    from_email = settings.DEFAULT_FROM_EMAIL
                    recipient_list = [email]
                    
                    send_mail(assunto, mensagem, from_email, recipient_list, fail_silently=True)
                    
                    # Exibir mensagem de sucesso com as credenciais
                    messages.success(request, f'<strong>Motorista criado com sucesso!</strong><br>Credenciais:<br>Usuário: <strong>{username}</strong><br>Senha: <strong>{senha}</strong>')
                except Exception as email_error:
                    # Log do erro de email mas não impede a criação do motorista
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Erro ao enviar email para {email}: {str(email_error)}")
                    
                    # Exibir mensagem de sucesso com as credenciais
                    messages.success(request, f'<strong>Motorista criado com sucesso!</strong><br>Credenciais:<br>Usuário: <strong>{username}</strong><br>Senha: <strong>{senha}</strong>')
                
                return redirect('core:listar_motoristas')
                
        except Exception as e:
            messages.error(request, f'Erro ao criar motorista: {str(e)}')
    
    return render(request, 'core/motoristas/form.html', {
        'caminhoes': caminhoes
    })


@login_required
@user_passes_test(is_admin)
def editar_motorista(request, pk):
    """Edita os dados de um motorista"""
    # Buscar motorista verificando que pertence ao usuário logado
    motorista = get_object_or_404(
        User, 
        pk=pk, 
        perfil__tipo_usuario='MOTORISTA',
        perfil__criado_por=request.user
    )
    caminhoes = Caminhao.objects.filter(usuario=request.user)
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        sobrenome = request.POST.get('sobrenome')
        telefone = request.POST.get('telefone')
        cnh = request.POST.get('cnh')
        categoria_cnh = request.POST.get('categoria_cnh')
        validade_cnh = request.POST.get('validade_cnh') or None
        caminhao_id = request.POST.get('caminhao') or None
        ativo = request.POST.get('ativo') == 'on'
        
        try:
            with transaction.atomic():
                # Atualizar usuário
                motorista.first_name = nome
                motorista.last_name = sobrenome
                motorista.save()
                
                # Atualizar perfil
                perfil = motorista.perfil
                perfil.telefone = telefone
                perfil.cnh = cnh
                perfil.categoria_cnh = categoria_cnh
                perfil.validade_cnh = validade_cnh
                perfil.ativo = ativo
                
                # Associar ao caminhão se fornecido
                if caminhao_id:
                    caminhao = get_object_or_404(Caminhao, id=caminhao_id, usuario=request.user)
                    perfil.caminhao_atual = caminhao
                else:
                    perfil.caminhao_atual = None
                
                perfil.save()
                
                messages.success(request, 'Motorista atualizado com sucesso!')
                return redirect('core:listar_motoristas')
                
        except Exception as e:
            messages.error(request, f'Erro ao atualizar motorista: {str(e)}')
    
    return render(request, 'core/motoristas/form.html', {
        'motorista': motorista,
        'caminhoes': caminhoes
    })


@login_required
@user_passes_test(is_admin)
def resetar_senha_motorista(request, pk):
    """Reseta a senha de um motorista e envia por email"""
    motorista = get_object_or_404(User, pk=pk, perfil__tipo_usuario='MOTORISTA')
    
    if request.method == 'POST':
        try:
            # Gerar uma senha aleatória
            senha = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            # Atualizar a senha
            motorista.set_password(senha)
            motorista.save()
            
            # Enviar email com a nova senha
            assunto = 'Nova senha para o sistema TransportadorPRO'
            mensagem = f"""
            Olá {motorista.first_name},
            
            Sua senha foi redefinida com sucesso!
            
            Para acessar o sistema, utilize os seguintes dados:
            
            URL: https://motorista.transportadorpro.com
            Usuário: {motorista.username}
            Nova Senha: {senha}
            
            Recomendamos que você altere sua senha após o primeiro acesso.
            
            Atenciosamente,
            Equipe TransportadorPRO
            """
            
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [motorista.email]
            
            send_mail(assunto, mensagem, from_email, recipient_list, fail_silently=False)
            
            messages.success(request, f'Senha resetada com sucesso! A nova senha foi enviada para {motorista.email}')
            
        except Exception as e:
            messages.error(request, f'Erro ao resetar senha: {str(e)}')
    
    return redirect('core:detalhe_motorista', pk=pk)


@login_required
@user_passes_test(is_admin)
def excluir_motorista(request, pk):
    """Exclui um motorista"""
    motorista = get_object_or_404(
        User, 
        pk=pk, 
        perfil__tipo_usuario='MOTORISTA',
        perfil__criado_por=request.user
    )
    
    if request.method == 'POST':
        try:
            motorista.delete()
            messages.success(request, 'Motorista excluído com sucesso!')
            return redirect('core:listar_motoristas')
        except Exception as e:
            messages.error(request, f'Erro ao excluir motorista: {str(e)}')
    
    return render(request, 'core/motoristas/confirmar_exclusao.html', {
        'motorista': motorista
    })
