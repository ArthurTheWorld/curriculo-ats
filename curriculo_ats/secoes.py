"""Divide o texto do currículo em seções, reconhecendo títulos comuns em português e inglês."""
import re

from curriculo_ats.modelos import Secoes, normalizar, secoes_vazias

# Títulos normalizados (sem acento, minúsculos) para cada seção.
SINONIMOS: dict[str, tuple[str, ...]] = {
    "resumo": (
        "resumo", "resumo profissional", "perfil", "perfil profissional", "sobre", "sobre mim",
        "objetivo", "objetivo profissional", "apresentacao",
        "summary", "professional summary", "profile", "professional profile", "about", "about me",
        "objective", "career objective",
    ),
    "habilidades": (
        "habilidades", "competencias", "competencias tecnicas", "habilidades tecnicas",
        "conhecimentos", "conhecimentos tecnicos", "principais competencias",
        "skills", "technical skills", "core competencies", "competencies", "top skills",
    ),
    "experiencia": (
        "experiencia", "experiencias", "experiencia profissional", "experiencias profissionais",
        "historico profissional", "trajetoria profissional",
        "experience", "work experience", "professional experience", "employment history",
        "work history", "employment",
    ),
    "projetos": (
        "projetos", "projetos pessoais", "projetos relevantes", "portfolio",
        "projects", "personal projects", "selected projects",
    ),
    "formacao": (
        "formacao", "formacao academica", "escolaridade", "educacao", "graduacao",
        "education", "academic background", "academic education",
    ),
    "certificacoes": (
        "certificacoes", "certificados", "cursos", "cursos e certificacoes",
        "certificacoes e cursos", "cursos complementares", "formacao complementar",
        "certifications", "certificates", "courses", "licenses and certifications",
        "licenses & certifications",
    ),
    "idiomas": ("idiomas", "linguas", "languages"),
    "outros": (
        "outros", "informacoes adicionais", "voluntariado", "trabalho voluntario",
        "atividades extracurriculares", "interesses", "premios", "premiacoes", "publicacoes",
        "additional information", "volunteering", "volunteer experience", "extracurricular activities",
        "interests", "awards", "honors", "honors and awards", "publications", "other",
    ),
}

# De propósito ausentes: "Atividades", "Tecnologias", "Ferramentas" e "Stack" sozinhos costumam ser
# subtítulos dentro de um emprego, não seções. Se virassem títulos, partiriam a experiência ao meio.
_TITULOS = {titulo: chave for chave, titulos in SINONIMOS.items() for titulo in titulos}
MAX_PALAVRAS_TITULO = 5


def identificar_titulo(linha: str) -> str | None:
    """Chave canônica se a linha for um título de seção conhecido; senão None."""
    limpa = normalizar(linha).strip()
    if not limpa or len(limpa.split()) > MAX_PALAVRAS_TITULO:
        return None
    # Tira marcações comuns: "## Skills", "EXPERIÊNCIA:", "— Formação —", "**Resumo**".
    limpa = re.sub(r"[#*_:|\-–—•=]+", " ", limpa)
    limpa = " ".join(limpa.split())
    return _TITULOS.get(limpa)


def dividir_secoes(texto: str) -> Secoes:
    """Texto antes do primeiro título vai para 'contato'; seções repetidas são concatenadas."""
    blocos: dict[str, list[str]] = {}
    atual = "contato"
    for linha in texto.splitlines():
        chave = identificar_titulo(linha)
        if chave:
            atual = chave
            continue
        if linha.strip():
            blocos.setdefault(atual, []).append(linha.strip())

    secoes = secoes_vazias()
    for chave, linhas in blocos.items():
        secoes[chave] = "\n".join(linhas)
    return secoes
