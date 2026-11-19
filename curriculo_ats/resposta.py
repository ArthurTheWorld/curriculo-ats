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


def _parece_contato(linha: str) -> bool:
    """E-mail, telefone, link ou uma linha curta que não é frase de conversa ("Claro! Aqui está:")."""
    if "@" in linha or re.search(r"\d{4}", linha) or re.search(r"linkedin|github|https?://", linha, re.I):
        return True
    return len(linha.split()) <= 5 and not linha.rstrip().endswith((":", "!", "?", "."))


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
    preambulo: list[str] = []
    atual: str | None = None
    for linha in linhas:
        achou = _MARCADOR.match(linha)
        if achou:
            atual = _chave_do_marcador(achou.group(1))
            continue
        if atual and linha:
            blocos.setdefault(atual, []).append(linha)
        elif linha:
            preambulo.append(linha)

    # Antes do primeiro marcador costuma vir conversa do chat ("Claro! Aqui está:"), que é
    # descartada. Mas, se não veio seção de contato, linhas que parecem nome ou contato ficam.
    if blocos and "contato" not in blocos:
        contato = [linha for linha in preambulo if _parece_contato(linha)]
        if contato:
            blocos["contato"] = contato

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
