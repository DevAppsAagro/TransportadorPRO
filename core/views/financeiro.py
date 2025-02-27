from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def financeiro(request):
    return render(request, 'core/financeiro.html')