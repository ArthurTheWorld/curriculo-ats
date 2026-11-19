"""Correções que saíram do teste de usabilidade no app real."""
from streamlit.testing.v1 import AppTest

from curriculo_ats.conferencia import perdidos, secoes_perdidas
from curriculo_ats.exportar import gerar_texto
from curriculo_ats.modelos import secoes_vazias
from curriculo_ats.palavras_chave import POUCOS_TERMOS, analisar, carregar_termos, faixa

APP = "../app.py"
TERMOS = carregar_termos()
VAGA_LOJA = ("Vaga de atendente de loja. Buscamos simpatia, pontualidade e vontade de aprender. "
             "Atendimento ao cliente, controle de estoque, operação de caixa e metas de vendas.")
RESPOSTA = ("=== CONTATO ===\nAna Souza\n=== RESUMO ===\nEngenheira de dados que aumentou a eficiência em 40%.\n"
            "=== HABILIDADES ===\nPython, SQL, dbt, Power BI, AWS")


def _app_com_exemplo() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=20).run()
    at.button(key="usar_exemplo").click().run()
    return at


def _textos(elementos) -> str:
    return " ".join(e.value for e in elementos)


# 1. Vagas fora de tecnologia
def test_dicionario_reconhece_vaga_de_comercio():
    analise = analisar("Pontual, com experiência em atendimento ao público e controle de estoque.",
                       VAGA_LOJA, TERMOS)
    assert len(analise.encontradas) + len(analise.faltando) >= POUCOS_TERMOS
    assert {"Pontualidade", "Controle de estoque"} <= set(analise.encontradas)
    assert analise.nota > 0


def test_aviso_quando_a_vaga_tem_poucas_palavras_reconhecidas():
    at = _app_com_exemplo()
    at.text_area(key="vaga").set_value("Vaga de recepcionista. Boa apresentação.").run()
    assert "Reconheci só" in _textos(at.warning)


def test_sem_aviso_de_poucas_palavras_na_vaga_de_exemplo():
    assert "Reconheci só" not in _textos(_app_com_exemplo().warning)


# 2. A IA tirou conteúdo
def test_perdidos_aponta_palavras_que_sumiram():
    assert perdidos("Python, SQL e Inglês avançado", "Python e SQL", TERMOS) == ["Inglês"]
    assert perdidos("Python", "Python, AWS", TERMOS) == []


def test_secoes_perdidas():
    original = secoes_vazias() | {"idiomas": "Inglês", "resumo": "x"}
    final = secoes_vazias() | {"resumo": "y"}
    assert secoes_perdidas(original, final) == ["idiomas"]


def test_app_avisa_o_que_a_ia_tirou():
    at = _app_com_exemplo()
    at.session_state["modo"] = "ia"
    at.run()
    at.text_area(key="resposta").set_value(RESPOSTA).run()
    avisos = _textos(at.warning)
    assert "A IA tirou" in avisos and "Inglês" in avisos and "Idiomas" in avisos


# 3, 4, 5. Textos e prompt
def test_explica_como_aplicar_a_resposta_colada():
    at = _app_com_exemplo()
    at.session_state["modo"] = "ia"
    at.run()
    assert "Ctrl+Enter" in _textos(at.caption)


def test_rotulo_do_envio_explica_o_botao():
    at = AppTest.from_file(APP, default_timeout=20).run()
    assert "arraste" in at.get("file_uploader")[0].proto.label


# 6. Referência para a nota
def test_faixa_da_nota():
    assert [faixa(n) for n in (0, 39, 40, 69, 70, 100)] == ["baixa", "baixa", "média", "média", "alta", "alta"]


def test_app_explica_a_nota():
    assert "Como guia" in _textos(_app_com_exemplo().caption)


# 7. Subida por itens inventados
def test_avisa_que_a_subida_veio_de_itens_novos():
    at = _app_com_exemplo()
    at.session_state["modo"] = "ia"
    at.run()
    at.text_area(key="resposta").set_value(RESPOSTA).run()
    assert "Parte dessa subida" in _textos(at.warning)


# 8. Confirmação da leitura e prévia
def test_confirma_que_o_curriculo_foi_lido():
    assert "Currículo lido" in _textos(_app_com_exemplo().success)


def test_gerar_texto_segue_a_ordem_e_os_titulos_do_arquivo():
    texto = gerar_texto(secoes_vazias() | {"contato": "Ana", "experiencia": "Acme", "resumo": "Dados"}, "pt")
    assert texto.index("Ana") < texto.index("RESUMO") < texto.index("EXPERIÊNCIA")


def test_previa_no_caminho_sem_ia():
    at = _app_com_exemplo()
    assert any("Prévia" in e.label for e in at.expander)


# 9. Download no caminho com IA antes de colar
def test_explica_por_que_o_download_ainda_nao_aparece():
    at = _app_com_exemplo()
    at.session_state["modo"] = "ia"
    at.run()
    assert "para liberar o download" in _textos(at.info)
