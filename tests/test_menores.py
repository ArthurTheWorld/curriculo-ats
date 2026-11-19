"""Problemas menores encontrados na revisão final. Cada teste reproduz um deles."""
import time
from pathlib import Path

from streamlit.testing.v1 import AppTest

from curriculo_ats.conferencia import conferir
from curriculo_ats.exportar import gerar_docx, gerar_pdf, nome_arquivo
from curriculo_ats.leitura import extrair_texto
from curriculo_ats.modelos import secoes_vazias
from curriculo_ats.palavras_chave import analisar, carregar_termos, termos_extras
from curriculo_ats.resposta import ler_resposta

RAIZ = Path(__file__).resolve().parent.parent


# 1. Letras fora do latin-1 não somem do PDF
def test_pdf_mantem_letras_de_outros_alfabetos_latinos():
    s = secoes_vazias() | {"contato": "Łukasz Wiśniewski", "resumo": "Pretensão €50k\n● Python\n▪ SQL"}
    texto = extrair_texto("cv.pdf", gerar_pdf(s, "pt"))
    assert "Lukasz Wisniewski" in texto
    assert "EUR50k" in texto or "EUR 50k" in texto
    assert "- Python" in texto and "- SQL" in texto


# 2. Nomes próprios da vaga não viram palavra-chave
def test_extras_ignoram_lugares_beneficios_e_empresa():
    vaga = ("A Acme busca pessoa para São Paulo. Benefícios: Vale Refeição e Vale Transporte. "
            "Na Acme você usa Looker. O dashboard é no Looker. Escritório em São Paulo.")
    assert termos_extras(vaga, [], ignorar=["Acme"]) == ["Looker"]


def test_analise_ignora_a_empresa():
    vaga = "Na Acme usamos Python. A Acme é legal."
    assert "Acme" not in analisar("Python", vaga, carregar_termos(), ignorar=["Acme"]).faltando


# 3. Contato antes do primeiro marcador não se perde
def test_contato_antes_do_primeiro_marcador_vai_para_contato():
    s = ler_resposta("Luiz Arthur\nluiz@x.com\n=== RESUMO ===\nDev")
    assert s["contato"] == "Luiz Arthur\nluiz@x.com" and s["resumo"] == "Dev"


def test_conversa_do_chat_antes_do_marcador_continua_ignorada():
    s = ler_resposta("Claro! Aqui está o currículo:\n=== RESUMO ===\nDev")
    assert s["contato"] == ""
    s = ler_resposta("Claro! Aqui está:\n=== CONTATO ===\nAna\n=== RESUMO ===\nDev")
    assert s["contato"] == "Ana"


# 4. Datas reescritas não são acusadas como números novos
def test_datas_reformatadas_nao_sao_novidade():
    assert conferir("Jan 2019 - Dez 2020", "01/2019 - 12/2020", carregar_termos()) == []


def test_numero_novo_ao_lado_de_data_continua_acusado():
    novidades = conferir("Jan 2019", "01/2019: reduzi 30%", carregar_termos())
    assert [n.valor for n in novidades] == ["30%"]


# 5. Vagas muito longas não deixam o app lento
def test_vaga_muito_longa_e_rapida():
    base = (RAIZ / "exemplos" / "vaga_exemplo.txt").read_text(encoding="utf-8")
    termos = carregar_termos()
    analisar("aquecimento", "Python", termos)
    inicio = time.perf_counter()
    analisar(base, base * 200, termos)
    assert time.perf_counter() - inicio < 0.8


# 6. A versão mínima do Streamlit é a que o código usa
def test_versao_minima_do_streamlit():
    linha = next(l for l in (RAIZ / "requirements.txt").read_text().splitlines() if l.startswith("streamlit"))
    assert linha == "streamlit>=1.67"


# 7. Nome do arquivo segue o design; "Curriculum Vitae" não vira nome
def test_nome_arquivo_sem_empresa_usa_vaga():
    s = secoes_vazias() | {"contato": "Ana Souza"}
    assert nome_arquivo(s, "", "pdf") == "curriculo-ana-souza-vaga.pdf"


def test_titulo_curriculum_vitae_nao_vira_nome():
    s = secoes_vazias() | {"contato": "Curriculum Vitae\nAna Souza\nana@x.com", "resumo": "Dados"}
    assert nome_arquivo(s, "Acme", "pdf") == "curriculo-ana-souza-acme.pdf"
    texto = extrair_texto("cv.docx", gerar_docx(s, "pt"))
    assert texto.splitlines()[0] == "Ana Souza"


# 8. A resposta colada não some ao trocar de modo
def test_resposta_sobrevive_a_troca_de_modo():
    at = AppTest.from_file("../app.py", default_timeout=15).run()
    at.button(key="usar_exemplo").click().run()
    at.session_state["modo"] = "ia"
    at.run()
    at.text_area(key="resposta").set_value("=== CONTATO ===\nAna\n=== RESUMO ===\nDados").run()
    at.session_state["modo"] = "sem_ia"
    at.run()
    at.session_state["modo"] = "ia"
    at.run()
    assert not at.exception
    assert "Dados" in at.text_area(key="resposta").value


# 9. iniciar.sh explica o que instalar quando falta o python3-venv
def test_iniciar_sh_explica_python3_venv():
    assert "sudo apt install python3-venv" in (RAIZ / "iniciar.sh").read_text(encoding="utf-8")
