from django.http import HttpResponseRedirect

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
