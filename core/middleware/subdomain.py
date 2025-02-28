from django.conf import settings

class SubdomainMiddleware:
    """Middleware para processar e detectar subdomínios"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().lower()
        
        # Remover a porta se presente
        if ':' in host:
            host = host.split(':')[0]
        
        request.is_motorista_subdomain = False
        request.subdomain = None
        
        # Verificar se é um subdomínio
        domain_parts = host.split('.')
        if len(domain_parts) > 2:
            subdomain = domain_parts[0]
            
            # Verificar se é o subdomínio de motoristas
            if subdomain == 'motorista':
                request.is_motorista_subdomain = True
                request.subdomain = 'motorista'
        
        response = self.get_response(request)
        return response
