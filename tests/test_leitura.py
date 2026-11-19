import pytest

from curriculo_ats.leitura import ArquivoIlegivel, extrair_texto


def test_le_docx(fazer_docx):
    assert extrair_texto("cv.DOCX", fazer_docx(["Ana Souza", "Experiência"])) == "Ana Souza\nExperiência"


def test_le_pdf_com_texto(fazer_pdf):
    texto = extrair_texto("cv.pdf", fazer_pdf(["Ana Souza", "Python e SQL"]))
    assert "Ana Souza" in texto and "Python e SQL" in texto


def test_pdf_sem_texto_da_erro_claro(fazer_pdf):
    with pytest.raises(ArquivoIlegivel, match="PDF com texto ou um arquivo .docx"):
        extrair_texto("scan.pdf", fazer_pdf([]))


def test_formato_nao_suportado():
    with pytest.raises(ArquivoIlegivel, match="PDF ou .docx"):
        extrair_texto("cv.odt", b"x")


def test_arquivo_corrompido():
    with pytest.raises(ArquivoIlegivel):
        extrair_texto("cv.docx", b"nao e um zip")
