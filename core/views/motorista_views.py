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
from django.db.models import Q
from decimal import Decimal

from ..models import AbastecimentoPendente, Caminhao, Contato, Frete, Empresa

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


def motorista_logout(request):
    """View de logout para o subdomínio de motoristas"""
    logout(request)
    return redirect('motorista:login')


def get_first_name(request):
    """View para obter o primeiro nome do motorista via AJAX"""
    from django.http import JsonResponse
    from django.contrib.auth.models import User
    
    username = request.GET.get('username')
    first_name = ''
    
    if username:
        try:
            user = User.objects.get(username=username)
            first_name = user.first_name
        except User.DoesNotExist:
            pass
    
    return JsonResponse({'first_name': first_name})


def motorista_login(request):
    """View de login para o subdomínio de motoristas"""
    # Redirecionar para o dashboard se já estiver logado como motorista
    if is_motorista(request.user):
        return redirect('motorista:dashboard')
    
    # Obter empresas para exibir logo no carregamento
    empresas = Empresa.objects.all()
    empresa_logo = None
    if empresas.exists():
        empresa = empresas.first()
        empresa_logo = empresa.logo if empresa.logo else None
    
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
                
                # Buscar empresa associada ao motorista (se tiver caminhão atual)
                empresa = None
                try:
                    caminhao_atual = user.perfil.caminhao_atual
                    if caminhao_atual:
                        empresas = Empresa.objects.filter(usuario=caminhao_atual.usuario)
                        if empresas.exists():
                            empresa = empresas.first()
                            empresa_logo = empresa.logo if empresa.logo else None
                except:
                    pass
                
                # Redirecionar diretamente para o dashboard
                # A tela de carregamento agora é exibida como sobreposição no próprio formulário de login
                return redirect('motorista:dashboard')
            else:
                messages.error(request, 'Acesso negado. Esta área é restrita para motoristas.')
        else:
            messages.error(request, 'Usuário ou senha inválidos!')
    
    # Tentar obter o primeiro nome do usuário se ele estiver autenticado
    first_name = None
    if request.user.is_authenticated:
        first_name = request.user.first_name
    
    return render(request, 'motorista/login.html', {
        'empresa_logo': empresa_logo,
        'first_name': first_name
    })


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
    
    # Buscar caminhão atual do motorista e a empresa associada
    empresa = None
    try:
        caminhao_atual = motorista.perfil.caminhao_atual
        if caminhao_atual:
            # Obter a empresa do usuário dono do caminhão
            empresas = Empresa.objects.filter(usuario=caminhao_atual.usuario)
            if empresas.exists():
                empresa = empresas.first()
    except:
        caminhao_atual = None
    
    return render(request, 'motorista/dashboard.html', {
        'motorista': motorista,
        'abastecimentos_pendentes': abastecimentos_pendentes[:5],
        'caminhao_atual': caminhao_atual,
        'empresa': empresa
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
    """Permite que o motorista crie um novo abastecimento pendente"""
    motorista = request.user
    
    # Obter o caminhão atual do motorista
    try:
        caminhao = motorista.perfil.caminhao_atual
    except:
        messages.error(request, 'Você não possui um caminhão associado!')
        return redirect('motorista:dashboard')
    
    if request.method == 'POST':
        try:
            # Extrair dados do formulário
            posto_id = request.POST.get('posto')
            data = request.POST.get('data')
            combustivel = request.POST.get('combustivel')
            litros = request.POST.get('litros')
            valor_litro = request.POST.get('valor_litro')
            km_atual = request.POST.get('km_atual')
            observacao = request.POST.get('observacao')
            frete_id = request.POST.get('frete')
            situacao = request.POST.get('situacao')
            data_vencimento = request.POST.get('data_vencimento')
            data_pagamento = request.POST.get('data_pagamento')
            
            # Validações básicas
            if not posto_id or not data or not combustivel or not litros or not valor_litro or not km_atual or not situacao or not data_vencimento:
                messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos!')
                return redirect('motorista:criar_abastecimento_pendente')
            
            # Converter valores
            try:
                litros = Decimal(litros.replace(',', '.'))
                valor_litro = Decimal(valor_litro.replace(',', '.'))
                
                # Verificar se o km_atual está dentro do intervalo permitido para IntegerField
                try:
                    km_atual_int = int(km_atual)
                    # Verificar se o valor está dentro do intervalo válido para IntegerField
                    if km_atual_int < -2147483648 or km_atual_int > 2147483647:
                        raise ValueError(f"Quilometragem {km_atual_int} está fora do intervalo permitido")
                    km_atual = km_atual_int
                except ValueError as e:
                    # Se não for possível converter para int ou o valor for muito grande
                    messages.error(request, f'Quilometragem inválida! O valor deve ser um número inteiro entre -2147483648 e 2147483647. Erro: {str(e)}')
                    return redirect('motorista:criar_abastecimento_pendente')
                
                # Converter data e data_vencimento para objeto date
                from datetime import datetime
                data = datetime.strptime(data, '%Y-%m-%d').date()
                data_vencimento = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
                
                # Converter data_pagamento se foi fornecida
                data_pagamento_obj = None
                if data_pagamento:
                    data_pagamento_obj = datetime.strptime(data_pagamento, '%Y-%m-%d').date()
            except ValueError as e:
                messages.error(request, f'Valores inválidos! Verifique os campos numéricos. Erro: {str(e)}')
                return redirect('motorista:criar_abastecimento_pendente')
            except Exception as e:
                messages.error(request, f'Erro ao processar os dados: {str(e)}')
                return redirect('motorista:criar_abastecimento_pendente')
            
            # Obter objetos relacionados
            posto = get_object_or_404(Contato, id=posto_id, tipo='POSTO')
            
            # Verificar se o frete foi selecionado
            frete = None
            if frete_id:
                frete = get_object_or_404(Frete, id=frete_id, caminhao=caminhao)
            
            # Calcular valor total
            valor_total = litros * valor_litro
            
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
                observacao=observacao,
                frete=frete,
                situacao=situacao,
                data_vencimento=data_vencimento,
                data_pagamento=data_pagamento_obj
            )
            
            messages.success(request, 'Abastecimento cadastrado com sucesso! Aguarde a aprovação.')
            return redirect('motorista:listar_abastecimentos_pendentes')
            
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar abastecimento: {str(e)}')
    
    # Obter postos para o formulário - CORRIGIDO: Mostrar apenas postos do administrador e os criados pelo motorista
    admin_usuario = caminhao.usuario
    postos = Contato.objects.filter(
        tipo='POSTO'
    ).filter(
        Q(usuario=admin_usuario) | Q(usuario=motorista)
    ).order_by('nome_completo')
    
    # Obter fretes recentes para o formulário
    fretes = Frete.objects.filter(caminhao=caminhao).order_by('-data_saida')[:20]
    
    return render(request, 'motorista/abastecimentos/novo.html', {
        'postos': postos,
        'fretes': fretes
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
        senha_atual = request.POST.get('senha_atual')
        senha_nova = request.POST.get('senha_nova')
        senha_confirmacao = request.POST.get('senha_confirmacao')
        
        # Validação básica
        if not senha_atual or not senha_nova or not senha_confirmacao:
            messages.error(request, 'Todos os campos são obrigatórios')
            return redirect('motorista:alterar_senha')
        
        if senha_nova != senha_confirmacao:
            messages.error(request, 'A nova senha e a confirmação não coincidem')
            return redirect('motorista:alterar_senha')
        
        # Verificar senha atual
        user = authenticate(username=request.user.username, password=senha_atual)
        if user is None:
            messages.error(request, 'Senha atual incorreta')
            return redirect('motorista:alterar_senha')
        
        # Alterar senha
        request.user.set_password(senha_nova)
        request.user.save()
        
        # Realizar login novamente com a nova senha
        login(request, request.user)
        
        messages.success(request, 'Senha alterada com sucesso')
        return redirect('motorista:perfil')
    
    return render(request, 'motorista/alterar_senha.html')


@login_required
@motorista_required
def contatos_motorista(request):
    """Lista os contatos associados ao usuário que liberou acesso ao motorista"""
    motorista = request.user
    admin_user = None
    
    # Identificar o usuário admin que liberou acesso ao motorista
    # Na falta de um campo explícito que relacione motorista ao admin,
    # vamos buscar o usuário que criou o motorista
    if hasattr(motorista, 'perfil') and hasattr(motorista.perfil, 'criado_por') and motorista.perfil.criado_por:
        admin_user = motorista.perfil.criado_por
    
    # Se não encontrou, usar o primeiro superusuário como fallback
    if not admin_user:
        admin_user = User.objects.filter(is_superuser=True).first()
    
    # Buscar contatos associados ao admin user
    if admin_user:
        contatos = Contato.objects.filter(usuario=admin_user).order_by('nome_completo')
        
        # Dados para estatísticas
        total_contatos = contatos.count()
        total_clientes = contatos.filter(tipo='CLIENTE').count()
        total_fornecedores = contatos.filter(tipo='FORNECEDOR').count()
        total_postos = contatos.filter(tipo='POSTO').count()
    else:
        contatos = []
        total_contatos = total_clientes = total_fornecedores = total_postos = 0
    
    return render(request, 'motorista/contatos/contatos.html', {
        'contatos': contatos,
        'total_contatos': total_contatos,
        'total_clientes': total_clientes,
        'total_fornecedores': total_fornecedores,
        'total_postos': total_postos,
    })


@login_required
@motorista_required
def contato_novo_motorista(request):
    """Permite ao motorista cadastrar um novo contato que será associado ao admin"""
    motorista = request.user
    
    # Identificar o usuário admin que liberou acesso ao motorista
    if hasattr(motorista, 'perfil') and hasattr(motorista.perfil, 'criado_por') and motorista.perfil.criado_por:
        admin_user = motorista.perfil.criado_por
    else:
        # Usar o primeiro superusuário como fallback
        admin_user = User.objects.filter(is_superuser=True).first()
    
    if not admin_user:
        messages.error(request, 'Não foi possível identificar o usuário administrador.')
        return redirect('motorista:dashboard')
    
    if request.method == 'POST':
        # Validar campos obrigatórios
        campos_obrigatorios = ['nome_completo', 'tipo']
        for campo in campos_obrigatorios:
            if not request.POST.get(campo):
                messages.error(request, f'O campo {campo.replace("_", " ").title()} é obrigatório.')
                return render(request, 'motorista/contatos/contato_form.html', {'contato': request.POST})
        
        try:
            # Criar novo contato associado ao admin
            contato = Contato.objects.create(
                usuario=admin_user,  # Associa o contato ao admin, não ao motorista
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
            return redirect('motorista:contatos')
        except Exception as e:
            messages.error(request, f'Erro ao criar contato: {str(e)}')
            return render(request, 'motorista/contatos/contato_form.html', {'contato': request.POST})
    
    return render(request, 'motorista/contatos/contato_form.html')


@login_required
@motorista_required
def criar_posto(request):
    """Permite que o motorista cadastre um novo posto de combustível"""
    motorista = request.user
    
    if request.method == 'POST':
        try:
            # Extrair dados do formulário
            nome_completo = request.POST.get('nome_completo')
            nome_fantasia = request.POST.get('nome_fantasia')
            telefone = request.POST.get('telefone')
            email = request.POST.get('email')
            cnpj = request.POST.get('cnpj')
            inscricao_estadual = request.POST.get('inscricao_estadual')
            endereco = request.POST.get('endereco')
            cidade = request.POST.get('cidade')
            estado = request.POST.get('estado')
            cep = request.POST.get('cep')
            observacoes = request.POST.get('observacoes')
            
            # Validações básicas
            if not nome_completo:
                messages.error(request, 'O nome do posto é obrigatório!')
                return redirect('motorista:criar_posto')
            
            # Criar o posto como um contato do tipo POSTO
            posto = Contato.objects.create(
                usuario=motorista.perfil.caminhao_atual.usuario,  # Associar ao dono do caminhão
                tipo='POSTO',
                nome_completo=nome_completo,
                nome_fantasia=nome_fantasia,
                telefone=telefone,
                email=email,
                cnpj=cnpj,
                inscricao_estadual=inscricao_estadual,
                endereco=endereco,
                cidade=cidade,
                estado=estado,
                cep=cep,
                observacoes=observacoes
            )
            
            messages.success(request, 'Posto cadastrado com sucesso!')
            return redirect('motorista:criar_abastecimento_pendente')
            
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar posto: {str(e)}')
    
    return render(request, 'motorista/contatos/novo_posto.html')
