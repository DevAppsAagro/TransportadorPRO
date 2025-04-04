from core.models.empresa import Empresa

def empresa_context(request):
    """
    Context processor para adicionar a empresa do usuário ao contexto de todos os templates.
    """
    if request.user.is_authenticated:
        empresa = Empresa.objects.filter(usuario=request.user).first()
        return {'empresa_usuario': empresa}
    return {'empresa_usuario': None}
