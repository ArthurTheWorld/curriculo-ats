"""Melhorias pedidas depois do primeiro teste com pessoas de verdade."""
from streamlit.testing.v1 import AppTest

from curriculo_ats.modelos import ORDEM, secoes_vazias
from curriculo_ats.palavras_chave import acrescentar_habilidades
from curriculo_ats.prompt import marcador, montar_prompt
from curriculo_ats.resposta import ler_resposta

APP = "../app.py"
SECOES = secoes_vazias() | {"contato": "Ana", "experiencia": "Analista na Acme\n- Criei dashboards"}


# 1. Prompt inteiro no idioma da vaga
def test_prompt_de_vaga_em_ingles_e_todo_em_ingles():
    p = montar_prompt(SECOES, "We need a Data Engineer", "en", ["dbt"], ["Python"])
    assert "Do not invent" in p and "=== EXPERIENCE ===" in p and "=== CONTACT ===" in p
    for trecho in ("Não invente", "Reescreva", "=== EXPERIENCIA ===", "CURRÍCULO", "VAGA"):
        assert trecho not in p


def test_prompt_de_vaga_em_portugues_continua_em_portugues():
    p = montar_prompt(SECOES, "Vaga de dados", "pt", [], [])
    assert "Não invente" in p and "=== EXPERIENCIA ===" in p and "Do not invent" not in p


def test_resposta_no_formato_do_prompt_em_ingles_e_lida():
    original = secoes_vazias() | {"contato": "Ana", "resumo": "Data", "experiencia": "Acme", "formacao": "USP",
                                  "habilidades": "Python", "idiomas": "English", "outros": "Volunteer"}
    resposta = "\n".join(f"{marcador(k, 'en')}\n{v}" for k, v in original.items() if v)
    assert ler_resposta(resposta) == original
    assert set(marcador(k, "en") for k in ORDEM) == set(marcador(k, "en") for k in ORDEM)  # todos definidos


# 2. Prompt pede a grafia da vaga para o que a pessoa já tem
def test_prompt_pede_a_grafia_exata_das_palavras_encontradas():
    p = montar_prompt(SECOES, "Vaga", "pt", ["dbt"], ["Power BI", "Pipelines de dados"])
    assert "Power BI, Pipelines de dados" in p and "exatamente como" in p
    p = montar_prompt(SECOES, "Job", "en", ["dbt"], ["Power BI"])
    assert "Power BI" in p and "exactly as" in p


# 3. Checklist "Eu tenho isso": a pessoa declara, o app acrescenta
def test_acrescentar_habilidades_em_linha():
    assert acrescentar_habilidades("Python, SQL", ["dbt", "Apache Airflow"]) == "Python, SQL, dbt, Apache Airflow"


def test_acrescentar_habilidades_em_lista_com_marcador():
    assert acrescentar_habilidades("- Python\n- SQL", ["dbt"]) == "- Python\n- SQL\n- dbt"


def test_acrescentar_habilidades_vazia_e_sem_repetir():
    assert acrescentar_habilidades("", ["dbt", "AWS"]) == "dbt, AWS"
    assert acrescentar_habilidades("Python, DBT", ["dbt"]) == "Python, DBT"


def _app_com_exemplo() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.button(key="usar_exemplo").click().run()
    return at


def _nota(at: AppTest) -> int:
    return int(at.metric[0].value.rstrip("%"))


def test_marcar_tenho_isso_sobe_a_nota_e_entra_no_curriculo():
    at = _app_com_exemplo()
    antes = _nota(at)
    at.session_state["tenho"] = ["dbt", "Apache Airflow"]
    at.run()
    assert not at.exception
    assert _nota(at) > antes
    at.session_state["modo"] = "ia"
    at.run()
    assert "dbt" in at.code[0].value.split("CURRÍCULO ORIGINAL")[1]


def test_marcados_nao_sao_acusados_como_inventados():
    at = _app_com_exemplo()
    at.session_state["tenho"] = ["dbt"]
    at.session_state["modo"] = "ia"
    at.run()
    at.text_area(key="resposta").set_value("=== CONTATO ===\nAna Souza\n=== HABILIDADES ===\nPython, dbt").run()
    assert not any("dbt" in w.value for w in at.warning)


# 4. Aviso de que a nota só sobe com o que a pessoa tem
def test_aviso_explica_como_a_nota_sobe():
    at = _app_com_exemplo()
    textos = " ".join(c.value for c in at.caption)
    assert "só sobe" in textos
