from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.decorators import login_required

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Nome')
    last_name = forms.CharField(max_length=30, required=True, label='Sobrenome')
    email = forms.EmailField(max_length=254, required=True, label='E-mail')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'E-mail',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-sm'}),
        }

def login_view(request):
    # Inicializar variável de logo da empresa
    from ..models import Empresa
    
    # Obter empresas para exibir logo no carregamento
    empresas = Empresa.objects.all()
    empresa_logo = None
    if empresas.exists():
        empresa = empresas.first()
        # Garantir que a URL da logo seja completa e absoluta
        if empresa.logo:
            # O campo logo já é uma string URL
            empresa_logo = empresa.logo
            # Se a URL não começar com http ou https, adicionar o domínio
            if not (empresa_logo.startswith('http://') or empresa_logo.startswith('https://')):
                from django.contrib.sites.shortcuts import get_current_site
                current_site = get_current_site(request)
                protocol = 'https' if request.is_secure() else 'http'
                empresa_logo = f"{protocol}://{current_site.domain}{empresa_logo}"
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Buscar empresa associada ao usuário (se existir)
            empresa = None
            try:
                empresas = Empresa.objects.filter(usuario=user)
                if empresas.exists():
                    empresa = empresas.first()
                    # Garantir que a URL da logo seja completa e absoluta
                    if empresa.logo:
                        # O campo logo já é uma string URL
                        empresa_logo = empresa.logo
                        # Se a URL não começar com http ou https, adicionar o domínio
                        if not (empresa_logo.startswith('http://') or empresa_logo.startswith('https://')):
                            from django.contrib.sites.shortcuts import get_current_site
                            current_site = get_current_site(request)
                            protocol = 'https' if request.is_secure() else 'http'
                            empresa_logo = f"{protocol}://{current_site.domain}{empresa_logo}"
            except Exception as e:
                print(f"Erro ao buscar empresa do usuário: {e}")
            
            # Redirecionar diretamente para o dashboard
            # A tela de carregamento agora é exibida como sobreposição no próprio formulário de login
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    
    return render(request, 'core/auth/login.html', {'empresa_logo': empresa_logo})

def register(request):
    # Buscar a empresa do usuário que está tentando se registrar
    from ..models import Empresa
    
    # Inicialmente, usar a primeira empresa como fallback
    empresa_logo = None
    empresas = Empresa.objects.all()
    if empresas.exists():
        empresa = empresas.first()
        if empresa and empresa.logo:
            empresa_logo = empresa.logo
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Conta criada com sucesso!')
            
            # Redirecionar diretamente para o dashboard
            # A tela de carregamento agora é exibida como sobreposição no próprio formulário de registro
            return redirect('core:dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'core/auth/register.html', {'form': form, 'empresa_logo': empresa_logo})


@login_required
def perfil_usuario(request):
    # Obter a empresa do usuário atual
    from ..models import Empresa
    empresa_usuario = None
    try:
        empresas = Empresa.objects.filter(usuario=request.user)
        if empresas.exists():
            empresa_usuario = empresas.first()
    except Exception as e:
        print(f"Erro ao buscar empresa do usuário: {e}")
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('core:perfil')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'core/auth/perfil.html', {
        'form': form,
        'empresa_usuario': empresa_usuario
    })