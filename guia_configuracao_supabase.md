# Guia de Configuração do Bucket Supabase para Upload de Logos

Este guia explica como configurar corretamente o bucket "logos" no Supabase para permitir o upload de logos de empresas no sistema TransportadorPRO.

## 1. Criar o Bucket "logos"

1. Acesse o painel do Supabase: https://app.supabase.com
2. Selecione seu projeto
3. No menu lateral, clique em **Storage**
4. Clique no botão **New Bucket**
5. Digite o nome do bucket: `logos`
6. Marque a opção **Public bucket** para torná-lo público
7. Clique em **Create bucket**

## 2. Configurar Políticas de Acesso

Depois de criar o bucket, você precisa configurar as políticas de acesso para permitir leitura pública e escrita apenas para usuários autenticados.

### Política de Leitura Pública

1. No painel do Supabase, vá para **Storage** > **Policies**
2. Clique no botão **New Policy**
3. Selecione o bucket `logos`
4. Em **Policy Type**, selecione **SELECT (read)**
5. Em **Policy Definition**, selecione **Custom**
6. No campo de definição, insira: `true`
7. Em **Policy Name**, insira: `Allow public read access`
8. Clique em **Save Policy**

### Política de Escrita para Usuários Autenticados

1. Clique no botão **New Policy**
2. Selecione o bucket `logos`
3. Em **Policy Type**, selecione **INSERT (create)**
4. Em **Policy Definition**, selecione **Custom**
5. No campo de definição, insira: `auth.role() = 'authenticated'`
6. Em **Policy Name**, insira: `Allow authenticated users to upload`
7. Clique em **Save Policy**

### Política de Atualização para Usuários Autenticados

1. Clique no botão **New Policy**
2. Selecione o bucket `logos`
3. Em **Policy Type**, selecione **UPDATE (update)**
4. Em **Policy Definition**, selecione **Custom**
5. No campo de definição, insira: `auth.role() = 'authenticated'`
6. Em **Policy Name**, insira: `Allow authenticated users to update`
7. Clique em **Save Policy**

### Política de Exclusão para Usuários Autenticados

1. Clique no botão **New Policy**
2. Selecione o bucket `logos`
3. Em **Policy Type**, selecione **DELETE (delete)**
4. Em **Policy Definition**, selecione **Custom**
5. No campo de definição, insira: `auth.role() = 'authenticated'`
6. Em **Policy Name**, insira: `Allow authenticated users to delete`
7. Clique em **Save Policy**

## 3. Verificar Configuração

Após configurar todas as políticas, você deve ver quatro políticas para o bucket `logos`:

- **Allow public read access** (SELECT)
- **Allow authenticated users to upload** (INSERT)
- **Allow authenticated users to update** (UPDATE)
- **Allow authenticated users to delete** (DELETE)

## 4. Testar o Upload

Após configurar o bucket e as políticas, execute o script de teste para verificar se o upload está funcionando corretamente:

```bash
python test_supabase_direct.py
```

Se tudo estiver configurado corretamente, você deverá ver uma mensagem de sucesso e a URL pública do arquivo carregado.

## Solução de Problemas

Se você continuar enfrentando problemas com o upload, verifique:

1. **Credenciais do Supabase**: Certifique-se de que as variáveis de ambiente `SUPABASE_URL` e `SUPABASE_KEY` estão configuradas corretamente no arquivo `.env`.

2. **Tipo de Chave API**: Certifique-se de que está usando a chave `anon` ou `service_role` do Supabase. A chave `service_role` tem mais permissões e pode ser necessária para operações administrativas.

3. **Bucket Existente**: Confirme que o bucket `logos` foi criado corretamente no painel do Supabase.

4. **Políticas de Acesso**: Verifique se todas as políticas foram configuradas conforme descrito acima.

5. **Autenticação**: Para uploads autenticados, certifique-se de que o usuário está autenticado e que o token de autenticação está sendo passado corretamente.
