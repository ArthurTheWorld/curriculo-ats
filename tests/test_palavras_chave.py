from curriculo_ats.palavras_chave import (
    Termo, analisar, carregar_termos, extrair_termos, priorizar_habilidades, termos_extras,
)

TERMOS = [
    Termo("Java", (), "linguagem"), Termo("JavaScript", ("JS",), "linguagem"),
    Termo("C++", (), "linguagem"), Termo("C#", (), "linguagem"), Termo(".NET", ("dotnet",), "framework"),
    Termo("Node.js", ("NodeJS",), "framework"), Termo("Gestão de projetos", (), "metodologia"),
    Termo("React", (), "framework"), Termo("Power BI", ("PowerBI",), "ferramenta"),
]


def test_simbolos_sinonimos_e_acentos():
    assert extrair_termos("C++, C#, dotnet, NodeJS e gestao de projetos", TERMOS) == \
        ["C++", "C#", ".NET", "Node.js", "Gestão de projetos"]


def test_sem_falso_positivo_de_substring():
    assert extrair_termos("JavaScript e React", TERMOS) == ["JavaScript", "React"]


def test_termo_no_fim_de_frase_com_ponto():
    assert extrair_termos("Experiência com Java.", TERMOS) == ["Java"]


def test_analise_nota_e_faltando():
    a = analisar("Sei Java e PowerBI", "Vaga: Java, Power BI, React e C#", TERMOS)
    assert a.encontradas == ["Java", "Power BI"]
    assert a.faltando == ["React", "C#"]
    assert a.nota == 50


def test_sinonimo_repetido_nao_vira_termo_extra_duplicado():
    termos = [Termo("Apache Spark", ("Spark",), "dados")]
    a = analisar("Sei Spark", "Usamos Spark no dia a dia. O Spark roda na nuvem.", termos)
    assert a.encontradas == ["Apache Spark"] and a.faltando == []


def test_vaga_sem_termos_da_nota_zero_sem_erro():
    assert analisar("x", "texto sem nada técnico", TERMOS).nota == 0


def test_termos_extras_repetidos_da_vaga():
    vaga = "Experiência com Looker. O Looker é central. Também Airbyte."
    assert termos_extras(vaga, []) == ["Looker"]


def test_termos_extras_ignora_os_ja_encontrados():
    assert termos_extras("Usamos React. React no front.", ["React"]) == []


def test_priorizar_habilidades_nao_acrescenta():
    assert priorizar_habilidades("Excel, Python, SQL", ["SQL", "Python", "Rust"], TERMOS) == "SQL, Python, Excel"


def test_priorizar_habilidades_vazia():
    assert priorizar_habilidades("", ["SQL"], TERMOS) == ""


def test_dicionario_real_carrega_e_nao_tem_duplicados():
    termos = carregar_termos()
    nomes = [t.nome.casefold() for t in termos]
    assert len(termos) >= 200 and len(nomes) == len(set(nomes))


def test_dicionario_real_sem_falsos_positivos_em_texto_comum():
    texto = "Sou uma pessoa tranquila, gosto de aprender e trabalhar em equipe com foco no cliente."
    assert extrair_termos(texto, carregar_termos()) == []


def test_competencias_comportamentais_sao_reconhecidas():
    # De propósito: vagas fora de tecnologia pedem isso, e o currículo deve poder mostrar.
    assert extrair_termos("Sou organizada, pontual e proativa.", carregar_termos()) ==         ["Organização", "Pontualidade", "Proatividade"]
