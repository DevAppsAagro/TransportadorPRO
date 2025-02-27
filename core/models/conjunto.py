from django.db import models
from django.contrib.auth.models import User
from .caminhao import Caminhao
from .carreta import Carreta

class Conjunto(models.Model):
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('INATIVO', 'Inativo')
    ]
    
    data_configuracao = models.DateField(verbose_name='Data de Configuração')
    caminhao = models.ForeignKey(Caminhao, on_delete=models.CASCADE, verbose_name='Caminhão')
    carreta1 = models.ForeignKey(Carreta, on_delete=models.CASCADE, related_name='conjunto_carreta1', verbose_name='Carreta 1')
    carreta2 = models.ForeignKey(Carreta, on_delete=models.SET_NULL, null=True, blank=True, related_name='conjunto_carreta2', verbose_name='Carreta 2')
    carreta3 = models.ForeignKey(Carreta, on_delete=models.SET_NULL, null=True, blank=True, related_name='conjunto_carreta3', verbose_name='Carreta 3')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ATIVO', verbose_name='Status')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuário')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    
    class Meta:
        verbose_name = 'Conjunto'
        verbose_name_plural = 'Conjuntos'
        ordering = ['-data_configuracao']
    
    def __str__(self):
        return f"{self.caminhao.placa} - {self.data_configuracao}"
    
    def save(self, *args, **kwargs):
        # Se este é um novo conjunto sendo criado como ATIVO
        if not self.pk and self.status == 'ATIVO':
            # Desativa todos os outros conjuntos ativos do mesmo caminhão
            Conjunto.objects.filter(caminhao=self.caminhao, status='ATIVO').update(status='INATIVO')
        super().save(*args, **kwargs)