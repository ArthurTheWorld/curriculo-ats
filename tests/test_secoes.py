from curriculo_ats.modelos import ORDEM
from curriculo_ats.secoes import dividir_secoes, identificar_titulo


def test_titulos_pt_e_en():
    assert identificar_titulo("EXPERIÊNCIA PROFISSIONAL") == "experiencia"
    assert identificar_titulo("Work Experience:") == "experiencia"
    assert identificar_titulo("Formação Acadêmica") == "formacao"
    assert identificar_titulo("Skills") == "habilidades"
    assert identificar_titulo("Trabalhei com experiência em vendas por 3 anos") is None


def test_divide_e_contato_antes_do_primeiro_titulo():
    s = dividir_secoes("Ana Souza\nana@x.com\nResumo\nEngenheira de dados\nHabilidades\nPython, SQL")
    assert s["contato"] == "Ana Souza\nana@x.com"
    assert s["resumo"] == "Engenheira de dados"
    assert s["habilidades"] == "Python, SQL"
    assert set(s) == set(ORDEM)


def test_titulo_desconhecido_vai_para_outros():
    s = dividir_secoes("Ana\nResumo\nTexto\nVoluntariado\nONG X")
    assert s["outros"] == "ONG X" and s["resumo"] == "Texto"


def test_sem_nenhum_titulo():
    s = dividir_secoes("Ana Souza\nPython SQL dbt")
    assert s["contato"] == "Ana Souza\nPython SQL dbt"


def test_mesma_secao_repetida_e_concatenada():
    s = dividir_secoes("Ana\nExperiência\nEmpresa A\nEducation\nUSP\nExperience\nEmpresa B")
    assert s["experiencia"] == "Empresa A\nEmpresa B"
