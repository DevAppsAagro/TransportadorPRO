import requests
import json
from decimal import Decimal
from datetime import datetime, timedelta
import logging
from django.conf import settings
from core.models.cobranca_config import AsaasConfig
from core.models.empresa import Empresa

logger = logging.getLogger(__name__)

class CobrancaService:
    """
    Serviço para integração com a API do sistema de cobranças.
    Permite criar clientes, cobranças, subcontas e gerenciar pagamentos.
    """
    def __init__(self, usuario):
        """
        Inicializa o serviço com as configurações do usuário.
        
        Args:
            usuario: Objeto User do Django
        """
        # Inicializar configuração
        self.cobranca_config = None
        self.master_api_key = getattr(settings, 'COBRANCA_MASTER_API_KEY', None)
        self.master_api_url = 'https://sandbox.asaas.com/api/v3' if getattr(settings, 'COBRANCA_SANDBOX', True) else 'https://api.asaas.com/api/v3'
        self.master_headers = {
            'Content-Type': 'application/json',
            'access_token': self.master_api_key
        }
        
        try:
            self.cobranca_config = AsaasConfig.objects.get(usuario=usuario)
            
            # Se não tem API key, verificar se o usuário tem empresa cadastrada
            if not self.cobranca_config.api_key:
                # Verificar se a chave de API mestra está configurada
                if not self.master_api_key:
                    logger.error("Chave de API mestra não configurada. Verifique as variáveis de ambiente COBRANCA_MASTER_API_KEY ou ASAAS_MASTER_API_KEY.")
                    # Não criará subconta automaticamente, será tratado na view
                # Verificar se o usuário tem empresa cadastrada
                elif self.usuario_tem_empresa_completa(usuario):
                    subconta = self.criar_subconta(usuario)
                    self.cobranca_config.api_key = subconta.get('apiKey')
                    self.cobranca_config.save()
                    logger.info(f"Subconta criada automaticamente para o usuário {usuario.username}")
                else:
                    logger.warning(f"Usuário {usuario.username} não tem empresa cadastrada ou dados incompletos")
                    # Usar a chave de API do usuário se disponível, caso contrário usar a chave mestre
            if self.cobranca_config and self.cobranca_config.api_key:
                self.api_key = self.cobranca_config.get_api_key()  # Usar o método que descriptografa a chave
                self.api_url = self.cobranca_config.api_url
                self.headers = {
                    'Content-Type': 'application/json',
                    'access_token': self.api_key
                }
                self.taxa_sistema = self.cobranca_config.taxa_sistema
                # Wallet ID para receber as taxas (configurado no settings.py)
                self.wallet_id = getattr(settings, 'COBRANCA_WALLET_ID', None)
            # Wallet ID para receber as taxas (configurado no settings.py)
            self.wallet_id = getattr(settings, 'COBRANCA_WALLET_ID', None)
        except AsaasConfig.DoesNotExist:
            # Criar configuração e subconta automaticamente
            self.cobranca_config = AsaasConfig(usuario=usuario)
            subconta = self.criar_subconta(usuario)
            self.cobranca_config.api_key = subconta.get('apiKey')
            self.cobranca_config.save()
            
            self.api_key = self.cobranca_config.get_api_key()  # Usar o método que descriptografa a chave
            self.api_url = self.cobranca_config.api_url
            self.headers = {
                'Content-Type': 'application/json',
                'access_token': self.api_key
            }
            self.taxa_sistema = self.cobranca_config.taxa_sistema
            self.wallet_id = getattr(settings, 'COBRANCA_WALLET_ID', None)
            
            logger.info(f"Configuração e subconta criadas automaticamente para o usuário {usuario.username}")
    
    def criar_cliente(self, cliente):
        """
        Cria ou atualiza um cliente na API de cobrança.
        Cria ou atualiza um cliente no sistema de cobranças.
        
        Args:
            cliente: Objeto Contato do tipo CLIENTE
            
        Returns:
            str: ID do cliente na Asaas
        """
        url = f"{self.api_url}/customers"
        
        # Verificar se o cliente já existe pelo CPF/CNPJ
        cpf_cnpj = cliente.cpf_cnpj.replace('.', '').replace('-', '').replace('/', '')
        
        if not cpf_cnpj:
            logger.error(f"Cliente {cliente.nome_completo} não possui CPF/CNPJ")
            raise ValueError(f"Cliente {cliente.nome_completo} não possui CPF/CNPJ")
        
        # Buscar cliente existente
        response = requests.get(
            f"{self.api_url}/customers?cpfCnpj={cpf_cnpj}",
            headers=self.headers
        )
        
        data = response.json()
        
        # Se o cliente já existe, retorna o ID existente
        if response.status_code == 200 and data.get('data') and len(data['data']) > 0:
            logger.info(f"Cliente {cliente.nome_completo} já existe na Asaas com ID {data['data'][0]['id']}")
            return data['data'][0]['id']
        
        # Caso contrário, cria um novo cliente
        payload = {
            'name': cliente.nome_completo,
            'cpfCnpj': cpf_cnpj,
            'email': cliente.email or '',
            'phone': cliente.telefone or '',
            'mobilePhone': cliente.telefone or '',  # Usando o mesmo telefone para celular
            'address': cliente.logradouro or '',
            'addressNumber': cliente.numero or '',
            'complement': cliente.complemento or '',
            'province': cliente.bairro or '',
            'postalCode': cliente.cep.replace('-', '') if cliente.cep else '',
            'externalReference': str(cliente.id),
            'notificationDisabled': False,
        }
        
        logger.info(f"Criando cliente na Asaas: {payload}")
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code in (200, 201):
            data = response.json()
            logger.info(f"Cliente criado com sucesso na Asaas com ID {data['id']}")
            return data['id']
        else:
            error_msg = f"Erro ao criar cliente no sistema de cobranças: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def criar_cobranca(self, frete, data_vencimento=None):
        """
        Cria uma cobrança no sistema de cobranças para um frete.
        
        Args:
            frete: Objeto Frete
            data_vencimento: Data de vencimento da cobrança (opcional)
            
        Returns:
            dict: Dados da cobrança criada
        """
        # Verificar se o frete já possui uma cobrança
        if frete.asaas_cobranca_id:
            logger.warning(f"Frete {frete.id} já possui uma cobrança com ID {frete.asaas_cobranca_id}")
            return self.consultar_cobranca(frete.asaas_cobranca_id)
        
        # Verificar se o frete tem cliente associado
        if not frete.cliente:
            error_msg = f"Frete {frete.id} não possui cliente associado"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Obter cliente ou criar se não existir
        try:
            cliente_id = self.criar_cliente(frete.cliente)
        except Exception as e:
            logger.error(f"Erro ao criar cliente para o frete {frete.id}: {str(e)}")
            raise
        
        # Calcular valores
        valor_frete = float(frete.valor_total)
        valor_total = valor_frete + float(self.taxa_sistema)
        
        # Definir data de vencimento (padrão: data do frete ou 7 dias)
        if not data_vencimento:
            if frete.data_vencimento:
                data_vencimento = frete.data_vencimento
            else:
                data_vencimento = datetime.now().date() + timedelta(days=7)
        
        # Preparar payload
        payload = {
            'customer': cliente_id,
            'billingType': 'BOLETO',  # Pode ser configurável: BOLETO, CREDIT_CARD, PIX
            'value': valor_total,
            'dueDate': data_vencimento.strftime('%Y-%m-%d'),
            'description': f'Frete #{frete.id} - {frete.origem} para {frete.destino}',
            'externalReference': f'FRETE-{frete.id}',
        }
        
        # Adicionar split se tiver wallet_id configurado
        if self.wallet_id:
            payload['split'] = [{
                'walletId': self.wallet_id,
                'fixedValue': float(self.taxa_sistema)  # Valor fixo em vez de percentual
            }]
        
        logger.info(f"Criando cobrança no sistema de cobranças: {payload}")
        
        # Enviar requisição
        url = f"{self.api_url}/payments"
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code in (200, 201):
            data = response.json()
            logger.info(f"Cobrança criada com sucesso no sistema de cobranças com ID {data['id']}")
            
            # Atualizar frete com informações da cobrança
            frete.asaas_cobranca_id = data['id']
            frete.asaas_link_pagamento = data.get('invoiceUrl')
            frete.asaas_status = data.get('status', 'PENDING')
            frete.asaas_data_criacao = datetime.now()
            frete.asaas_data_vencimento = data_vencimento
            frete.asaas_valor_total = Decimal(str(data.get('value', 0)))
            frete.save()
            
            return data
        else:
            error_msg = f"Erro ao criar cobrança no sistema de cobranças: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def consultar_cobranca(self, cobranca_id):
        """
        Atualiza o status de uma cobrança no sistema de cobranças.
        
        Args:
            cobranca_id: ID da cobrança no sistema de cobranças
            
        Returns:
            dict: Dados da cobrança
        """
        url = f"{self.api_url}/payments/{cobranca_id}"
        
        logger.info(f"Consultando cobrança {cobranca_id} no sistema de cobranças")
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Cobrança {cobranca_id} consultada com sucesso no sistema de cobranças: status={data['status']}")
            return data
        else:
            error_msg = f"Erro ao consultar cobrança {cobranca_id} no sistema de cobranças: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def atualizar_status_cobranca(self, frete):
        """
        Atualiza o status da cobrança de um frete.
        
        Args:
            frete: Objeto Frete
            
        Returns:
            bool: True se o status foi atualizado, False caso contrário
        """
        if not frete.asaas_cobranca_id:
            logger.warning(f"Frete {frete.id} não possui cobrança associada")
            return False
        
        try:
            dados_cobranca = self.consultar_cobranca(frete.asaas_cobranca_id)
            
            # Atualizar status no frete
            frete.asaas_status = dados_cobranca['status']
            
            # Se foi pago, atualizar data de recebimento
            if dados_cobranca['status'] in ('RECEIVED', 'CONFIRMED'):
                if not frete.data_recebimento:
                    frete.data_recebimento = datetime.now().date()
            
            frete.save()
            logger.info(f"Status da cobrança do frete {frete.id} atualizado para {frete.asaas_status}")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao atualizar status da cobrança do frete {frete.id}: {str(e)}")
            return False
    
    def cancelar_cobranca(self, frete):
        """
        Cancela uma cobrança no sistema de cobranças.
        
        Args:
            frete: Objeto Frete
            
        Returns:
            bool: True se a cobrança foi cancelada, False caso contrário
        """
        if not frete.asaas_cobranca_id:
            logger.warning(f"Frete {frete.id} não possui cobrança associada")
            return False
        
        url = f"{self.api_url}/payments/{frete.asaas_cobranca_id}/cancel"
        
        logger.info(f"Cancelando cobrança {frete.asaas_cobranca_id} no sistema de cobranças")
        
        response = requests.post(url, headers=self.headers)
        
        if response.status_code in (200, 204):
            # Atualizar status no frete
            frete.asaas_status = 'CANCELED'
            frete.save()
            logger.info(f"Cobrança do frete {frete.id} cancelada com sucesso")
            return True
        else:
            error_msg = f"Erro ao cancelar cobrança do frete {frete.id}: {response.text}"
            logger.error(error_msg)
            return False

    def usuario_tem_empresa_completa(self, usuario):
        """
        Verifica se o usuário tem uma empresa cadastrada com todos os dados necessários
        para criar uma subconta no sistema de cobranças.
        
        Args:
            usuario: Objeto User do Django
            
        Returns:
            bool: True se o usuário tem empresa completa, False caso contrário
        """
        try:
            # Verificar se o usuário tem empresa associada usando o ORM do Django
            empresa = Empresa.objects.filter(usuario=usuario).first()
            
            if not empresa:
                logger.warning(f"Usuário {usuario.username} não tem empresa associada")
                return False
            
            # Verificar campos obrigatórios
            campos_obrigatorios = [
                'razao_social',
                'cnpj',
                'cep',
                'logradouro',
                'numero',
                'bairro',
                'cidade',
                'estado',
                'telefone',
                'email'
            ]
            
            for campo in campos_obrigatorios:
                valor = getattr(empresa, campo, None)
                if not valor or valor.strip() == '':
                    logger.warning(f"Empresa do usuário {usuario.username} não tem o campo {campo} preenchido")
                    return False
            
            # Verificar se o CEP está no formato correto
            cep = empresa.cep.replace('-', '').replace('.', '').strip()
            if len(cep) != 8:
                logger.warning(f"CEP da empresa do usuário {usuario.username} está em formato inválido: {empresa.cep}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Erro ao verificar empresa do usuário {usuario.username}: {str(e)}")
            return False
    
    def criar_subconta(self, usuario):
        """
        Cria uma subconta no sistema de cobranças para um usuário.
        
        Args:
            usuario: Objeto User do Django
            
        Returns:
            dict: Dados da subconta criada
        """
        # Obter informações da empresa do usuário usando o ORM do Django
        empresa = Empresa.objects.filter(usuario=usuario).first()
        
        if empresa:
            # Usar dados da empresa cadastrada
            nome = empresa.nome_fantasia or empresa.razao_social
            email = empresa.email
            cpfCnpj = empresa.cnpj
            
            # Garantir que estamos usando os valores exatos que a Asaas aceita
            # MEI, LIMITED, INDIVIDUAL, ASSOCIATION
            company_type = empresa.company_type
            
            # Verificar se o valor já é um dos aceitos pela Asaas
            valid_types = ['MEI', 'LIMITED', 'INDIVIDUAL', 'ASSOCIATION']
            if company_type not in valid_types:
                # Mapear valores antigos para os valores aceitos pela Asaas
                if company_type == 'LTDA':
                    company_type = 'LIMITED'
                elif company_type in ['EIRELI', 'INDIVIDUAL']:
                    company_type = 'INDIVIDUAL'
                elif company_type == 'SA':
                    company_type = 'LIMITED'
                elif company_type in ['INSTITUITION_NGO_ASSOCIATION', 'ASSOCIATION']:
                    company_type = 'ASSOCIATION'
                else:
                    # Valor padrão se nenhum mapeamento for encontrado
                    company_type = 'LIMITED'
                
            logger.info(f"Tipo de empresa original: {empresa.company_type}, valor enviado para API: {company_type}")
            
            # Criar payload com dados mínimos necessários
            payload = {
                "name": nome,
                "email": email,
                "cpfCnpj": cpfCnpj.replace('.', '').replace('/', '').replace('-', ''),  # Remover caracteres especiais
                "companyType": company_type,  # Usar o tipo de empresa correto (MEI, LIMITED, INDIVIDUAL, ASSOCIATION)
                "mobilePhone": empresa.telefone.replace('(', '').replace(')', '').replace(' ', '').replace('-', ''),  # Formato: 11999999999
                "address": empresa.logradouro,
                "addressNumber": empresa.numero,
                "province": empresa.bairro,
                "postalCode": empresa.cep.replace('-', '').replace('.', '').strip(),
                "city": empresa.cidade,
                "state": empresa.estado,
                "incomeValue": 10000.00  # Valor padrão de faturamento mensal (R$ 10.000,00)
            }
            
            logger.info(f"Usando dados da empresa cadastrada para {usuario.username}: {empresa.razao_social}, {empresa.cidade}/{empresa.estado}")
        else:
            # Se não tem empresa, usar dados do usuário
            logger.warning(f"Usuário {usuario.username} não tem empresa cadastrada. Usando dados básicos.")
            nome = f"{usuario.first_name} {usuario.last_name}" if usuario.first_name else usuario.username
            email = usuario.email
            
            # Payload simplificado apenas com dados do usuário
            payload = {
                "name": nome,
                "email": email,
                "companyType": "LIMITED",  # Valor aceito pela Asaas para Sociedade Limitada (LTDA)
                "postalCode": "01001000",  # CEP válido padrão (centro de São Paulo)
                "addressNumber": "S/N",  # Número padrão
                "address": "Praça da Sé",  # Endereço padrão
                "province": "Sé",  # Bairro padrão
                "city": "São Paulo",  # Cidade padrão
                "state": "SP",  # Estado padrão
                "mobilePhone": "11999999999",  # Telefone padrão
                "incomeValue": 10000.00  # Valor padrão de faturamento mensal (R$ 10.000,00)
            }
        
        # Enviar requisição para API master do sistema de cobranças
        url = f"{self.master_api_url}/accounts"
        
        logger.info(f"Criando subconta para o usuário {usuario.username} com payload: {payload}")
        logger.info(f"URL: {url}, Headers: {self.master_headers}")
        
        try:
            response = requests.post(url, headers=self.master_headers, json=payload)
            
            # Registrar a resposta completa para debug
            logger.info(f"Resposta da API: Status {response.status_code}, Conteúdo: {response.text}")
            
            if response.status_code in (200, 201):
                data = response.json()
                logger.info(f"Subconta criada com sucesso para o usuário {usuario.username} com API Key {data.get('apiKey')}")
                return data
            else:
                error_msg = f"Erro ao criar subconta para o usuário {usuario.username}: Status {response.status_code}, Resposta: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Exceção ao criar subconta para o usuário {usuario.username}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

