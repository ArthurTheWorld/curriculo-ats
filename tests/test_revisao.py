"""Casos encontrados na revisão final. Cada teste reproduz um problema real."""
import io

import docx
from fpdf import FPDF

from curriculo_ats.conferencia import Novidade, conferir
from curriculo_ats.estado import aplicar_upload
from curriculo_ats.exportar import gerar_docx
from curriculo_ats.leitura import extrair_texto
from curriculo_ats.modelos import secoes_vazias, somente_contato
from curriculo_ats.palavras_chave import Termo, analisar, carregar_termos, extrair_termos, priorizar_habilidades
from curriculo_ats.resposta import ler_resposta
from curriculo_ats.secoes import dividir_secoes


# 1. Marcadores traduzidos ou por extenso na resposta da IA
def test_marcadores_em_ingles_e_por_extenso():
    s = ler_resposta("=== CONTACT ===\nJohn Doe\n=== SUMMARY ===\nData eng\n"
                     "=== EXPERIÊNCIA PROFISSIONAL ===\nAcme 2020\n=== SKILLS ===\nPython")
    assert s["contato"] == "John Doe" and s["resumo"] == "Data eng"
    assert s["experiencia"] == "Acme 2020" and s["habilidades"] == "Python" and s["outros"] == ""


# 2. Subtítulos dentro de um emprego não quebram a seção de experiência
def test_subtitulos_dentro_da_experiencia():
    texto = ("Ana\nExperiência\nAnalista na Acme\nAtividades:\n- Criei dashboards\n"
             "Tecnologias:\nPython, SQL\nAnalista na Beta")
    s = dividir_secoes(texto)
    assert "Criei dashboards" in s["experiencia"] and "Analista na Beta" in s["experiencia"]
    assert "Python, SQL" in s["experiencia"] and s["outros"] == "" and s["habilidades"] == ""


# 3. Habilidades por categoria e listas com marcadores
def test_priorizar_mantem_categorias():
    texto = "Linguagens: Python, SQL\nFerramentas: Power BI, Excel"
    assert priorizar_habilidades(texto, ["Power BI"], carregar_termos()) == \
        "Ferramentas: Power BI, Excel\nLinguagens: Python, SQL"


def test_priorizar_lista_com_marcadores_e_sinonimo():
    texto = "- Python\n- PowerBI\n- Excel, Word"
    assert priorizar_habilidades(texto, ["Power BI"], carregar_termos()) == "- PowerBI\n- Python\n- Excel, Word"


# 4. Termo dentro de outro maior também conta como presente no currículo
def test_termo_aninhado_conta_como_presente():
    termos = carregar_termos()
    a = analisar("AWS Lambda, SQL Server, React Native, Azure DevOps", "Vaga: AWS, SQL, React e Azure", termos)
    assert a.nota == 100 and a.faltando == []


def test_conferencia_nao_acusa_termo_aninhado():
    termos = carregar_termos()
    assert conferir("Usei AWS Lambda", "Usei AWS e AWS Lambda", termos) == []


# 5. Palavras comuns não viram palavras-chave
def test_sem_falsos_positivos_em_prosa():
    termos = carregar_termos()
    ingles = ("We have a solid team, the rest of the team is swift and lean, with elastic hours, "
              "a notion of glue code, a spark of creativity and express delivery.")
    portugues = "Trabalho em um ambiente ágil, na lua, perto do posto Shell, num nó da rede."
    assert extrair_termos(ingles, termos) == []
    assert extrair_termos(portugues, termos) == []


def test_formas_exatas_continuam_reconhecidas():
    termos = carregar_termos()
    assert extrair_termos("APIs REST, Spark, Swift, princípios SOLID, Node e Express", termos) == \
        ["APIs REST", "Apache Spark", "Swift", "SOLID", "Node.js", "Express"]


# 6. PDF em duas colunas (exportação do LinkedIn, Canva)
def _pdf_duas_colunas() -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    esquerda = ["Principais competencias", "Python", "SQL", "Idiomas", "Ingles"]
    direita = ["Resumo", "Trabalho com dados ha 5 anos", "Experiencia", "Analista na Acme", "2020 - 2024"]
    for linha, (e, d) in enumerate(zip(esquerda, direita)):
        pdf.text(15, 20 + 8 * linha, e)
        pdf.text(90, 20 + 8 * linha, d)
    return bytes(pdf.output())


def test_pdf_duas_colunas_le_uma_coluna_de_cada_vez():
    texto = extrair_texto("linkedin.pdf", _pdf_duas_colunas())
    linhas = texto.splitlines()
    assert linhas[:5] == ["Principais competencias", "Python", "SQL", "Idiomas", "Ingles"]
    s = dividir_secoes(texto)
    assert "Python" in s["habilidades"] and "Analista na Acme" in s["experiencia"]


def test_somente_contato_detecta_divisao_que_falhou():
    assert somente_contato(secoes_vazias() | {"contato": "tudo aqui"})
    assert not somente_contato(secoes_vazias() | {"contato": "Ana", "resumo": "x"})


# 8. Um segundo arquivo ilegível não deixa o currículo anterior "valendo" escondido
def test_upload_ilegivel_limpa_o_curriculo_anterior(fazer_docx, fazer_pdf):
    estado: dict = {}
    assert aplicar_upload(estado, "a.docx", fazer_docx(["Ana", "Resumo", "Dados"]), "id-a") is None
    assert estado["carregado"] and estado["secao_resumo"] == "Dados"

    erro = aplicar_upload(estado, "b.pdf", fazer_pdf([]), "id-b")
    assert erro and "PDF com texto" in erro
    assert not estado.get("carregado") and not estado.get("secao_resumo")


def test_mesmo_arquivo_nao_e_relido(fazer_docx):
    estado: dict = {}
    aplicar_upload(estado, "a.docx", fazer_docx(["Ana", "Resumo", "Dados"]), "id-a")
    estado["secao_resumo"] = "editado pela pessoa"
    aplicar_upload(estado, "a.docx", fazer_docx(["Ana", "Resumo", "Dados"]), "id-a")
    assert estado["secao_resumo"] == "editado pela pessoa"


# Caracteres de controle (comuns em PDFs gerados pelo Word) não quebram o .docx
def test_caracteres_de_controle_nao_quebram_o_docx(fazer_docx):
    dados = gerar_docx(secoes_vazias() | {"contato": "a\x0bb\x00c", "resumo": "x\x0cy"}, "pt")
    texto = "\n".join(p.text for p in docx.Document(io.BytesIO(dados)).paragraphs)
    assert "a" in texto and "\x00" not in texto


def test_leitura_remove_caracteres_de_controle(fazer_docx):
    assert "\x0b" not in ler_resposta("=== RESUMO ===\nDados\x0bmais")["resumo"]


def test_nome_aninhado_nao_usa_sinonimo_sozinho():
    """Sanidade: termo exato não casa em minúsculas, mas o nome canônico continua valendo."""
    termos = [Termo("Apache Spark", ("PySpark",), "dados", exatos=("Spark",))]
    assert extrair_termos("spark de ideias", termos) == []
    assert extrair_termos("Spark e pyspark", termos) == ["Apache Spark"]
