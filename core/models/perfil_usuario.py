from django.db import models
from django.contrib.auth.models import User
from .caminhao import Caminhao

class PerfilUsuario(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('MOTORISTA', 'Motorista'),
        ('USUARIO', 'Usuário Regular')
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo_usuario = models.CharField('Tipo de Usuário', max_length=20, choices=TIPO_USUARIO_CHOICES, default='USUARIO')
    telefone = models.CharField('Telefone', max_length=20, blank=True, null=True)
    foto = models.ImageField('Foto de Perfil', upload_to='perfis/', blank=True, null=True)
    
    # Campos específicos para motoristas
    cnh = models.CharField('CNH', max_length=20, blank=True, null=True)
    categoria_cnh = models.CharField('Categoria CNH', max_length=5, blank=True, null=True)
    validade_cnh = models.DateField('Validade CNH', blank=True, null=True)
    caminhao_atual = models.ForeignKey(Caminhao, on_delete=models.SET_NULL, blank=True, null=True, related_name='motorista_atual')
    
    # Controle de acesso
    ativo = models.BooleanField('Ativo', default=True)
    ultimo_acesso = models.DateTimeField('Último Acesso', blank=True, null=True)
    
    # Dados para comunicação
    receber_notificacoes = models.BooleanField('Receber Notificações', default=True)
    token_notificacao = models.CharField('Token de Notificação', max_length=255, blank=True, null=True)
    
    # Relacionamento com usuário administrador que criou o perfil
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='motoristas_criados')
    
    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_usuario_display()}"
    
    @property
    def is_motorista(self):
        return self.tipo_usuario == 'MOTORISTA'
    
    @property
    def is_admin(self):
        return self.tipo_usuario == 'ADMIN'
