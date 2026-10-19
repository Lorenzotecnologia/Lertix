# Domínio www.lertrix.com e contas Locaweb

O Django roda no Render; a Locaweb continua sendo o registro do domínio/DNS e o
provedor de e-mail. O site antigo (hospedagem Locaweb) só é substituído quando
o DNS passar a apontar para o Render.

## 1. Preparar o Render (sem afetar o site atual)

1. Crie o Blueprint a partir de `render.yaml`.
2. Em **Environment**, preencha `EMAIL_HOST_USER` (ex.: `contato@lertrix.com`) e
   `EMAIL_HOST_PASSWORD` (senha da caixa criada no painel Locaweb).
   Não coloque essas senhas no repositório.
3. Valide o site em `https://<nome>.onrender.com` (o Django aceita esse host via
   `RENDER_EXTERNAL_HOSTNAME`). Atenção: com `CANONICAL_HOST` definido, esse
   endereço redireciona para `www.lertrix.com`; para testar antes da troca,
   remova temporariamente `CANONICAL_HOST`.
4. Em **Settings → Custom Domains**, adicione `www.lertrix.com` e `lertrix.com`.

## 2. E-mail SMTP (Locaweb)

Padrão: `email-ssl.com.br`, porta 465 (SSL). Se a conta usar outro servidor ou
porta (587 usa STARTTLS), ajuste `EMAIL_HOST`/`EMAIL_PORT`. Sem
`EMAIL_HOST_PASSWORD` o e-mail só é escrito no log. Mensagens de contato e
pedidos são sempre salvas no admin (`/admin/`), mesmo se o envio falhar.

## 3. DNS na Locaweb (momento da troca)

No painel Locaweb → Domínios → Gerenciar DNS (Zona de DNS):

| Tipo  | Nome    | Valor                                   |
|-------|---------|-----------------------------------------|
| CNAME | `www`   | valor exibido pelo Render (`*.onrender.com`) |
| A     | `@`     | IP exibido pelo Render (redireciona para www) |

- **Não altere** registros `MX`, `TXT` (SPF/DKIM) — são do e-mail.
- Reduza o TTL para 300 s um dia antes. Anote os valores atuais para reverter.
- Remova registros `A`/`CNAME` antigos de `www`/`@` que apontem à hospedagem.
- Aguarde a propagação; o Render emite o HTTPS automaticamente.

## 4. Migração do site antigo

1. Faça backup dos arquivos e das caixas de e-mail da hospedagem antiga.
2. Liste URLs antigas relevantes (Google/Search Console) e crie redirecionamentos
   para as novas (`/livros/<slug>/`) se necessário.
3. Cadastre os livros no admin e confira `/api/livros/`.
4. Troque o DNS (seção 3), teste `https://www.lertrix.com`, o formulário de
   contato e um pedido de teste.
5. Crie o superusuário: `python manage.py createsuperuser` no Shell do Render.
6. Mantenha a hospedagem antiga por alguns dias como reserva; depois cancele
   apenas se o e-mail não depender dela.

## Variáveis de ambiente

`CANONICAL_HOST`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`,
`EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, `CONTACT_EMAIL_TO`, `WHATSAPP_NUMBER` (DDI+DDD+número, só dígitos, ex.: `5511999998888`; vazio oculta os botões de WhatsApp).
