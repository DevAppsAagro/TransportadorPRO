from django.shortcuts import render

def dashboard(request):
    return render(request, 'core/dashboard/dashboard.html')

def financeiro(request):
    return render(request, 'core/financeiro/financeiro.html')

def contatos(request):
    return render(request, 'core/contatos/contatos.html')

def veiculos(request):
    return render(request, 'core/veiculos/veiculos.html')

def relatorios(request):
    return render(request, 'core/relatorios/relatorios.html')

def empresa(request):
    return render(request, 'core/empresa/empresa.html')

def configuracao(request):
    return render(request, 'core/configuracao/configuracao.html')