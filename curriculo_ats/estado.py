"""Regras de estado da tela que valem a pena testar fora do Streamlit."""
from collections.abc import MutableMapping

from curriculo_ats.leitura import ArquivoIlegivel, extrair_texto
from curriculo_ats.modelos import ORDEM
from curriculo_ats.secoes import dividir_secoes


def aplicar_upload(estado: MutableMapping, nome: str, dados: bytes, arquivo_id: str) -> str | None:
    """Lê o arquivo enviado e preenche as seções. Devolve a mensagem de erro, se houver.

    O mesmo arquivo não é relido (as edições da pessoa ficam). Um arquivo ilegível apaga o
    currículo anterior: senão a tela mostraria a nota de um arquivo que não é o enviado.
    """
    if estado.get("arquivo_id") == arquivo_id:
        return None
    estado["arquivo_id"] = arquivo_id
    try:
        texto = extrair_texto(nome, dados)
    except ArquivoIlegivel as erro:
        for chave in ORDEM:
            estado.pop(f"secao_{chave}", None)
        estado["carregado"] = False
        estado["erro_upload"] = str(erro)
        return str(erro)
    preencher_secoes(estado, texto)
    return None


def preencher_secoes(estado: MutableMapping, texto: str) -> None:
    for chave, conteudo in dividir_secoes(texto).items():
        estado[f"secao_{chave}"] = conteudo
    estado["carregado"] = True
    estado.pop("erro_upload", None)
