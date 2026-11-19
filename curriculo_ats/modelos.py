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


def somente_contato(secoes: Secoes) -> bool:
    """A divisão automática falhou? (tudo caiu em 'contato', nenhuma outra seção tem texto)"""
    return bool(secoes.get("contato")) and not any(secoes.get(c) for c in ORDEM if c != "contato")


_CONTROLE = dict.fromkeys(c for c in range(32) if chr(c) not in "\t\n\r")


def limpar_controle(texto: str) -> str:
    """Remove caracteres de controle (comuns em PDFs do Word) que quebram o .docx.

    A tabulação vertical e a quebra de página viram quebra de linha; o resto some.
    """
    return texto.replace("\x0b", "\n").replace("\x0c", "\n").translate(_CONTROLE)


def normalizar(texto: str) -> str:
    """Minúsculas e sem acentos: 'Gestão' e 'GESTAO' viram 'gestao'."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.casefold()
