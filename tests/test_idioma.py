from curriculo_ats.idioma import TITULOS, detectar_idioma
from curriculo_ats.modelos import ORDEM


def test_portugues():
    assert detectar_idioma("Buscamos pessoa engenheira de dados com experiência em Python para atuar no time") == "pt"


def test_ingles():
    assert detectar_idioma("We are looking for a data engineer with experience in Python to join the team") == "en"


def test_vazio_e_pt():
    assert detectar_idioma("") == "pt"


def test_titulos_cobrem_todas_as_secoes():
    for lingua in ("pt", "en"):
        assert set(TITULOS[lingua]) == set(ORDEM) - {"contato"}
    assert TITULOS["en"]["experiencia"] == "Professional Experience"
    assert TITULOS["pt"]["experiencia"] == "Experiência Profissional"
