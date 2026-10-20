# Hospedar o Lertix em uma VPS Linux da Locaweb

Esta configuração usa uma VPS Ubuntu 24.04 LTS com PostgreSQL local, Gunicorn
gerenciado pelo `systemd` e Nginx para HTTPS, arquivos estáticos e mídia. O
domínio continua registrado na Locaweb. Estes passos são executados no servidor
por SSH; não compartilhe senha, chave privada ou conteúdo do arquivo de ambiente.

Os exemplos usam `/opt/lertix/app` para o código, `/var/lib/lertix/media` para
capas enviadas pelo admin e o domínio `lertrix.com`. Ajuste os nomes se o seu
servidor ou domínio forem diferentes. A publicação no Render permanece como
alternativa independente, documentada no README.

## 1. Preparar a VPS

Conecte-se por SSH com uma conta administrativa e atualize/instale os pacotes:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-dev build-essential \
  libpq-dev postgresql nginx certbot python3-certbot-nginx
python3 --version
```

Use Python 3.12 ou superior. No firewall da VPS, mantenha SSH liberado e permita
as portas TCP 80 e 443. Não exponha a porta do PostgreSQL publicamente.

Crie a conta de serviço e obtenha o código:

```bash
sudo adduser --system --group --no-create-home --home /opt/lertix \
  --shell /usr/sbin/nologin lertix
sudo install -d -o lertix -g www-data -m 0750 /opt/lertix
sudo -u lertix git clone https://github.com/Lorenzotecnologia/Lertix.git \
  /opt/lertix/app
sudo -u lertix python3 -m venv /opt/lertix/venv
sudo -u lertix /opt/lertix/venv/bin/pip install \
  -r /opt/lertix/app/backend/requirements.txt
```

Se o repositório não for público, configure uma chave de deploy somente de
leitura no servidor antes do `git clone`.

## 2. Criar o banco e configurar o ambiente

Crie um usuário PostgreSQL; `createuser` solicita a senha sem colocá-la no
comando ou no histórico do shell:

```bash
sudo -u postgres createuser --pwprompt lertix
sudo -u postgres createdb --owner=lertix lertrix
```

Gere uma senha de banco URL-safe, por exemplo com `openssl rand -hex 32`, e
informe a mesma senha ao PostgreSQL e na URL abaixo. Gere também uma chave
Django secreta (o comando abaixo imprime uma chave nova):

```bash
sudo -u lertix /opt/lertix/venv/bin/python -c \
  'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Instale e edite o arquivo de ambiente. Substitua todos os valores `replace-...`
e configure a senha SMTP da caixa Locaweb. Restrinja o arquivo ao usuário de
serviço:

```bash
sudo install -d -o root -g lertix -m 0750 /etc/lertix
sudo install -o root -g lertix -m 0640 \
  /opt/lertix/app/infra/lertix.env.example /etc/lertix/lertix.env
sudoedit /etc/lertix/lertix.env
```

`DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` e
`CANONICAL_HOST` já trazem os dois domínios esperados. Se não for usar SMTP ou
Correios, deixe as credenciais correspondentes vazias e não ative a integração.
Mantenha cada variável em uma linha; envolva valores que contenham espaços ou
caracteres especiais de shell em aspas simples (sem aspas simples dentro do
valor), pois o arquivo também é lido pelo comando de administração abaixo.
Não copie `.env` para o Git.

Crie a pasta persistente de mídia:

```bash
sudo install -d -o lertix -g www-data -m 2750 /var/lib/lertix/media
sudo install -d -o lertix -g www-data -m 0755 \
  /opt/lertix/app/backend/staticfiles
```

## 3. Instalar Gunicorn e Nginx

Copie os arquivos de serviço incluídos no repositório e configure o Nginx:

```bash
sudo install -o root -g root -m 0644 \
  /opt/lertix/app/infra/lertix.service /etc/systemd/system/lertix.service
sudo install -o root -g root -m 0644 \
  /opt/lertix/app/infra/lertix-deploy.service \
  /etc/systemd/system/lertix-deploy.service
sudo install -o root -g root -m 0644 \
  /opt/lertix/app/infra/nginx-lertix.conf \
  /etc/nginx/sites-available/lertrix
sudo ln -s /etc/nginx/sites-available/lertrix \
  /etc/nginx/sites-enabled/lertrix
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl reload nginx
```

O Nginx encaminha as requisições dinâmicas ao socket privado do Gunicorn e
entrega `/static/` e `/media/` diretamente. Não abra a porta do Gunicorn no
firewall.

## 4. DNS e HTTPS na Locaweb

No painel Locaweb, em Domínios → Gerenciar DNS, aponte o domínio para o IP
público da VPS:

| Tipo | Nome | Valor |
|---|---|---|
| A | `@` | IP público da VPS |
| CNAME | `www` | `lertrix.com` |

Remova apenas os registros antigos de `@` e `www` que apontam para a hospedagem
anterior. **Preserve os registros MX e TXT**, necessários ao e-mail (SPF, DKIM
e validações). Se existir um registro AAAA, confirme que aponta para um IPv6
configurado na VPS; caso contrário, remova-o para evitar tráfego IPv6 quebrado.

Depois que o DNS resolver para o IP da VPS, emita o certificado HTTPS:

```bash
sudo certbot --nginx -d lertrix.com -d www.lertrix.com
sudo certbot renew --dry-run
```

O Nginx encaminha o protocolo HTTPS ao Django. O Django força HTTPS quando
`DJANGO_DEBUG=false`; por isso, finalize e teste o certificado antes de expor o
site ao público.

## 5. Aplicar migrações e iniciar

Com o ambiente configurado, rode migrações e gere os arquivos estáticos:

```bash
sudo systemctl start lertix-deploy.service
sudo systemctl status lertix-deploy.service --no-pager
```

Se o serviço de deploy falhar, consulte `sudo journalctl -u
lertix-deploy.service -n 100 --no-pager`, corrija a configuração e execute-o
novamente. Em seguida, inicie o site:

```bash
sudo systemctl enable --now lertix.service
sudo systemctl status lertix.service --no-pager
```

Crie o primeiro usuário administrativo:

```bash
sudo -u lertix bash /opt/lertix/app/infra/manage-vps.sh createsuperuser
```

Verifique `https://www.lertrix.com/api/health/`, a vitrine, `/admin/`, o envio do
formulário e uma imagem enviada pelo admin. Logs da aplicação:

```bash
sudo journalctl -u lertix.service -f
```

## Atualizações e cópias de segurança

Para atualizar, faça backup do banco e da pasta de mídia antes de alterações
importantes. Depois atualize o código como a conta de serviço, instale
dependências, aplique migrações/estáticos e reinicie:

```bash
sudo -u lertix git -C /opt/lertix/app pull --ff-only
sudo -u lertix /opt/lertix/venv/bin/pip install \
  -r /opt/lertix/app/backend/requirements.txt
sudo systemctl start lertix-deploy.service
sudo systemctl restart lertix.service
```

Mantenha backups externos e testados do PostgreSQL e de `/var/lib/lertix/media`.
Os arquivos de configuração de infraestrutura deste repositório são modelos;
confirme domínio, caminhos, usuários e regras de firewall antes de aplicar.
