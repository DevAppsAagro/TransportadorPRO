from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def configuracao(request):
    return render(request, 'core/configuracao.html')