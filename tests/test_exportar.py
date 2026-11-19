import io

import docx

from curriculo_ats.exportar import gerar_docx, gerar_pdf, nome_arquivo
from curriculo_ats.leitura import extrair_texto
from curriculo_ats.modelos import secoes_vazias

SECOES = secoes_vazias() | {
    "contato": "Ana Souza\nana@x.com",
    "experiencia": "Empresa X\n- Fiz pipelines",
    "habilidades": "Python, SQL",
}


def test_docx_ordem_titulos_e_sem_tabelas_ou_imagens():
    dados = gerar_docx(SECOES, "en")
    texto = extrair_texto("cv.docx", dados)
    assert texto.index("SKILLS") < texto.index("PROFESSIONAL EXPERIENCE")
    assert "PROJECTS" not in texto  # seção vazia omitida
    doc = docx.Document(io.BytesIO(dados))
    assert not doc.tables and not doc.inline_shapes
    assert not any(p.text for s in doc.sections for p in s.header.paragraphs)


def test_docx_marcadores_viram_lista():
    doc = docx.Document(io.BytesIO(gerar_docx(SECOES, "pt")))
    item = next(p for p in doc.paragraphs if "Fiz pipelines" in p.text)
    assert item.style.name == "List Bullet" and not item.text.startswith("-")


def test_pdf_legivel():
    texto = extrair_texto("cv.pdf", gerar_pdf(SECOES, "pt"))
    assert "Ana Souza" in texto and "EXPERIÊNCIA PROFISSIONAL" in texto and "Fiz pipelines" in texto


def test_pdf_com_caracteres_fora_do_latin1():
    s = SECOES | {"resumo": "Dados – “ETL” • 10× mais rápido… 🚀"}
    texto = extrair_texto("cv.pdf", gerar_pdf(s, "pt"))
    assert "ETL" in texto and "mais rápido" in texto


def test_pdf_com_linha_longa_sem_espacos():
    s = SECOES | {"contato": "Ana\nhttps://www.linkedin.com/in/" + "a" * 150}
    assert gerar_pdf(s, "pt").startswith(b"%PDF")


def test_nome_arquivo():
    assert nome_arquivo(SECOES, "Nubank S.A.", "pdf") == "curriculo-ana-souza-nubank-s-a.pdf"
    assert nome_arquivo(secoes_vazias(), None, "docx") == "curriculo-ats.docx"
