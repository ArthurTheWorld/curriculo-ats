"""Palavras-chave: o que a vaga pede, o que o currículo já tem e o que falta.

Tudo por código, sem IA: um dicionário de termos (dados/termos.yaml) mais termos
técnicos que a própria vaga repete.
"""
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from curriculo_ats.idioma import PALAVRAS_FUNCIONAIS
from curriculo_ats.modelos import normalizar

DICIONARIO_PADRAO = Path(__file__).resolve().parent.parent / "dados" / "termos.yaml"

# Fronteiras de palavra que também respeitam termos como C++, C#, .NET e Node.js:
# antes do termo não pode haver letra/número/+/#/.; depois, nem letra/número/+/#.
_ANTES = r"(?<![\w+#.])"
_DEPOIS = r"(?![\w+#])"


@dataclass(frozen=True)
class Termo:
    nome: str
    sinonimos: tuple[str, ...]
    categoria: str
    so_sinonimos: bool = False

    def formas(self) -> tuple[str, ...]:
        return self.sinonimos if self.so_sinonimos else (self.nome, *self.sinonimos)


@dataclass
class Analise:
    nota: int
    encontradas: list[str]
    faltando: list[str]


def carregar_termos(caminho: Path | None = None) -> list[Termo]:
    return list(_carregar(str(caminho or DICIONARIO_PADRAO)))


@lru_cache(maxsize=4)
def _carregar(caminho: str) -> tuple[Termo, ...]:
    with open(caminho, encoding="utf-8") as arquivo:
        itens = yaml.safe_load(arquivo) or []
    return tuple(
        Termo(
            nome=str(item["nome"]),
            sinonimos=tuple(str(s) for s in item.get("sinonimos") or ()),
            categoria=str(item.get("categoria", "")),
            so_sinonimos=bool(item.get("so_sinonimos", False)),
        )
        for item in itens
    )


@lru_cache(maxsize=4096)
def _padrao(forma: str) -> re.Pattern:
    return re.compile(_ANTES + re.escape(normalizar(forma)) + _DEPOIS)


def _ocorrencias(texto_normalizado: str, forma: str) -> list[tuple[int, int]]:
    return [m.span() for m in _padrao(forma).finditer(texto_normalizado)]


def contem(texto: str, forma: str) -> bool:
    """O texto cita esta forma como palavra inteira (sem diferenciar acento e caixa)?"""
    return bool(_padrao(forma).search(normalizar(texto)))


def extrair_termos(texto: str, termos: list[Termo]) -> list[str]:
    """Nomes canônicos dos termos citados, na ordem em que aparecem, sem repetição.

    Quando um termo está dentro de outro maior (BI dentro de Power BI), só o maior conta.
    """
    alvo = normalizar(texto)
    achados: list[tuple[int, int, str]] = []  # (início, fim, nome)
    for termo in termos:
        for forma in termo.formas():
            achados.extend((ini, fim, termo.nome) for ini, fim in _ocorrencias(alvo, forma))

    # Maiores primeiro; descarta o que fica dentro de um trecho já aceito.
    achados.sort(key=lambda a: (-(a[1] - a[0]), a[0]))
    aceitos: list[tuple[int, int, str]] = []
    for ini, fim, nome in achados:
        if not any(a_ini <= ini and fim <= a_fim for a_ini, a_fim, _ in aceitos):
            aceitos.append((ini, fim, nome))

    nomes: list[str] = []
    for _ini, _fim, nome in sorted(aceitos):
        if nome not in nomes:
            nomes.append(nome)
    return nomes


_TOKEN = re.compile(r"[^\W_][\w.+#/-]*[\w+#]|[^\W_]")
_FUNCIONAIS = frozenset().union(*PALAVRAS_FUNCIONAIS.values())


def _parece_tecnico(token: str) -> bool:
    return token[0].isupper() or any(c.isdigit() for c in token) or any(c in ".+#" for c in token[1:])


def _inicio_de_frase(texto: str, posicao: int) -> bool:
    anterior = texto[:posicao].rstrip()
    return not anterior or anterior[-1] in ".!?:;\n•-–—"


def termos_extras(vaga: str, ja_encontrados: list[str]) -> list[str]:
    """Termos técnicos que a vaga repete (≥ 2 vezes) e o dicionário não conhece.

    Ex.: uma ferramenta nova citada duas vezes. Palavras no começo de frase sozinhas
    não contam, porque toda frase começa com maiúscula.
    """
    conhecidos = {normalizar(n) for n in ja_encontrados}
    contagem: dict[str, int] = {}
    fora_do_inicio: set[str] = set()
    grafia: dict[str, str] = {}

    for m in _TOKEN.finditer(vaga):
        token = m.group()
        chave = normalizar(token)
        if len(token) < 2 or not _parece_tecnico(token) or chave in _FUNCIONAIS or chave in conhecidos:
            continue
        contagem[chave] = contagem.get(chave, 0) + 1
        grafia.setdefault(chave, token)
        if not _inicio_de_frase(vaga, m.start()):
            fora_do_inicio.add(chave)

    return [grafia[c] for c in contagem if contagem[c] >= 2 and c in fora_do_inicio]


def analisar(curriculo: str, vaga: str, termos: list[Termo]) -> Analise:
    da_vaga = extrair_termos(vaga, termos)
    # Extras que já são forma de um termo do dicionário (ex.: "Spark") seriam duplicados.
    da_vaga += [extra for extra in termos_extras(vaga, da_vaga) if not extrair_termos(extra, termos)]
    no_curriculo = set(extrair_termos(curriculo, termos))

    termo_por_nome = {t.nome: t for t in termos}
    encontradas, faltando = [], []
    for nome in da_vaga:
        termo = termo_por_nome.get(nome)
        presente = nome in no_curriculo if termo else contem(curriculo, nome)
        (encontradas if presente else faltando).append(nome)

    nota = round(100 * len(encontradas) / len(da_vaga)) if da_vaga else 0
    return Analise(nota=nota, encontradas=encontradas, faltando=faltando)


_SEPARADORES = re.compile(r"\s*[,;|•\n]\s*")


def priorizar_habilidades(habilidades: str, encontradas: list[str]) -> str:
    """Põe no começo as habilidades que a vaga pede. Não acrescenta nem remove nada."""
    itens = [i for i in _SEPARADORES.split(habilidades.strip()) if i]
    if not itens:
        return habilidades

    def posicao(item: str) -> int:
        for indice, nome in enumerate(encontradas):
            if contem(item, nome) or contem(nome, item):
                return indice
        return len(encontradas)

    ordenados = sorted(itens, key=posicao)  # sorted é estável: o resto mantém a ordem original
    separador = "\n" if "\n" in habilidades and "," not in habilidades else ", "
    return separador.join(ordenados)
