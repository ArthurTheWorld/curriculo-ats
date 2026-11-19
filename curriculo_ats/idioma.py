"""Detecta se um texto está em português ou inglês e define os títulos das seções em cada idioma."""
import re

from curriculo_ats.modelos import normalizar

# Palavras muito frequentes e quase exclusivas de cada idioma (já normalizadas, sem acento).
PALAVRAS_FUNCIONAIS: dict[str, frozenset[str]] = {
    "pt": frozenset({
        "de", "da", "do", "das", "dos", "para", "com", "que", "em", "uma", "um", "no", "na",
        "nos", "nas", "voce", "sera", "sao", "nao", "ou", "pelo", "pela", "como", "seu", "sua",
        "buscamos", "vaga", "requisitos", "experiencia", "conhecimento", "e",
        "o", "os", "as", "ao", "aos", "na", "no", "num", "numa",
    }),
    "en": frozenset({
        "the", "and", "with", "for", "you", "will", "to", "of", "our", "we", "are", "is", "in",
        "on", "a", "an", "your", "be", "as", "this", "that", "looking", "requirements",
        "experience", "knowledge", "join", "team", "or",
    }),
}

TITULOS: dict[str, dict[str, str]] = {
    "pt": {
        "resumo": "Resumo",
        "habilidades": "Habilidades",
        "experiencia": "Experiência Profissional",
        "projetos": "Projetos",
        "formacao": "Formação Acadêmica",
        "certificacoes": "Certificações",
        "idiomas": "Idiomas",
        "outros": "Informações Adicionais",
    },
    "en": {
        "resumo": "Summary",
        "habilidades": "Skills",
        "experiencia": "Professional Experience",
        "projetos": "Projects",
        "formacao": "Education",
        "certificacoes": "Certifications",
        "idiomas": "Languages",
        "outros": "Additional Information",
    },
}


def palavras(texto: str) -> list[str]:
    return re.findall(r"[a-z]+", normalizar(texto))


def detectar_idioma(texto: str) -> str:
    """'pt' ou 'en'. Empate ou texto sem pistas: 'pt'."""
    contagem = {lingua: 0 for lingua in PALAVRAS_FUNCIONAIS}
    for palavra in palavras(texto):
        for lingua, conjunto in PALAVRAS_FUNCIONAIS.items():
            if palavra in conjunto:
                contagem[lingua] += 1
    return "en" if contagem["en"] > contagem["pt"] else "pt"
