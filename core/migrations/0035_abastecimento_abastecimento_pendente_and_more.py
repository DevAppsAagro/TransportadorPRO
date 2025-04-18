# Generated by Django 5.0 on 2025-04-04 21:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0034_abastecimento_origem_pendente'),
    ]

    operations = [
        migrations.AddField(
            model_name='abastecimento',
            name='abastecimento_pendente',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='abastecimento_aprovado', to='core.abastecimentopendente', verbose_name='Abastecimento Pendente Original'),
        ),
        migrations.AlterField(
            model_name='contato',
            name='tipo',
            field=models.CharField(choices=[('FORNECEDOR', 'Fornecedor'), ('CLIENTE', 'Cliente'), ('FUNCIONARIO', 'Funcionário'), ('MOTORISTA', 'Motorista'), ('POSTO', 'Posto de Combustível')], max_length=20, verbose_name='Tipo'),
        ),
    ]
