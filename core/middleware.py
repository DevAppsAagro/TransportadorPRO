from django.http import HttpResponseRedirect
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

class DomainRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.META.get('HTTP_HOST', '')
        path = request.path
        
        # Caso 1: É o domínio app.transportadorpro.com
        if host.startswith('app.'):
            # Se está tentando acessar a raiz, redireciona para o dashboard
            if path == '/':
                return HttpResponseRedirect('/dashboard/')
        
        # Caso 2: É o domínio principal (transportadorpro.com ou www.transportadorpro.com)
        else:
            # Se está tentando acessar áreas do sistema (dashboard, perfil, etc)
            if path.startswith('/dashboard/') or path == '/dashboard':
                # Redireciona para o domínio do app
                return HttpResponseRedirect(f'https://app.transportadorpro.com{path}')
            
        return self.get_response(request)


class EmpresaRequiredMiddleware:
    """Middleware para verificar se o usuário tem os dados da empresa cadastrados."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Primeiro, processa a resposta normalmente
        response = self.get_response(request)
        
        # Depois verifica se o usuário está autenticado e precisa cadastrar a empresa
        if request.user.is_authenticated:
            # Caminhos que não devem ser redirecionados (página de cadastro da empresa, logout, etc)
            excluded_paths = [
                reverse('core:configurar_empresa'),
                '/admin/',
                '/logout/',
                '/static/',
                '/media/',
                '/configuracoes/empresa/',
            ]
            
            # Verifica se o caminho atual não está na lista de exclusões
            should_check = True
            for path in excluded_paths:
                if request.path.startswith(path):
                    should_check = False
                    break
            
            if should_check:
                try:
                    # Verifica se o usuário tem empresa associada
                    if not hasattr(request.user, 'empresa'):
                        logger.warning(f"Usuário {request.user.username} não tem empresa associada. Redirecionando para cadastro.")
                        return HttpResponseRedirect('/configuracoes/empresa/')
                    
                    # Verifica se os campos obrigatórios estão preenchidos
                    empresa = request.user.empresa
                    campos_obrigatorios = [
                        'razao_social',
                        'cnpj',
                        'cep',
                        'logradouro',
                        'numero',
                        'bairro',
                        'cidade',
                        'estado',
                        'telefone',
                        'email'
                    ]
                    
                    for campo in campos_obrigatorios:
                        if not getattr(empresa, campo, None):
                            logger.warning(f"Empresa do usuário {request.user.username} não tem o campo {campo} preenchido. Redirecionando para cadastro.")
                            return HttpResponseRedirect('/configuracoes/empresa/')
                    
                except Exception as e:
                    logger.error(f"Erro ao verificar empresa do usuário {request.user.username}: {str(e)}")
                    return HttpResponseRedirect('/configuracoes/empresa/')
        
        return response
