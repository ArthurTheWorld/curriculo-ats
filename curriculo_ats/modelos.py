"""Tipos e utilidades compartilhados pelos módulos."""
import unicodedata

# Um currículo dividido em seções: chave canônica → texto da seção.
Secoes = dict[str, str]

# Ordem das seções no arquivo final (e chaves canônicas válidas).
ORDEM: tuple[str, ...] = (
    "contato", "resumo", "habilidades", "experiencia", "projetos",
    "formacao", "certificacoes", "idiomas", "outros",
)


def secoes_vazias() -> Secoes:
    return {chave: "" for chave in ORDEM}


def normalizar(texto: str) -> str:
    """Minúsculas e sem acentos: 'Gestão' e 'GESTAO' viram 'gestao'."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.casefold()
