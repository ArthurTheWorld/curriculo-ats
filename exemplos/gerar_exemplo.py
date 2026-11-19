"""Gera exemplos/curriculo_exemplo.docx: um currículo fictício para testar o app.

    python exemplos/gerar_exemplo.py
"""
from pathlib import Path

import docx

PASTA = Path(__file__).resolve().parent

CURRICULO = [
    ("Ana Souza", None),
    ("São Paulo, SP · ana.souza@email.com · (11) 91234-5678", None),
    ("linkedin.com/in/ana-souza-exemplo", None),
    ("Resumo", "titulo"),
    ("Analista de dados com 3 anos de experiência transformando dados de vendas em relatórios e "
     "indicadores para as áreas comercial e financeira.", None),
    ("Experiência Profissional", "titulo"),
    ("Analista de Dados · Loja Exemplo S.A. · mar/2023 – atual", None),
    ("- Criei dashboards em Power BI usados semanalmente pela diretoria comercial.", None),
    ("- Automatizei relatórios de vendas com Python e SQL, reduzindo 6 horas de trabalho manual por semana.", None),
    ("- Organizei a base de clientes em um modelo de dados único no SQL Server.", None),
    ("Assistente de Dados · Empresa Fictícia Ltda. · jan/2022 – fev/2023", None),
    ("- Mantive planilhas de indicadores em Excel e apoiei a migração para o Power BI.", None),
    ("Formação Acadêmica", "titulo"),
    ("Bacharelado em Estatística · Universidade Exemplo · 2018 – 2021", None),
    ("Habilidades", "titulo"),
    ("Excel, SQL, Power BI, Python, SQL Server, Estatística, Comunicação", None),
    ("Idiomas", "titulo"),
    ("Português: nativo", None),
    ("Inglês: intermediário", None),
]


def gerar() -> Path:
    documento = docx.Document()
    for texto, tipo in CURRICULO:
        paragrafo = documento.add_paragraph(texto)
        if tipo == "titulo":
            paragrafo.runs[0].bold = True
    destino = PASTA / "curriculo_exemplo.docx"
    documento.save(destino)
    return destino


if __name__ == "__main__":
    print(f"Gerado: {gerar()}")
