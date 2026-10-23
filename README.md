# Lertix

Base do projeto de e-commerce Lertix. O repositório contém a vitrine web
responsiva, servida pelo Django, além da API e dos diretórios de catálogo e
infraestrutura.

## Requisitos

- Python 3.12 ou superior
- Git
- GitHub CLI (`gh`), opcional, para autenticação com o GitHub

## Backend

Crie e ative um ambiente virtual na raiz do projeto e instale as dependências:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

No Windows PowerShell, ative o ambiente com:

```powershell
.\.venv\Scripts\Activate.ps1
```

Inicie o servidor de desenvolvimento:

```bash
cd backend
python manage.py runserver
```

A vitrine do Modelo B fica disponível em `http://127.0.0.1:8000/`. As seções
Início, Catálogo, Sobre a Editora e Contato são acessadas pela navegação da
vitrine. O painel privado em `/admin/` mostra um resumo do catálogo e oferece
atalhos para cadastrar e gerenciar livros; crie um usuário administrativo com
`python manage.py createsuperuser`. As imagens enviadas pelo painel são
armazenadas em `backend/media/` durante o desenvolvimento. Em produção,
configure armazenamento e entrega de mídia apropriados para o ambiente.
A verificação de saúde da API fica disponível em `http://127.0.0.1:8000/api/health/`.

Para executar as verificações e os testes:

```bash
cd backend
python manage.py check
python manage.py collectstatic --no-input
python manage.py test
```

Em desenvolvimento, o Django usa configurações locais padrão. Antes de publicar
o serviço, defina `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false` e
`DJANGO_ALLOWED_HOSTS` no ambiente de execução. Não versione segredos nem
arquivos `.env`.

## Publicação no Render

O arquivo `render.yaml` (plano gratuito, para testes; `render.paid.yaml` é a versão de produção) configura o deploy do Django no Render com PostgreSQL,
arquivos estáticos servidos pelo WhiteNoise e um disco persistente para as capas
enviadas pelo painel administrativo. A configuração usa os planos pagos Starter
para a aplicação e Basic para o banco.

1. Envie este repositório para o GitHub e, no Render, crie um **Blueprint** a
   partir dele. Revise os recursos e custos apresentados antes de confirmar.
2. Quando o serviço estiver disponível, abra **Settings → Custom Domains**,
   adicione `lertrix.com` e siga as instruções exibidas pelo Render para criar
   os registros DNS no provedor do domínio. O Render inclui também `www` e
   fornece HTTPS após a verificação.
3. Depois do primeiro deploy, use o Shell do serviço no Render para criar o
   usuário administrativo com `python manage.py createsuperuser` no diretório
   `backend`.

O Blueprint executa as migrações antes de cada deploy, coleta os arquivos
estáticos e verifica a aplicação em `/api/health/`. O domínio só ficará ativo
depois de adicionar o serviço no painel do Render e apontar o DNS conforme os
valores que o Render informar.

## Publicação em VPS Linux (Locaweb)

O projeto também inclui arquivos de exemplo para hospedar o Django em uma VPS
Ubuntu com PostgreSQL, Gunicorn, `systemd` e Nginx. A configuração e o passo a
passo de DNS, HTTPS, variáveis de ambiente e atualização estão em
[`docs/locaweb-dominio.md`](docs/locaweb-dominio.md). Os arquivos de serviço e
Nginx estão em `infra/`; revise os caminhos e o domínio se forem diferentes no
seu servidor. Esta opção substitui o Render para a aplicação; mantenha os
registros MX/TXT da Locaweb se o e-mail do domínio continuar lá.

## Domínio, e-mail Locaweb e funcionalidades

A loja inclui formulário de contato (`/contato/`), carrinho (`/carrinho/`),
pedidos sem pagamento online (`/pedido/`, gerenciados no admin) e API JSON do
catálogo (`/api/livros/`). O frete usa a cotação de preço e prazo dos Correios
quando a integração está configurada; sem credenciais ou medidas da embalagem,
usa a tabela interna (UF do CEP × faixa de peso), editável em Admin → Tarifas
de frete. Configure `CORREIOS_USERNAME`, `CORREIOS_ACCESS_CODE`,
`CORREIOS_POSTING_CARD`, os códigos contratados em `CORREIOS_PAC_CODE` e
`CORREIOS_SEDEX_CODE`, e as medidas da embalagem em
`CORREIOS_PACKAGE_LENGTH_CM`, `CORREIOS_PACKAGE_WIDTH_CM` e
`CORREIOS_PACKAGE_HEIGHT_CM` como variáveis de ambiente. Não envie credenciais
no código nem em mensagens. Atualize também o peso de cada livro no admin para
que a cotação seja precisa. Não há frete grátis por padrão (defina
`FREE_SHIPPING_MIN` para ativar). O domínio `www.lertrix.com`, o SMTP da Locaweb e a
migração do site antigo estão descritos em `docs/locaweb-dominio.md`.

## Estrutura

Veja o [diagrama atualizado do stack](docs/diagrama-stack.md), com a
arquitetura da aplicação, as alternativas de hospedagem e o fluxo de CI e
publicação.

```text
.
├── .github/workflows/ci.yml
├── .vscode/
├── backend/       # Projeto Django, API, modelos de catálogo e painel admin
├── catalogo/      # Planilhas de validação do catálogo
├── docs/          # Documentação do projeto
├── frontend/      # Templates, estilos e logo do site
└── infra/         # Configuração de infraestrutura
```

## Git e GitHub

Este repositório já está inicializado e vinculado ao GitHub. Para obter uma
cópia em outra máquina:

```bash
git clone https://github.com/Lorenzotecnologia/Lertix.git
cd Lertix
```

Se usar GitHub CLI, autentique-se uma vez com `gh auth login` e escolha a opção
de login pelo navegador. O workflow de CI executa `check` e os testes do Django
em pushes e pull requests.

## Versão Linux

Para gerar um pacote Linux e publicá-lo como arquivo baixável em uma GitHub
Release, crie e envie uma tag no formato `v*`:

```bash
git tag v1.0.0
git push origin v1.0.0
```

O workflow valida o backend e anexa `lertix-linux.tar.gz` à Release. O pacote
inclui `launch.sh`, que requer Python 3.12 ou superior e instala as dependências
na primeira execução. Consulte `linux/README.md` para instruções de uso. Este é
um pacote executável de um backend Django, não um binário independente de
Python.
