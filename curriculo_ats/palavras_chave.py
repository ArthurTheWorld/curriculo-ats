"""Palavras-chave: o que a vaga pede, o que o currículo já tem e o que falta.

Tudo por código, sem IA: um dicionário de termos (dados/termos.yaml) mais termos
técnicos que a própria vaga repete.
"""
import re
import unicodedata
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
    # Formas que só contam com estas maiúsculas: "Spark" é tecnologia, "spark" é palavra comum.
    exatos: tuple[str, ...] = ()

    def formas(self) -> tuple[str, ...]:
        """Formas comparadas sem diferenciar maiúsculas e acentos."""
        nome = () if self.so_sinonimos or self.nome in self.exatos else (self.nome,)
        return (*nome, *self.sinonimos)


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
            exatos=tuple(str(s) for s in item.get("exatos") or ()),
        )
        for item in itens
    )


def _sem_acento(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c))


@lru_cache(maxsize=4096)
def _padrao(forma: str, exato: bool = False) -> re.Pattern:
    alvo = _sem_acento(forma) if exato else _sem_acento(forma).lower()
    return re.compile(_ANTES + re.escape(alvo) + _DEPOIS)


def _versoes(texto: str) -> tuple[str, str]:
    """(sem acento e minúsculo, sem acento com as maiúsculas originais) — mesmo tamanho."""
    sem_acento = _sem_acento(texto)
    return sem_acento.lower(), sem_acento


def _ocorrencias_do_termo(versoes: tuple[str, str], termo: Termo) -> list[tuple[int, int]]:
    minusculo, original = versoes
    spans = [m.span() for forma in termo.formas() for m in _padrao(forma).finditer(minusculo)]
    spans += [m.span() for forma in termo.exatos for m in _padrao(forma, True).finditer(original)]
    return spans


def contem(texto: str, forma: str) -> bool:
    """O texto cita esta forma como palavra inteira (sem diferenciar acento e caixa)?"""
    return bool(_padrao(forma).search(_sem_acento(texto).lower()))


def termos_presentes(texto: str, termos: list[Termo]) -> set[str]:
    """Todos os termos citados, inclusive os que estão dentro de outro maior (AWS em AWS Lambda)."""
    versoes = _versoes(texto)
    return {t.nome for t in termos if _ocorrencias_do_termo(versoes, t)}


def extrair_termos(texto: str, termos: list[Termo]) -> list[str]:
    """Nomes canônicos dos termos citados, na ordem em que aparecem, sem repetição.

    Para listar o que uma vaga pede: quando um termo está dentro de outro maior
    (BI dentro de Power BI), só o maior conta.
    """
    versoes = _versoes(texto)
    achados = [(ini, fim, t.nome) for t in termos for ini, fim in _ocorrencias_do_termo(versoes, t)]

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
    anterior = texto[max(0, posicao - 20):posicao].rstrip()
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
    no_curriculo = termos_presentes(curriculo, termos)

    do_dicionario = {t.nome for t in termos}
    encontradas, faltando = [], []
    for nome in da_vaga:
        presente = nome in no_curriculo if nome in do_dicionario else contem(curriculo, nome)
        (encontradas if presente else faltando).append(nome)

    nota = round(100 * len(encontradas) / len(da_vaga)) if da_vaga else 0
    return Analise(nota=nota, encontradas=encontradas, faltando=faltando)


_ROTULO = re.compile(r"^\s*[^,;:|]{1,40}:\s")
_SEPARADORES = re.compile(r"\s*[,;|•]\s*")


def priorizar_habilidades(habilidades: str, encontradas: list[str], termos: list[Termo]) -> str:
    """Põe no começo as habilidades que a vaga pede. Não acrescenta, remove nem reescreve nada.

    - Várias linhas (listas com marcador ou por categoria): reordena linhas inteiras.
    - Uma linha "Python, SQL, Excel": reordena os itens, exceto se tiver rótulo ("Ferramentas: ...").
    """
    def posicao(trecho: str) -> int:
        presentes = termos_presentes(trecho, termos)
        indices = [i for i, nome in enumerate(encontradas) if nome in presentes or contem(trecho, nome)]
        return min(indices, default=len(encontradas))

    linhas = [linha for linha in habilidades.splitlines() if linha.strip()]
    if len(linhas) > 1:
        return "\n".join(sorted(linhas, key=posicao))  # sorted é estável: o resto mantém a ordem
    if not linhas or _ROTULO.match(linhas[0]):
        return habilidades
    itens = [i for i in _SEPARADORES.split(linhas[0].strip()) if i]
    return ", ".join(sorted(itens, key=posicao))
