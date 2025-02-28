from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db import transaction
from django.utils import timezone

from ..models import AbastecimentoPendente, Caminhao, Contato

# Constantes
COMBUSTIVEL_CHOICES = [
    ('GASOLINA', 'Gasolina'),
    ('DIESEL', 'Diesel'),
    ('ETANOL', 'Etanol'),
    ('FLEX', 'Flex')
]

def is_motorista(user):
    """Verifica se o usuário é motorista"""
    try:
        return user.is_authenticated and user.perfil.tipo_usuario == 'MOTORISTA'
    except:
        return False


def motorista_required(view_func):
    """Decorator para verificar se o usuário é motorista e redirecionar para login se necessário"""
    decorated_view = user_passes_test(is_motorista, login_url='motorista:login')(view_func)
    return decorated_view


def motorista_login(request):
    """View de login para o subdomínio de motoristas"""
    # Redirecionar para o dashboard se já estiver logado como motorista
    if is_motorista(request.user):
        return redirect('motorista:dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None and is_motorista(user):
                login(request, user)
                
                # Atualizar último acesso
                if hasattr(user, 'perfil'):
                    user.perfil.ultimo_acesso = timezone.now()
                    user.perfil.save()
                
                messages.success(request, f'Bem-vindo, {user.first_name}!')
                return redirect('motorista:dashboard')
            else:
                messages.error(request, 'Acesso negado. Esta área é restrita para motoristas.')
        else:
            messages.error(request, 'Usuário ou senha inválidos!')
    
    return render(request, 'motorista/login.html')


def motorista_logout(request):
    """Logout de motorista"""
    logout(request)
    messages.success(request, 'Logout realizado com sucesso!')
    return redirect('motorista:login')


@login_required
@motorista_required
def motorista_dashboard(request):
    """Dashboard do motorista"""
    motorista = request.user
    
    # Buscar abastecimentos pendentes
    abastecimentos_pendentes = AbastecimentoPendente.objects.filter(motorista=motorista).order_by('-data_solicitacao')
    
    # Buscar caminhão atual do motorista
    try:
        caminhao_atual = motorista.perfil.caminhao_atual
    except:
        caminhao_atual = None
    
    return render(request, 'motorista/dashboard.html', {
        'motorista': motorista,
        'abastecimentos_pendentes': abastecimentos_pendentes[:5],
        'caminhao_atual': caminhao_atual
    })


@login_required
@motorista_required
def listar_abastecimentos_pendentes(request):
    """Lista todos os abastecimentos pendentes do motorista"""
    motorista = request.user
    
    # Filtrar por status se especificado
    status = request.GET.get('status')
    if status and status in ['PENDENTE', 'APROVADO', 'REJEITADO']:
        abastecimentos = AbastecimentoPendente.objects.filter(motorista=motorista, status=status).order_by('-data_solicitacao')
    else:
        abastecimentos = AbastecimentoPendente.objects.filter(motorista=motorista).order_by('-data_solicitacao')
    
    return render(request, 'motorista/abastecimentos/lista.html', {
        'abastecimentos': abastecimentos
    })


@login_required
@motorista_required
def detalhe_abastecimento_pendente(request, pk):
    """Exibe os detalhes de um abastecimento pendente"""
    abastecimento = get_object_or_404(AbastecimentoPendente, pk=pk, motorista=request.user)
    
    return render(request, 'motorista/abastecimentos/detalhe.html', {
        'abastecimento': abastecimento
    })


@login_required
@motorista_required
def criar_abastecimento_pendente(request):
    """Permite que o motorista crie um novo pedido de abastecimento"""
    motorista = request.user
    
    # Formulário foi enviado
    if request.method == 'POST':
        try:
            # Extrair dados do formulário
            data = request.POST.get('data')
            id_posto = request.POST.get('posto')
            combustivel = request.POST.get('combustivel')
            litros = request.POST.get('litros')
            valor_litro = request.POST.get('valor_litro')
            valor_total = request.POST.get('valor_total')
            km_atual = request.POST.get('km_atual')
            observacao = request.POST.get('observacao')
            
            # Validações básicas
            if not data or not id_posto or not combustivel or not litros or not valor_litro or not valor_total or not km_atual:
                messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos!')
                return redirect('motorista:criar_abastecimento_pendente')
            
            # Buscar objetos relacionados
            posto = get_object_or_404(Contato, id=id_posto, tipo='POSTO')
            
            # Identificar caminhão atual do motorista
            if hasattr(motorista, 'perfil') and motorista.perfil.caminhao_atual:
                caminhao = motorista.perfil.caminhao_atual
            else:
                messages.error(request, 'Você não possui um caminhão associado ao seu perfil!')
                return redirect('motorista:criar_abastecimento_pendente')
            
            # Criar o abastecimento pendente
            abastecimento = AbastecimentoPendente.objects.create(
                motorista=motorista,
                caminhao=caminhao,
                posto=posto,
                data=data,
                combustivel=combustivel,
                litros=litros,
                valor_litro=valor_litro,
                valor_total=valor_total,
                km_atual=km_atual,
                observacao=observacao
            )
            
            # Processar upload de comprovante se enviado
            if 'comprovante' in request.FILES:
                abastecimento.comprovante = request.FILES['comprovante']
                abastecimento.save()
            
            messages.success(request, 'Solicitação de abastecimento criada com sucesso!')
            return redirect('motorista:listar_abastecimentos_pendentes')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar solicitação: {str(e)}')
    
    # Carregar formulário
    postos = Contato.objects.filter(tipo='POSTO')
    
    return render(request, 'motorista/abastecimentos/novo.html', {
        'postos': postos,
        'combustiveis': COMBUSTIVEL_CHOICES
    })


@login_required
@motorista_required
def perfil_motorista(request):
    """Exibe informações do perfil do motorista"""
    return render(request, 'motorista/perfil.html', {
        'now': timezone.now(),
    })


@login_required
@motorista_required
def alterar_senha(request):
    """Permite ao motorista alterar sua senha"""
    if request.method == 'POST':
        # Lógica para alterar a senha
        senha_atual = request.POST.get('senha_atual')
        nova_senha = request.POST.get('nova_senha')
        confirmar_senha = request.POST.get('confirmar_senha')
        
        if not request.user.check_password(senha_atual):
            messages.error(request, 'Senha atual incorreta!')
            return redirect('motorista:alterar_senha')
        
        if nova_senha != confirmar_senha:
            messages.error(request, 'As senhas não conferem!')
            return redirect('motorista:alterar_senha')
        
        request.user.set_password(nova_senha)
        request.user.save()
        
        # Fazer login novamente com a nova senha
        user = authenticate(username=request.user.username, password=nova_senha)
        if user:
            login(request, user)
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('motorista:perfil')
    
    return render(request, 'motorista/alterar_senha.html')
