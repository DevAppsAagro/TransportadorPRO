from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtracts the arg from the value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def count_concluidos(fretes):
    """Returns the count of completed freights"""
    return sum(1 for frete in fretes if frete.data_chegada)

@register.filter
def count_em_andamento(fretes):
    """Returns the count of in-progress freights"""
    return sum(1 for frete in fretes if not frete.data_chegada)

@register.filter
def sum_valor_total(fretes):
    """Returns the sum of total values from all freights"""
    return sum(frete.valor_total for frete in fretes)

@register.filter
def div(value, arg):
    """Divides the value by the argument"""
    try:
        if arg == 0:
            return 0
        return Decimal(value) / Decimal(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Multiplies the value by the argument"""
    try:
        return Decimal(value) * Decimal(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def sum_list(value):
    """Sums all values in a list or tuple"""
    try:
        return sum(value)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calculates the percentage of value relative to total"""
    try:
        if total == 0:
            return 0
        return (Decimal(value) / Decimal(total)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def replace(value, arg):
    """Replaces all occurrences of the first argument with the second argument in the given string"""
    if not isinstance(value, str):
        return value
    
    if ',' not in arg:
        return value
    
    old, new = arg.split(',', 1)
    return value.replace(old, new)