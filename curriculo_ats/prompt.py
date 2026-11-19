"""Monta o prompt do modo "copiar e colar" para qualquer chat de IA gratuito.

O prompt inteiro (instruções, marcadores e descrições) sai no idioma da vaga. Misturar
instruções em português com um pedido de resposta em inglês confunde as IAs mais simples.
"""
from curriculo_ats.modelos import ORDEM, Secoes

_MARCADORES = {
    "pt": {
        "contato": "CONTATO", "resumo": "RESUMO", "habilidades": "HABILIDADES",
        "experiencia": "EXPERIENCIA", "projetos": "PROJETOS", "formacao": "FORMACAO",
        "certificacoes": "CERTIFICACOES", "idiomas": "IDIOMAS", "outros": "OUTROS",
    },
    "en": {
        "contato": "CONTACT", "resumo": "SUMMARY", "habilidades": "SKILLS",
        "experiencia": "EXPERIENCE", "projetos": "PROJECTS", "formacao": "EDUCATION",
        "certificacoes": "CERTIFICATIONS", "idiomas": "LANGUAGES", "outros": "OTHER",
    },
}

_DESCRICOES = {
    "pt": {
        "contato": "nome, cidade, e-mail, telefone, LinkedIn, GitHub (uma informação por linha)",
        "resumo": "3 a 4 linhas sobre quem a pessoa é e o que entrega",
        "habilidades": "lista separada por vírgulas",
        "experiencia": "para cada emprego: cargo, empresa e período na primeira linha; depois conquistas, "
                       "uma por linha começando com '- '",
        "projetos": "nome do projeto e uma linha do que foi feito, começando com '- '",
        "formacao": "curso, instituição e período",
        "certificacoes": "uma por linha",
        "idiomas": "idioma e nível, um por linha",
        "outros": "o que não couber nas seções acima",
    },
    "en": {
        "contato": "name, city, e-mail, phone, LinkedIn, GitHub (one item per line)",
        "resumo": "3 to 4 lines on who the person is and what they deliver",
        "habilidades": "comma-separated list",
        "experiencia": "for each job: title, company and dates on the first line; then achievements, "
                       "one per line starting with '- '",
        "projetos": "project name and one line on what was done, starting with '- '",
        "formacao": "degree, school and dates",
        "certificacoes": "one per line",
        "idiomas": "language and level, one per line",
        "outros": "anything that does not fit the sections above",
    },
}

_TEXTOS = {
    "pt": {
        "papel": "Você é especialista em recrutamento e em currículos compatíveis com sistemas ATS.",
        "tarefa": "Reescreva o currículo abaixo para a vaga informada, seguindo TODAS as regras:",
        "regras": [
            "Não invente nada. Não acrescente empresas, cargos, datas, números, métricas, tecnologias, "
            "cursos ou certificações que não estejam no currículo original.",
            "Mantenha exatamente as empresas, os cargos, as datas e a formação.",
            "Reescreva as frases para deixá-las claras, objetivas e orientadas a resultado.",
            "{encontradas}",
            "{faltando}",
            "Escreva o currículo inteiro em português do Brasil.",
            "Responda SOMENTE com o currículo, no formato abaixo: cada seção começa com o marcador "
            "exatamente como está (=== NOME ===), na ordem indicada. Omita seções sem conteúdo. "
            "Não use markdown, negrito, tabelas nem emojis.",
        ],
        "encontradas": "O currículo já tem estas palavras-chave da vaga: {lista}. Escreva cada uma "
                       "exatamente como está na vaga (mesma grafia) e mantenha todas no currículo, "
                       "na seção de habilidades e nas experiências em que foram usadas.",
        "sem_encontradas": "Use os termos da vaga onde eles descrevem algo que a pessoa realmente fez, "
                           "com a mesma grafia da vaga.",
        "faltando": "Estas palavras-chave da vaga NÃO aparecem no currículo: {lista}. Use alguma delas "
                    "somente se o currículo deixar claro que a pessoa tem essa experiência com outro "
                    "nome. Caso contrário, deixe de fora.",
        "sem_faltando": "Não acrescente palavras-chave que a pessoa não tenha.",
        "formato": "FORMATO DA RESPOSTA:",
        "vaga": "VAGA:",
        "curriculo": "CURRÍCULO ORIGINAL:",
    },
    "en": {
        "papel": "You are an expert recruiter and a specialist in ATS-friendly resumes.",
        "tarefa": "Rewrite the resume below for the job posting provided, following ALL of these rules:",
        "regras": [
            "Do not invent anything. Do not add companies, job titles, dates, numbers, metrics, "
            "technologies, courses or certifications that are not in the original resume.",
            "Keep the companies, job titles, dates and education exactly as they are.",
            "Rewrite the sentences to be clear, concise and results-oriented.",
            "{encontradas}",
            "{faltando}",
            "Write the entire resume in English. Translate the original content if needed, without "
            "changing its meaning.",
            "Reply ONLY with the resume, in the format below: each section starts with its marker "
            "exactly as written (=== NAME ===), in the order shown. Omit empty sections. "
            "Do not use markdown, bold, tables or emojis.",
        ],
        "encontradas": "The resume already has these keywords from the job posting: {lista}. Write each "
                       "one exactly as it appears in the posting (same spelling) and keep all of them, "
                       "in the skills section and in the jobs where they were used.",
        "sem_encontradas": "Use the posting's terms where they describe something the person actually "
                           "did, with the same spelling as the posting.",
        "faltando": "These keywords from the posting do NOT appear in the resume: {lista}. Use one only "
                    "if the resume makes it clear the person has that experience under another name. "
                    "Otherwise, leave it out.",
        "sem_faltando": "Do not add keywords the person does not have.",
        "formato": "RESPONSE FORMAT:",
        "vaga": "JOB POSTING:",
        "curriculo": "ORIGINAL RESUME:",
    },
}


def _lingua(idioma: str) -> str:
    return idioma if idioma in _TEXTOS else "pt"


def marcador(chave: str, idioma: str = "pt") -> str:
    """'experiencia' → '=== EXPERIENCIA ===' (pt) ou '=== EXPERIENCE ===' (en)."""
    return f"=== {_MARCADORES[_lingua(idioma)][chave]} ==="


def montar_prompt(secoes: Secoes, vaga: str, idioma: str, faltando: list[str],
                  encontradas: list[str] | tuple[str, ...] = ()) -> str:
    lingua = _lingua(idioma)
    t = _TEXTOS[lingua]

    sobre_encontradas = (t["encontradas"].format(lista=", ".join(encontradas)) if encontradas
                         else t["sem_encontradas"])
    sobre_faltando = t["faltando"].format(lista=", ".join(faltando)) if faltando else t["sem_faltando"]
    regras = "\n".join(
        f"{numero}. {regra.format(encontradas=sobre_encontradas, faltando=sobre_faltando)}"
        for numero, regra in enumerate(t["regras"], start=1)
    )
    formato = "\n".join(f"{marcador(chave, lingua)}\n({_DESCRICOES[lingua][chave]})" for chave in ORDEM)
    curriculo = "\n\n".join(
        f"{marcador(chave, lingua)}\n{secoes[chave].strip()}"
        for chave in ORDEM if secoes.get(chave, "").strip()
    )

    return f"""{t['papel']}

{t['tarefa']}

{regras}

{t['formato']}
{formato}

{t['vaga']}
{vaga.strip()}

{t['curriculo']}
{curriculo}
"""
