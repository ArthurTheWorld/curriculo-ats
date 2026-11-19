"""Fixtures para gerar currículos de teste em memória (nada de arquivos reais)."""
import io

import docx
import pytest
from fpdf import FPDF


def docx_bytes(paragrafos: list[str]) -> bytes:
    documento = docx.Document()
    for texto in paragrafos:
        documento.add_paragraph(texto)
    saida = io.BytesIO()
    documento.save(saida)
    return saida.getvalue()


def pdf_bytes(linhas: list[str]) -> bytes:
    """PDF com as linhas como texto. Sem linhas, é uma página em branco (como um PDF escaneado)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for linha in linhas:
        pdf.cell(0, 8, linha, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


@pytest.fixture
def fazer_docx():
    return docx_bytes


@pytest.fixture
def fazer_pdf():
    return pdf_bytes
