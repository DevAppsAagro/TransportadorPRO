import logging
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from core.services.cobranca_service import CobrancaService
from core.models.cobranca_config import AsaasConfig

logger = logging.getLogger(__name__)

@login_required
def saldo_transferencias(request):
    """
    View para exibir o saldo disponível e o histórico de transferências.
    """
    try:
        # Verificar se o usuário tem configuração do sistema de cobranças
        try:
            config = AsaasConfig.objects.get(usuario=request.user)
            if not config.api_key:
                messages.warning(request, 'Você precisa configurar sua integração com o sistema de cobranças antes de acessar esta página.')
                return redirect('core:configurar_cobranca')
        except AsaasConfig.DoesNotExist:
            messages.warning(request, 'Você precisa configurar sua integração com o sistema de cobranças antes de acessar esta página.')
            return redirect('core:configurar_cobranca')
        
        # Inicializar serviço de cobranças
        cobranca_service = CobrancaService(request.user)
        
        # Consultar saldo
        saldo = cobranca_service.consultar_saldo()
        
        # Listar transferências
        transferencias = cobranca_service.listar_transferencias(limit=20)
        
        # Listar contas bancárias
        contas_bancarias = cobranca_service.listar_contas_bancarias()
        
        return render(request, 'core/transferencias/saldo.html', {
            'saldo': saldo,
            'transferencias': transferencias['data'] if transferencias else [],
            'contas_bancarias': contas_bancarias
        })
        
    except Exception as e:
        logger.error(f"Erro ao carregar página de saldo e transferências: {str(e)}")
        messages.error(request, f'Erro ao carregar informações: {str(e)}')
        return redirect('core:dashboard')

@login_required
def cadastrar_conta_bancaria(request):
    """
    View para cadastrar uma nova conta bancária.
    """
    if request.method == 'POST':
        try:
            # Inicializar serviço de cobranças
            cobranca_service = CobrancaService(request.user)
            
            # Preparar dados da conta bancária
            dados_conta = {
                'bank': request.POST.get('bank'),
                'accountName': request.POST.get('accountName'),
                'ownerName': request.POST.get('ownerName'),
                'ownerBirthDate': request.POST.get('ownerBirthDate'),
                'cpfCnpj': request.POST.get('cpfCnpj').replace('.', '').replace('-', '').replace('/', ''),
                'agency': request.POST.get('agency'),
                'account': request.POST.get('account'),
                'accountDigit': request.POST.get('accountDigit'),
                'bankAccountType': request.POST.get('bankAccountType')
            }
            
            # Criar conta bancária
            resultado = cobranca_service.criar_conta_bancaria(dados_conta)
            
            if resultado:
                messages.success(request, 'Conta bancária cadastrada com sucesso!')
                return redirect('core:saldo_transferencias')
            else:
                messages.error(request, 'Erro ao cadastrar conta bancária. Verifique os dados e tente novamente.')
                
        except Exception as e:
            logger.error(f"Erro ao cadastrar conta bancária: {str(e)}")
            messages.error(request, f'Erro ao cadastrar conta bancária: {str(e)}')
        
        # Em caso de erro, retornar para o formulário com os dados preenchidos
        return render(request, 'core/transferencias/cadastrar_conta.html', {
            'dados': request.POST
        })
    
    # Carregar lista de bancos
    bancos = [
        {'codigo': '001', 'nome': 'Banco do Brasil'},
        {'codigo': '104', 'nome': 'Caixa Econômica Federal'},
        {'codigo': '033', 'nome': 'Santander'},
        {'codigo': '341', 'nome': 'Itaú'},
        {'codigo': '237', 'nome': 'Bradesco'},
        {'codigo': '260', 'nome': 'Nubank'},
        {'codigo': '077', 'nome': 'Inter'},
        {'codigo': '212', 'nome': 'Banco Original'},
        {'codigo': '336', 'nome': 'C6 Bank'},
        {'codigo': '290', 'nome': 'PagBank'},
        {'codigo': '380', 'nome': 'PicPay'},
        # Adicione outros bancos conforme necessário
    ]
    
    return render(request, 'core/transferencias/cadastrar_conta.html', {
        'bancos': bancos
    })

@login_required
def solicitar_transferencia(request):
    """
    View para solicitar uma transferência.
    """
    if request.method == 'POST':
        try:
            # Inicializar serviço de cobranças
            cobranca_service = CobrancaService(request.user)
            
            # Obter valor e conta bancária
            valor = request.POST.get('valor')
            conta_bancaria_id = request.POST.get('conta_bancaria_id')
            
            # Validar valor
            try:
                valor_float = float(valor.replace('.', '').replace(',', '.'))
                if valor_float <= 0:
                    raise ValueError("O valor deve ser maior que zero")
            except (ValueError, AttributeError):
                messages.error(request, 'Valor inválido. Informe um valor numérico maior que zero.')
                return redirect('core:saldo_transferencias')
            
            # Solicitar transferência
            resultado = cobranca_service.solicitar_transferencia(valor_float, conta_bancaria_id)
            
            if resultado:
                messages.success(request, 'Transferência solicitada com sucesso! O valor será transferido conforme as regras do sistema de pagamentos.')
            else:
                messages.error(request, 'Erro ao solicitar transferência. Verifique o saldo disponível e tente novamente.')
                
        except Exception as e:
            logger.error(f"Erro ao solicitar transferência: {str(e)}")
            messages.error(request, f'Erro ao solicitar transferência: {str(e)}')
        
        return redirect('core:saldo_transferencias')
    
    # Se não for POST, redirecionar para a página de saldo
    return redirect('core:saldo_transferencias')
