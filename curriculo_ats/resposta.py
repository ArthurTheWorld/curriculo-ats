"""Lê a resposta que a pessoa colou do chat de IA e transforma em seções."""
import re

from curriculo_ats.modelos import ORDEM, Secoes, limpar_controle, normalizar, secoes_vazias
from curriculo_ats.secoes import dividir_secoes, identificar_titulo

# "=== EXPERIENCIA ===", com tolerância a acentos, caixa, espaços e enfeites de markdown.
_MARCADOR = re.compile(r"^\s*={2,}\s*([^=]+?)\s*={2,}\s*$")
_ENFEITES = re.compile(r"^[#>\s]+|\*\*|__|`")
# Títulos de contato não existem em secoes.py (lá, contato é o que vem antes do primeiro título).
_CONTATO = {"contato", "contatos", "contact", "contacts", "contact information", "contact info",
            "dados pessoais", "informacoes de contato", "informacoes pessoais", "personal information"}

NAO_RECONHECI = ("Não reconheci as seções da resposta. Peça ao chat para responder no formato com "
                 "=== SEÇÃO ===, como está no prompt.")


class RespostaInvalida(Exception):
    """A resposta colada não pôde ser lida. A mensagem é para mostrar à pessoa."""


def _limpar(linha: str) -> str:
    return _ENFEITES.sub("", linha).strip()


def _chave_do_marcador(nome: str) -> str:
    """'EXPERIENCIA', 'Experiência Profissional', 'EXPERIENCE' → 'experiencia'. Desconhecido → 'outros'."""
    simples = normalizar(nome).strip()
    if simples.replace(" ", "") in ORDEM:
        return simples.replace(" ", "")
    if simples in _CONTATO:
        return "contato"
    return identificar_titulo(nome) or "outros"


def ler_resposta(texto: str) -> Secoes:
    linhas = [_limpar(linha) for linha in limpar_controle(texto).splitlines()]
    linhas = [linha for linha in linhas if not linha.startswith("```")]
    if not any(linhas):
        raise RespostaInvalida("A resposta está vazia. Cole aqui o texto que o chat devolveu.")

    blocos: dict[str, list[str]] = {}
    atual: str | None = None
    for linha in linhas:
        achou = _MARCADOR.match(linha)
        if achou:
            atual = _chave_do_marcador(achou.group(1))
            continue
        if atual and linha:  # texto antes do primeiro marcador ("Claro! Aqui está...") é ignorado
            blocos.setdefault(atual, []).append(linha)

    if blocos:
        secoes = secoes_vazias()
        for chave, conteudo in blocos.items():
            secoes[chave] = "\n".join(conteudo)
        return secoes

    # Sem marcadores: tenta pelos títulos de seção comuns.
    secoes = dividir_secoes("\n".join(linhas))
    so_contato = not any(secoes[c] for c in ORDEM if c != "contato")
    if so_contato and len([linha for linha in linhas if linha]) > 3:
        raise RespostaInvalida(NAO_RECONHECI)
    return secoes
