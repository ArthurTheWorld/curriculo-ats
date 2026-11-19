#!/usr/bin/env bash
# Abre o Currículo ATS no navegador (Mac e Linux).
# No terminal, dentro da pasta do projeto:  ./iniciar.sh
# Na primeira vez, prepara o ambiente e instala o que precisa (alguns minutos).
set -e
cd "$(dirname "$0")"

# 1. Encontrar o Python (3.11 ou mais novo)
#    Primeiro as versões testadas: a mais nova de todas pode não ter pacotes prontos ainda.
PY=""
for candidato in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$candidato" >/dev/null 2>&1 && \
       "$candidato" -c "import sys; sys.exit(sys.version_info < (3, 11))" 2>/dev/null; then
        PY="$candidato"
        break
    fi
done
if [ -z "$PY" ]; then
    echo
    echo "  Python 3.11 ou mais novo não foi encontrado."
    echo "  Veja o passo 1 do README: \"Instalar o Python\"."
    echo
    exit 1
fi

# 2. Criar o ambiente na primeira vez
if [ ! -x ".venv/bin/python" ]; then
    echo "Preparando o ambiente pela primeira vez..."
    if ! "$PY" -m venv .venv; then
        rm -rf .venv
        echo
        echo "  Não consegui criar o ambiente do Python."
        echo "  No Ubuntu ou Debian, instale o módulo que falta e tente de novo:"
        echo "      sudo apt install python3-venv"
        echo
        exit 1
    fi
fi

# 3. Instalar ou atualizar as bibliotecas quando requirements.txt mudar
if ! cmp -s requirements.txt .venv/requirements.instalado; then
    echo "Instalando as bibliotecas. Isso leva alguns minutos só na primeira vez..."
    .venv/bin/python -m pip install --upgrade pip >/dev/null
    .venv/bin/python -m pip install -r requirements.txt
    cp requirements.txt .venv/requirements.instalado
fi

# 4. Abrir o app
echo
echo "  Abrindo o Currículo ATS no seu navegador..."
echo "  Para fechar, pressione Ctrl+C neste terminal."
echo
.venv/bin/python -m streamlit run app.py
