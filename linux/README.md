# Lertix para Linux

Este pacote contém o backend Django do Lertix e um launcher para Linux. Ele
requer Python 3.12 ou superior, o módulo `venv` e acesso à internet na primeira
execução para instalar as dependências.

Extraia o arquivo e inicie a API:

```bash
tar -xzf lertix-linux.tar.gz
cd lertix-linux
./launch.sh
```

O launcher cria `.venv` ao lado do script, instala as dependências e inicia o
servidor local em `http://127.0.0.1:8000`. A verificação de saúde fica em
`http://127.0.0.1:8000/api/health/`.

Para alterar o endereço ou a porta:

```bash
LERTIX_HOST=127.0.0.1 LERTIX_PORT=8080 ./launch.sh
```

Este servidor é para execução local e desenvolvimento; não o exponha diretamente
à internet como serviço de produção.
