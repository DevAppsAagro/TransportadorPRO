from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse


class DomainRedirectMiddleware:
    """
    Middleware para redirecionar entre diferentes domínios e subdomínios
    conforme necessário para a aplicação.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().lower()
        
        # Remover a porta se presente
        if ':' in host:
            host = host.split(':')[0]
        
        # Verificar se é um subdomínio de motorista
        is_motorista_subdomain = host.startswith('motorista.')
        
        # Se estiver vindo de um subdomínio de motorista, adicionar um atributo
        # ao request para identificá-lo em outras partes da aplicação
        request.is_motorista_subdomain = is_motorista_subdomain
        
        # Verificar se o usuário está logado e é motorista
        is_motorista_user = False
        if request.user.is_authenticated:
            try:
                is_motorista_user = request.user.perfil.tipo_usuario == 'MOTORISTA'
            except:
                is_motorista_user = False
        
        # Ajustar caminhos de URL para o subdomínio de motorista
        if is_motorista_subdomain and not request.path.startswith('/motorista/'):
            # Se o path não começar com /motorista/, redirecionar
            # Tratar a raiz como um caso especial
            if request.path == '/':
                return HttpResponseRedirect('/motorista/')
            else:
                # Adicionar o prefixo /motorista/ a outros paths
                return HttpResponseRedirect(f'/motorista{request.path}')
        
        # Se for um motorista tentando acessar áreas de admin, redirecionar para o dashboard de motorista
        if is_motorista_user and not is_motorista_subdomain and not request.path.startswith('/motorista/'):
            try:
                # Verificar se está tentando acessar rotas administrativas
                if request.path.startswith('/abastecimentos/') or request.path.startswith('/motoristas/'):
                    # Redirecionar para o dashboard do motorista
                    return HttpResponseRedirect('/motorista/dashboard/')
            except:
                pass
        
        # Continua com o processamento padrão
        response = self.get_response(request)
        return response
