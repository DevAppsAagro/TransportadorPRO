from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from core.models.perfil_usuario import PerfilUsuario
from core.models.abastecimento_pendente import AbastecimentoPendente
from core.models.caminhao import Caminhao
from core.models.cobranca_config import AsaasConfig

# Configuração para exibir o Perfil junto com o Usuário
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil do Usuário'
    fk_name = 'usuario'

# Sobrescrever o UserAdmin padrão
class CustomUserAdmin(UserAdmin):
    inlines = (PerfilUsuarioInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_tipo_usuario')
    list_select_related = ('perfil', )
    
    def get_tipo_usuario(self, instance):
        try:
            return instance.perfil.get_tipo_usuario_display()
        except PerfilUsuario.DoesNotExist:
            return "Sem Perfil"
    get_tipo_usuario.short_description = 'Tipo de Usuário'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

# Classe para AbastecimentoPendente
class AbastecimentoPendenteAdmin(admin.ModelAdmin):
    list_display = ('motorista', 'data', 'posto', 'combustivel', 'litros', 'valor_total', 'status')
    list_filter = ('status', 'data', 'combustivel')
    search_fields = ('motorista__usuario__username',)
    date_hierarchy = 'data'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('motorista__usuario')

# Classe para Caminhao
class CaminhaoAdmin(admin.ModelAdmin):
    list_display = ('placa', 'modelo', 'ano', 'status')
    list_filter = ('status', 'ano')
    search_fields = ('placa', 'modelo')

# Classe para AsaasConfig
class AsaasConfigAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'is_sandbox', 'taxa_sistema', 'data_criacao', 'data_atualizacao')
    list_filter = ('is_sandbox', 'data_criacao')
    search_fields = ('usuario__username',)
    readonly_fields = ('data_criacao', 'data_atualizacao')

# Remover o registro padrão de User
admin.site.unregister(User)

# Registrar os modelos no admin
admin.site.register(User, CustomUserAdmin)
admin.site.register(AbastecimentoPendente, AbastecimentoPendenteAdmin)
admin.site.register(Caminhao, CaminhaoAdmin)
admin.site.register(AsaasConfig, AsaasConfigAdmin)
