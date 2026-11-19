"""Confere a resposta da IA contra o currículo original: o que apareceu e não existia antes?

Não decide nada sozinho: só aponta números, tecnologias e contatos novos para a pessoa conferir.
"""
import re
from dataclasses import dataclass

from curriculo_ats.palavras_chave import Termo, extrair_termos


@dataclass(frozen=True)
class Novidade:
    tipo: str   # "numero" | "termo" | "contato"
    valor: str


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_TELEFONE = re.compile(r"(?:\+\d{1,3}\s?)?\(?\d{2}\)?\s?9?\d{4}[\s-]?\d{4}(?!\d)|\+\d[\d\s-]{7,}\d")
# Número que não está colado a uma letra antes (k8s, S3, EC2 são nomes, não números).
_NUMERO = re.compile(r"(?<![^\W\d_])\d[\d.,]*(?:\s?%)?")


def _contatos(texto: str) -> list[str]:
    return [m.group().strip() for m in _EMAIL.finditer(texto)] + \
           [m.group().strip() for m in _TELEFONE.finditer(texto)]


def _so_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor)


def _sem_contatos(texto: str) -> str:
    """Remove e-mails e telefones para que seus dígitos não contem como números."""
    return _TELEFONE.sub(" ", _EMAIL.sub(" ", texto))


def _numeros(texto: str) -> dict[str, str]:
    """Forma normalizada → como apareceu. '1.500' e '1500' são o mesmo número."""
    achados: dict[str, str] = {}
    for m in _NUMERO.finditer(_sem_contatos(texto)):
        exibido = m.group().strip().rstrip(".,")
        chave = re.sub(r"[.,\s]", "", exibido)
        achados.setdefault(chave, exibido)
    return achados


def conferir(original: str, resposta: str, termos: list[Termo]) -> list[Novidade]:
    novidades: list[Novidade] = []

    numeros_originais = _numeros(original)
    for chave, exibido in _numeros(resposta).items():
        if chave not in numeros_originais:
            novidades.append(Novidade("numero", exibido))

    termos_originais = set(extrair_termos(original, termos))
    for nome in extrair_termos(resposta, termos):
        if nome not in termos_originais:
            novidades.append(Novidade("termo", nome))

    emails_originais = {e.casefold() for e in _EMAIL.findall(original)}
    telefones_originais = {_so_digitos(t) for t in _TELEFONE.findall(original)}
    vistos: set[str] = set()
    for contato in _contatos(resposta):
        chave = contato.casefold() if "@" in contato else _so_digitos(contato)
        conhecido = chave in emails_originais or chave in telefones_originais
        if not conhecido and chave not in vistos:
            vistos.add(chave)
            novidades.append(Novidade("contato", contato))

    return novidades
