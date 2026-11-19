@echo off
rem Abre o Currículo ATS no navegador. Dê dois cliques neste arquivo.
rem Na primeira vez, prepara o ambiente e instala o que precisa (alguns minutos).
chcp 65001 >nul
cd /d "%~dp0"
title Curriculo ATS

rem 1. Encontrar o Python (3.11 ou mais novo)
rem    Primeiro as versoes testadas: a mais nova de todas pode nao ter pacotes prontos ainda.
set "PY="
for %%V in (3.13 3.12 3.11) do (
    if not defined PY py -%%V -c "import sys" >nul 2>nul && set "PY=py -%%V"
)
if not defined PY py -3 -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>nul && set "PY=python"
if not defined PY (
    echo.
    echo  Python 3.11 ou mais novo nao foi encontrado neste computador.
    echo  Veja o passo 1 do README: "Instalar o Python".
    echo  Lembre de marcar "Add python.exe to PATH" na instalacao.
    echo.
    pause
    exit /b 1
)

rem 2. Criar o ambiente na primeira vez
if not exist ".venv\Scripts\python.exe" (
    echo Preparando o ambiente pela primeira vez...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo Nao consegui criar o ambiente. Veja "Problemas comuns" no README.
        pause
        exit /b 1
    )
)

rem 3. Instalar ou atualizar as bibliotecas quando requirements.txt mudar
fc /b requirements.txt ".venv\requirements.instalado" >nul 2>nul
if errorlevel 1 (
    echo Instalando as bibliotecas. Isso leva alguns minutos so na primeira vez...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Falha na instalacao. Confira a internet e veja "Problemas comuns" no README.
        pause
        exit /b 1
    )
    copy /y requirements.txt ".venv\requirements.instalado" >nul
)

rem 4. Abrir o app
echo.
echo  Abrindo o Curriculo ATS no seu navegador...
echo  Para fechar, feche esta janela.
echo.
".venv\Scripts\python.exe" -m streamlit run app.py
pause
