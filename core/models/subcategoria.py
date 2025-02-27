from django.db import models
from .categoria import Categoria

class Subcategoria(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Subcategoria'
        verbose_name_plural = 'Subcategorias'
        ordering = ['categoria', 'nome']
    
    def __str__(self):
        return f"{self.categoria.nome} - {self.nome}"
    
    @property
    def tipo(self):
        return self.categoria.tipo
    
    @property
    def alocacao(self):
        return self.categoria.alocacao