"""Gera o currículo final em .docx e PDF no layout que sistemas ATS leem bem.

Layout ATS: uma coluna, fonte padrão, títulos em texto simples, marcadores simples.
Sem tabelas, caixas de texto, imagens, ícones, cabeçalho/rodapé ou cores.
"""
import io
import re

import docx
from docx.shared import Cm, Pt
from fpdf import FPDF

from curriculo_ats.idioma import TITULOS
from curriculo_ats.modelos import ORDEM, Secoes, normalizar

_MARCADOR = re.compile(r"^\s*[-*•]\s+")


def _secoes_com_conteudo(secoes: Secoes) -> list[tuple[str, list[str]]]:
    resultado = []
    for chave in ORDEM:
        if chave == "contato":
            continue
        linhas = [linha.strip() for linha in secoes.get(chave, "").splitlines() if linha.strip()]
        if linhas:
            resultado.append((chave, linhas))
    return resultado


def _contato(secoes: Secoes) -> list[str]:
    return [linha.strip() for linha in secoes.get("contato", "").splitlines() if linha.strip()]


def _titulo(chave: str, idioma: str) -> str:
    return TITULOS.get(idioma, TITULOS["pt"])[chave].upper()


# --- .docx ------------------------------------------------------------------------

def gerar_docx(secoes: Secoes, idioma: str) -> bytes:
    documento = docx.Document()
    normal = documento.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10.5)
    for secao in documento.sections:
        secao.top_margin = secao.bottom_margin = Cm(2)
        secao.left_margin = secao.right_margin = Cm(2)

    contato = _contato(secoes)
    if contato:
        nome = documento.add_paragraph().add_run(contato[0])
        nome.bold = True
        nome.font.size = Pt(14)
        for linha in contato[1:]:
            documento.add_paragraph(linha).runs[0].font.size = Pt(10)

    for chave, linhas in _secoes_com_conteudo(secoes):
        titulo = documento.add_paragraph()
        titulo.paragraph_format.space_before = Pt(10)
        run = titulo.add_run(_titulo(chave, idioma))
        run.bold = True
        run.font.size = Pt(11)
        for linha in linhas:
            if _MARCADOR.match(linha):
                documento.add_paragraph(_MARCADOR.sub("", linha), style="List Bullet")
            else:
                documento.add_paragraph(linha)

    saida = io.BytesIO()
    documento.save(saida)
    return saida.getvalue()


# --- PDF --------------------------------------------------------------------------

_TROCAS = str.maketrans({
    "–": "-", "—": "-", "‐": "-", "‑": "-", "“": '"', "”": '"', "„": '"', "‘": "'", "’": "'",
    "•": "-", "…": "...", "×": "x", "→": "->", " ": " ", "​": "",
})


def _latin1(texto: str) -> str:
    """As fontes padrão do PDF só têm latin-1: troca o que dá e descarta o resto (ex.: emoji)."""
    return texto.translate(_TROCAS).encode("latin-1", errors="ignore").decode("latin-1")


def gerar_pdf(secoes: Secoes, idioma: str) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    def escrever(texto: str, tamanho: float, negrito: bool = False, recuo: float = 0) -> None:
        pdf.set_font("Helvetica", "B" if negrito else "", tamanho)
        pdf.set_x(pdf.l_margin + recuo)
        pdf.multi_cell(0, tamanho * 0.5, _latin1(texto), new_x="LMARGIN", new_y="NEXT")

    contato = _contato(secoes)
    if contato:
        escrever(contato[0], 14, negrito=True)
        for linha in contato[1:]:
            escrever(linha, 10)

    for chave, linhas in _secoes_com_conteudo(secoes):
        pdf.ln(3)
        escrever(_titulo(chave, idioma), 11, negrito=True)
        for linha in linhas:
            if _MARCADOR.match(linha):
                escrever("- " + _MARCADOR.sub("", linha), 10.5, recuo=4)
            else:
                escrever(linha, 10.5)

    return bytes(pdf.output())


# --- nome do arquivo --------------------------------------------------------------

def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalizar(texto)).strip("-")


def nome_arquivo(secoes: Secoes, empresa: str | None, extensao: str) -> str:
    contato = _contato(secoes)
    partes = [_slug(p) for p in (contato[0] if contato else "", empresa or "") if p]
    partes = [p for p in partes if p]
    base = "-".join(["curriculo", *partes]) if partes else "curriculo-ats"
    return f"{base}.{extensao}"
