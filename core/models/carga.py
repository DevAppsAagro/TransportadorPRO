from django.db import models
from django.contrib.auth.models import User

class Carga(models.Model):
    nome = models.CharField(max_length=100, verbose_name='Nome')
    unidade_medida = models.CharField(max_length=50, verbose_name='Unidade de Medida')
    fator_multiplicacao = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Fator de Multiplicação')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuário')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    
    class Meta:
        verbose_name = 'Carga'
        verbose_name_plural = 'Cargas'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} ({self.unidade_medida})"
    
    def converter_peso(self, peso_kg):
        """Converte o peso em kg para a unidade de medida da carga"""
        if self.fator_multiplicacao:
            return peso_kg / float(self.fator_multiplicacao)
        return peso_kg