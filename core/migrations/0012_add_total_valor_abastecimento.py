from django.db import migrations, models
from decimal import Decimal

def calculate_total_valor(apps, schema_editor):
    Abastecimento = apps.get_model('core', 'Abastecimento')
    for abastecimento in Abastecimento.objects.all():
        abastecimento.total_valor = abastecimento.litros * abastecimento.valor_litro
        abastecimento.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_abastecimento'),
    ]

    operations = [
        migrations.AddField(
            model_name='abastecimento',
            name='total_valor',
            field=models.DecimalField(
                'Valor Total',
                max_digits=10,
                decimal_places=2,
                default=Decimal('0.00'),
                editable=False
            ),
        ),
        migrations.RunPython(calculate_total_valor),
    ]