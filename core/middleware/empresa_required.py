from django.http import HttpResponseRedirect
from django.urls import reverse
import logging
from core.models.empresa import Empresa

logger = logging.getLogger(__name__)

class EmpresaRequiredMiddleware:
    """Middleware para verificar se o usuário tem os dados da empresa cadastrados."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Primeiro, processa a resposta normalmente
        response = self.get_response(request)
        
        # Depois verifica se o usuário está autenticado e precisa cadastrar a empresa
        if request.user.is_authenticated:
            # Se for motorista, não exige empresa cadastrada
            if hasattr(request.user, 'perfil') and getattr(request.user.perfil, 'is_motorista', False):
                return response
            # Caminhos que não devem ser redirecionados (página de cadastro da empresa, logout, etc)
            excluded_paths = [
                '/configuracoes/empresa/',
                '/admin/',
                '/logout/',
                '/static/',
                '/media/',
                '/api/',
            ]
            
            # Verifica se o caminho atual não está na lista de exclusões
            should_check = True
            for path in excluded_paths:
                if request.path.startswith(path):
                    should_check = False
                    break
            
            if should_check:
                try:
                    # Verifica se o usuário tem empresa associada usando o ORM do Django
                    empresa = Empresa.objects.filter(usuario=request.user).first()
                    
                    if not empresa:
                        logger.warning(f"Usuário {request.user.username} não tem empresa associada. Redirecionando para cadastro.")
                        return HttpResponseRedirect('/configuracoes/empresa/')
                    
                    # Verifica se os campos obrigatórios estão preenchidos
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
                        valor = getattr(empresa, campo, None)
                        if not valor or valor.strip() == '':
                            logger.warning(f"Empresa do usuário {request.user.username} não tem o campo {campo} preenchido. Redirecionando para cadastro.")
                            return HttpResponseRedirect('/configuracoes/empresa/')
                    
                except Exception as e:
                    logger.error(f"Erro ao verificar empresa do usuário {request.user.username}: {str(e)}")
                    return HttpResponseRedirect('/configuracoes/empresa/')
        
        return response
