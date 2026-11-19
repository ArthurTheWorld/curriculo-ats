"""Extrai o texto do currículo enviado (PDF com texto ou Word .docx)."""
import io
import logging

import docx
import pdfplumber

from curriculo_ats.modelos import limpar_controle

# O pdfminer (usado pelo pdfplumber) avisa demais sobre PDFs imperfeitos.
logging.getLogger("pdfminer").setLevel(logging.ERROR)

SEM_TEXTO = ("Não encontrei texto neste arquivo. Se for um PDF escaneado, envie um PDF com texto "
             "ou um arquivo .docx.")

# Faixa vazia mínima (em pontos) entre duas colunas, procurada no meio da página.
VAO_MINIMO = 12
MEIO = (0.25, 0.75)


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

    texto = limpar_controle(texto).strip()
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
        return "\n".join(_texto_da_pagina(pagina) for pagina in pdf.pages)


def _texto_da_pagina(pagina) -> str:
    """Lê uma coluna de cada vez quando a página tem duas (LinkedIn, Canva...)."""
    corte = _divisao_de_colunas(pagina)
    if corte is None:
        return pagina.extract_text() or ""
    esquerda = pagina.crop((0, 0, corte, pagina.height)).extract_text() or ""
    direita = pagina.crop((corte, 0, pagina.width, pagina.height)).extract_text() or ""
    return f"{esquerda}\n{direita}"


def _divisao_de_colunas(pagina) -> float | None:
    """Posição x de uma faixa vazia no meio da página, com texto dos dois lados; ou None."""
    palavras = pagina.extract_words()
    if len(palavras) < 6:
        return None
    largura = int(pagina.width) + 1
    ocupado = [False] * largura
    for p in palavras:
        for x in range(max(0, int(p["x0"])), min(largura, int(p["x1"]) + 1)):
            ocupado[x] = True

    # A faixa vazia mais larga no meio da página é o vão entre as colunas.
    inicio_faixa, melhor, maior = None, None, 0
    for x in range(int(largura * MEIO[0]), int(largura * MEIO[1])):
        if not ocupado[x]:
            inicio_faixa = x if inicio_faixa is None else inicio_faixa
            tamanho = x - inicio_faixa + 1
            if tamanho >= VAO_MINIMO and tamanho > maior:
                melhor, maior = (inicio_faixa + x) / 2, tamanho
        else:
            inicio_faixa = None
    if melhor is None:
        return None

    lado_esquerdo = sum(1 for p in palavras if p["x1"] <= melhor)
    lado_direito = len(palavras) - lado_esquerdo
    minimo = 0.15 * len(palavras)
    return melhor if lado_esquerdo >= minimo and lado_direito >= minimo else None
