"""Extrai o texto do currículo enviado (PDF com texto ou Word .docx)."""
import io
import logging

import docx
import pdfplumber

# O pdfminer (usado pelo pdfplumber) avisa demais sobre PDFs imperfeitos.
logging.getLogger("pdfminer").setLevel(logging.ERROR)

SEM_TEXTO = ("Não encontrei texto neste arquivo. Se for um PDF escaneado, envie um PDF com texto "
             "ou um arquivo .docx.")


class ArquivoIlegivel(Exception):
    """O arquivo não pôde ser lido. A mensagem é para mostrar à pessoa."""


def extrair_texto(nome_arquivo: str, conteudo: bytes) -> str:
    nome = nome_arquivo.lower()
    if nome.endswith(".docx"):
        leitor = _ler_docx
    elif nome.endswith(".pdf"):
        leitor = _ler_pdf
    else:
        raise ArquivoIlegivel("Formato não suportado. Envie o currículo em PDF ou .docx.")

    try:
        texto = leitor(conteudo)
    except Exception as erro:
        raise ArquivoIlegivel(
            "Não consegui abrir o arquivo. Ele pode estar corrompido ou protegido por senha. "
            "Tente salvar de novo como PDF ou .docx."
        ) from erro

    texto = texto.strip()
    if not texto:
        raise ArquivoIlegivel(SEM_TEXTO)
    return texto


def _ler_docx(conteudo: bytes) -> str:
    documento = docx.Document(io.BytesIO(conteudo))
    linhas = [p.text for p in documento.paragraphs]
    # Muitos currículos usam tabelas para organizar o layout.
    for tabela in documento.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                linhas.extend(p.text for p in celula.paragraphs)
    return "\n".join(linha.strip() for linha in linhas if linha.strip())


def _ler_pdf(conteudo: bytes) -> str:
    with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
        paginas = [pagina.extract_text() or "" for pagina in pdf.pages]
    return "\n".join(paginas)
