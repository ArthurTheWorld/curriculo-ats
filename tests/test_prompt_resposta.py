import pytest

from curriculo_ats.modelos import ORDEM, secoes_vazias
from curriculo_ats.prompt import montar_prompt
from curriculo_ats.resposta import RespostaInvalida, ler_resposta


def test_prompt_tem_regras_curriculo_vaga_e_formato():
    p = montar_prompt({"contato": "Ana", "experiencia": "Empresa X"}, "Vaga de dados", "pt", ["dbt"])
    assert "Ana" in p and "Empresa X" in p and "Vaga de dados" in p
    assert "Não invente" in p and "dbt" in p
    assert "=== EXPERIENCIA ===" in p


def test_prompt_em_portugues_e_sem_faltando():
    p = montar_prompt({"contato": "Ana"}, "Vaga", "pt", [])
    assert "português do Brasil" in p and "English" not in p


def test_ida_e_volta():
    original = secoes_vazias() | {"contato": "Ana", "resumo": "Dados", "experiencia": "Empresa X\n- Fiz pipelines"}
    resposta = "\n".join(f"=== {k.upper()} ===\n{v}" for k, v in original.items() if v)
    assert ler_resposta(resposta) == original


def test_resposta_com_markdown_e_acentos():
    texto = "```\n**=== Experiência ===**\nEmpresa X\n### === RESUMO ===\nDados\n```"
    s = ler_resposta(texto)
    assert s["experiencia"] == "Empresa X" and s["resumo"] == "Dados"


def test_resposta_com_texto_antes_dos_marcadores_e_ignorado():
    s = ler_resposta("Claro! Aqui está o currículo:\n=== CONTATO ===\nAna\n=== HABILIDADES ===\nPython")
    assert s["contato"] == "Ana" and s["habilidades"] == "Python"


def test_resposta_sem_marcadores_usa_titulos():
    s = ler_resposta("Ana\nProfessional Experience\nEmpresa X\nSkills\nPython")
    assert s["experiencia"] == "Empresa X" and s["habilidades"] == "Python"


def test_resposta_vazia_ou_irreconhecivel():
    with pytest.raises(RespostaInvalida):
        ler_resposta("   ")
    with pytest.raises(RespostaInvalida):
        ler_resposta("linha um\nlinha dois\nlinha três\nlinha quatro")


def test_chaves_do_resultado_sao_as_de_ordem():
    assert set(ler_resposta("=== RESUMO ===\nDados")) == set(ORDEM)
