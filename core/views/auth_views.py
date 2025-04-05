from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django import forms

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Nome')
    last_name = forms.CharField(max_length=30, required=True, label='Sobrenome')
    email = forms.EmailField(max_length=254, required=True, label='E-mail')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

def login_view(request):
    # Inicializar variável de logo da empresa
    from ..models import Empresa
    
    # Obter empresas para exibir logo no carregamento
    empresas = Empresa.objects.all()
    empresa_logo = None
    if empresas.exists():
        empresa = empresas.first()
        # Garantir que a URL da logo seja completa
        if empresa.logo:
            empresa_logo = empresa.logo
    
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
                    # Garantir que a URL da logo seja completa
                    if empresa.logo:
                        empresa_logo = empresa.logo
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