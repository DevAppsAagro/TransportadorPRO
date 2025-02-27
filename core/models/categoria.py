from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    TIPO_CHOICES = [
        ('CUSTO_FIXO', 'Custo Fixo'),
        ('CUSTO_VARIAVEL', 'Custo Variável'),
        ('INVESTIMENTO', 'Investimento')
    ]
    
    ALOCACAO_CHOICES = [
        ('VEICULO', 'Veículo'),
        ('FRETE', 'Frete'),
        ('ADMINISTRATIVO', 'Administrativo')
    ]
    
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    alocacao = models.CharField(max_length=20, choices=ALOCACAO_CHOICES)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
    
    def __str__(self):
        return self.nome