from streamlit.testing.v1 import AppTest

APP = "../app.py"  # caminho relativo a este arquivo de teste


def _com_exemplo() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.button(key="usar_exemplo").click().run()
    return at


def test_app_abre_sem_erro():
    at = AppTest.from_file(APP, default_timeout=15).run()
    assert not at.exception
    assert not at.metric  # sem currículo e vaga, ainda não há nota


def test_exemplo_gera_nota_e_downloads():
    at = _com_exemplo()
    assert not at.exception
    assert at.metric[0].value.endswith("%")
    assert at.text_area(key="secao_experiencia").value
    assert len(at.get("download_button")) == 2


def test_modo_ia_mostra_prompt_e_le_resposta():
    at = _com_exemplo()
    at.session_state["modo"] = "ia"
    at.run()
    assert not at.exception
    assert "Não invente" in at.code[0].value
    assert not at.get("download_button")  # só depois de colar a resposta

    at.text_area(key="resposta").set_value(
        "=== CONTATO ===\nAna Souza\n=== EXPERIENCIA ===\nEmpresa X\n- Reduzi custos em 99%"
    ).run()
    assert not at.exception
    assert any("99%" in w.value for w in at.warning)
    assert len(at.get("download_button")) == 2


def test_resposta_ilegivel_mostra_erro():
    at = _com_exemplo()
    at.session_state["modo"] = "ia"
    at.run()
    at.text_area(key="resposta").set_value("um\ndois\ntrês\nquatro").run()
    assert not at.exception
    assert at.error and "=== SEÇÃO ===" in at.error[0].value
