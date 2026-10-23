# Stack do Lertix

Diagrama do stack da aplicação e das opções de publicação presentes no
repositório. Render e VPS são alternativas de produção; SQLite é usado apenas
no desenvolvimento local.

## Aplicação e infraestrutura

```mermaid
flowchart LR
    visitor["Pessoa usuária<br/>Navegador"]

    subgraph hosting["Opções de hospedagem"]
        render["Render<br/>HTTPS + serviço web"]
        staging["Render Staging (gratuito)<br/>branch staging · desativável"]
        nginx["VPS Linux<br/>Nginx + Certbot + systemd"]
    end

    subgraph appserver["Servidor da aplicação"]
        gunicorn["Gunicorn<br/>WSGI"]
        django["Python 3.12+ · Django 5.2<br/>Vitrine · carrinho · pedidos<br/>Admin · API JSON"]
        templates["Templates Django<br/>HTML renderizado no servidor"]
        static["Arquivos estáticos<br/>frontend/static · CSS · JavaScript"]
        whitenoise["WhiteNoise<br/>arquivos estáticos no Render"]
    end

    subgraph storage["Dados e arquivos"]
        postgres["PostgreSQL<br/>produção"]
        sqlite["SQLite<br/>desenvolvimento local"]
        media["Capas dos livros<br/>disco persistente no Render<br/>/var/lib/lertix/media na VPS"]
    end

    subgraph integrations["Integrações"]
        correios["API dos Correios<br/>cotação de frete"]
        rates["Tarifas locais<br/>alternativa à cotação"]
        smtp["SMTP Locaweb<br/>e-mail de contato"]
        pix["Pix direto<br/>QR Code gerado pela aplicação"]
    end

    visitor -->|"HTTPS"| render
    visitor -.->|"HTTPS · testes"| staging
    staging -.-> gunicorn
    visitor -->|"HTTPS"| nginx
    render --> gunicorn
    nginx -->|"socket local"| gunicorn
    nginx -->|"estáticos e mídia"| visitor
    gunicorn --> django
    django -->|"renderiza"| templates
    templates -->|"HTML"| visitor
    static --> whitenoise
    static --> nginx
    whitenoise -->|"Render"| visitor

    django -->|"DATABASE_URL em produção"| postgres
    django -.->|"somente local"| sqlite
    django -->|"upload de capas"| media
    django -->|"consulta de frete"| correios
    django -->|"fallback"| rates
    django -->|"envio de mensagens"| smtp
    django -->|"dados para pagamento"| pix
```

No Render, o serviço web usa Gunicorn, WhiteNoise, PostgreSQL gerenciado e, na
configuração de produção, um disco persistente para as capas. Na VPS, Nginx
termina HTTPS e entrega estáticos e mídia; Gunicorn atende o Django por socket
local e o PostgreSQL roda na própria VPS.

O ambiente de staging (`render.staging.yaml`) publica a branch `staging` no plano
gratuito do Render para testar funcionalidades novas. Após o go-live na Locaweb
ele é suspenso (Suspend), sem ser removido, e reativado quando necessário.

O Pix é gerado diretamente pela aplicação; não há intermediador de pagamento.
O frete consulta os Correios quando configurado e pode recorrer às tarifas
mantidas no admin.

## CI e publicação

```mermaid
flowchart LR
    repo["GitHub<br/>código-fonte"]
    ci["GitHub Actions · CI<br/>Django check · collectstatic · testes"]
    render["Render Blueprint<br/>deploy da aplicação"]
    staging["Render Staging<br/>render.staging.yaml · branch staging"]
    vps["VPS Linux<br/>Nginx · systemd · PostgreSQL"]
    tag["Tag v*"]
    release["GitHub Actions<br/>validação + pacote Linux"]
    artifact["GitHub Release<br/>lertix-linux.tar.gz"]

    repo -->|"push / pull request"| ci
    repo -->|"Blueprint do Render"| render
    repo -.->|"push na branch staging"| staging
    repo -->|"deploy via SSH e systemd"| vps
    repo --> tag
    tag --> release --> artifact
```
