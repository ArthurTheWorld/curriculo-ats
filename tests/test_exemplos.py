from pathlib import Path

from curriculo_ats.exportar import gerar_pdf
from curriculo_ats.leitura import extrair_texto
from curriculo_ats.palavras_chave import analisar, carregar_termos
from curriculo_ats.secoes import dividir_secoes

EXEMPLOS = Path(__file__).resolve().parent.parent / "exemplos"


def test_exemplo_de_ponta_a_ponta():
    texto = extrair_texto("cv.docx", (EXEMPLOS / "curriculo_exemplo.docx").read_bytes())
    secoes = dividir_secoes(texto)
    a = analisar(texto, (EXEMPLOS / "vaga_exemplo.txt").read_text(encoding="utf-8"), carregar_termos())
    assert secoes["experiencia"] and secoes["formacao"]
    assert "dbt" in a.faltando and "Python" in a.encontradas
    assert gerar_pdf(secoes, "pt").startswith(b"%PDF")


def test_scripts_preferem_versoes_testadas_do_python():
    """O Python mais novo pode não ter pacotes prontos ainda (ex.: pyyaml no 3.15)."""
    raiz = EXEMPLOS.parent
    bat = (raiz / "iniciar.bat").read_text(encoding="utf-8")
    sh = (raiz / "iniciar.sh").read_text(encoding="utf-8")
    assert bat.index("3.13") < bat.index("py -3 ")
    assert sh.index("python3.13") < sh.index("python3 ")


def test_scripts_de_inicio_existem_e_chamam_o_app():
    raiz = EXEMPLOS.parent
    for nome in ("iniciar.bat", "iniciar.sh"):
        conteudo = (raiz / nome).read_text(encoding="utf-8")
        assert "streamlit run app.py" in conteudo and "requirements.txt" in conteudo
