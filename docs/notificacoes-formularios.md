# ZAC — notificações dos formulários

Estado: **formulários salvam no Cloudflare D1, mas notificações por email exigem ativação do Cloudflare Email Service**.

## Destinatário confirmado
- comercialcaxias@zacseguros.com.br

Os demais endereços da equipe precisam ser fornecidos e verificados antes de ativar o envio. Não invente endereços.

## Preparação já instalada
- `src/independent.js`: após salvar o formulário em D1, chama `sendLeadNotice` **somente quando existe o binding `env.EMAIL`**.
- Inclui nome, email, telefone, assunto, mensagem, consentimento e ID.
- Em caso de falha de email, a solicitação permanece no D1; não é perdida nem duplicada.
- Permite a lista separada por vírgulas em `ZAC_NOTIFICATION_RECIPIENTS`. Se ausente, usa o endereço confirmado acima.
- Remetente configurável em `ZAC_NOTIFICATION_SENDER`; padrão `notificacoes@zacseguros.com.br`.

## Como ativar sem trocar o provedor de e-mail
1. No painel Cloudflare, em Compute > Email Service > Email Routing > Destination Addresses, cadastrar **e verificar** cada endereço de destino.
2. Habilitar Email Sending para o domínio/sender autorizado, conforme exigências da conta. Conferir registros DNS estritamente para o domínio de envio, **sem modificar MX/SPF/DKIM existentes do serviço Locaweb sem revisão**.
3. Vincular o binding de envio no Worker via `wrangler.toml`:
   ```toml
   [[send_email]]
   name = "EMAIL"
   ```
4. Configurar `ZAC_NOTIFICATION_RECIPIENTS` com somente os endereços verificados; configurar `ZAC_NOTIFICATION_SENDER` para um remetente autorizado.
5. Testar no preview com dados sintéticos e conferir o recebimento de cada destinatário **antes** da implantação na produção.

**Não ativar Cloudflare Email Routing para substituir os MX do domínio:** os e-mails já existentes na Locaweb devem continuar operando.

Documentação oficial:
- https://developers.cloudflare.com/email-service/configuration/send-bindings/
- https://developers.cloudflare.com/email-service/configuration/email-routing-addresses/

A notificação por email ainda NÃO está ativa sem binding e verificação de remetente/destinatários.
