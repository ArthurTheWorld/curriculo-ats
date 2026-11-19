"""Monta o prompt do modo "copiar e colar" para qualquer chat de IA gratuito."""
from curriculo_ats.modelos import ORDEM, Secoes


def marcador(chave: str) -> str:
    """'experiencia' → '=== EXPERIENCIA ==='."""
    return f"=== {chave.upper()} ==="


IDIOMAS = {"pt": "português do Brasil", "en": "English"}

_DESCRICAO = {
    "contato": "nome, cidade, e-mail, telefone, LinkedIn, GitHub (uma informação por linha)",
    "resumo": "3 a 4 linhas sobre quem a pessoa é e o que entrega",
    "habilidades": "lista separada por vírgulas",
    "experiencia": "para cada emprego: cargo, empresa e período na primeira linha; depois conquistas, uma por linha começando com '- '",
    "projetos": "nome do projeto e uma linha do que foi feito, começando com '- '",
    "formacao": "curso, instituição e período",
    "certificacoes": "uma por linha",
    "idiomas": "idioma e nível, um por linha",
    "outros": "o que não couber nas seções acima",
}


def montar_prompt(secoes: Secoes, vaga: str, idioma: str, faltando: list[str]) -> str:
    lingua = IDIOMAS.get(idioma, IDIOMAS["pt"])
    curriculo = "\n\n".join(
        f"{marcador(chave)}\n{secoes[chave].strip()}"
        for chave in ORDEM if secoes.get(chave, "").strip()
    )
    formato = "\n".join(f"{marcador(chave)}\n({_DESCRICAO[chave]})" for chave in ORDEM)
    aviso_faltando = (
        "Estas palavras-chave da vaga NÃO aparecem no currículo: " + ", ".join(faltando) + ". "
        "Use alguma delas somente se o currículo deixar claro que a pessoa tem essa experiência "
        "(por exemplo, com outro nome). Caso contrário, deixe de fora."
        if faltando else ""
    )

    return f"""Você é especialista em recrutamento e em currículos compatíveis com sistemas ATS.

Reescreva o currículo abaixo para a vaga informada, seguindo TODAS as regras:

1. Não invente nada. Não acrescente empresas, cargos, datas, números, métricas, tecnologias, cursos ou certificações que não estejam no currículo original.
2. Mantenha exatamente as empresas, os cargos, as datas e a formação.
3. Você pode reescrever frases para deixá-las mais claras, objetivas e orientadas a resultado, e usar os termos da vaga onde eles descrevem algo que a pessoa realmente fez.
4. {aviso_faltando or "Não acrescente palavras-chave que a pessoa não tenha."}
5. Escreva o currículo inteiro em {lingua}.
6. Responda SOMENTE com o currículo, no formato abaixo: cada seção começa com o marcador exatamente como está (=== NOME ===), na ordem indicada. Omita seções sem conteúdo. Não use markdown, negrito, tabelas nem emojis.

FORMATO DA RESPOSTA:
{formato}

VAGA:
{vaga.strip()}

CURRÍCULO ORIGINAL:
{curriculo}
"""
