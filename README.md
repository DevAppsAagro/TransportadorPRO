# TransportadorPRO

Sistema de gestão completo para empresas de transporte, oferecendo controle de fretes, clientes, veículos, despesas e relatórios gerenciais.

## Funcionalidades

- **Gestão de Fretes**: Cadastro e acompanhamento de fretes com origem, destino, valores e status
- **Gestão de Clientes**: Cadastro e gerenciamento de clientes, motoristas e fornecedores
- **Gestão de Veículos**: Controle de caminhões, carretas e conjuntos
- **Controle Financeiro**: Gestão de despesas, receitas e fluxo de caixa
- **Relatórios Gerenciais**: DRE, Fluxo de Caixa, Relatório de Fretes, Relatório de Veículos e Relatório de Clientes
- **Dashboard**: Visão geral do negócio com gráficos e indicadores

## Tecnologias Utilizadas

- Django (Framework Web Python)
- PostgreSQL (Banco de Dados)
- Bootstrap (Framework CSS)
- JavaScript/jQuery
- Chart.js (Gráficos)
- DataTables (Tabelas interativas)

## Requisitos

- Python 3.8+
- Django 4.0+
- PostgreSQL 12+

## Instalação

1. Clone o repositório
```
git clone https://github.com/DevAppsAagro/TransportadorPRO.git
```

2. Crie e ative um ambiente virtual
```
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências
```
pip install -r requirements.txt
```

4. Configure o banco de dados no arquivo settings.py

5. Execute as migrações
```
python manage.py migrate
```

6. Crie um superusuário
```
python manage.py createsuperuser
```

7. Inicie o servidor
```
python manage.py runserver
```

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.

## Contato

Para mais informações, entre em contato com a equipe de desenvolvimento.
