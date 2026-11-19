"""curriculo-ats: adapte o seu currículo a uma vaga, em formato que sistemas ATS leem bem.

    streamlit run app.py   (ou dois cliques em iniciar.bat / iniciar.sh)
"""
from pathlib import Path

import streamlit as st

from curriculo_ats.conferencia import conferir
from curriculo_ats.exportar import gerar_docx, gerar_pdf, nome_arquivo
from curriculo_ats.idioma import detectar_idioma
from curriculo_ats.leitura import ArquivoIlegivel, extrair_texto
from curriculo_ats.modelos import ORDEM, Secoes
from curriculo_ats.palavras_chave import analisar, carregar_termos, priorizar_habilidades
from curriculo_ats.prompt import montar_prompt
from curriculo_ats.resposta import RespostaInvalida, ler_resposta
from curriculo_ats.secoes import dividir_secoes

RAIZ = Path(__file__).resolve().parent
ROTULOS = {
    "contato": "Contato", "resumo": "Resumo", "habilidades": "Habilidades",
    "experiencia": "Experiência", "projetos": "Projetos", "formacao": "Formação",
    "certificacoes": "Certificações", "idiomas": "Idiomas", "outros": "Outros",
}
MODOS = {"sem_ia": ":material/format_align_left: Só formatar (sem IA)",
         "ia": ":material/auto_awesome: Reescrever com IA (copiar e colar)"}
CHATS = {"ChatGPT": "https://chatgpt.com", "Claude": "https://claude.ai", "Gemini": "https://gemini.google.com"}


@st.cache_resource
def termos():
    return carregar_termos()


def preencher_secoes(texto: str) -> None:
    for chave, conteudo in dividir_secoes(texto).items():
        st.session_state[f"secao_{chave}"] = conteudo
    st.session_state["carregado"] = True


def carregar_exemplo() -> None:
    dados = (RAIZ / "exemplos" / "curriculo_exemplo.docx").read_bytes()
    preencher_secoes(extrair_texto("curriculo_exemplo.docx", dados))
    st.session_state["vaga"] = (RAIZ / "exemplos" / "vaga_exemplo.txt").read_text(encoding="utf-8")
    st.session_state["empresa"] = "Empresa Exemplo"


def secoes_da_tela() -> Secoes:
    return {chave: st.session_state.get(f"secao_{chave}", "") for chave in ORDEM}


def como_texto(secoes: Secoes) -> str:
    return "\n".join(v for v in secoes.values() if v)


def mostrar_analise(analise, rotulo: str, anterior: int | None = None) -> None:
    delta = f"{analise.nota - anterior:+d} pontos" if anterior is not None else None
    st.metric(rotulo, f"{analise.nota}%", delta=delta)
    with st.container(horizontal=True):
        with st.container(border=True):
            st.markdown("**Encontradas no currículo**")
            st.markdown(", ".join(analise.encontradas) or "Nenhuma")
        with st.container(border=True):
            st.markdown("**Pedidas na vaga e não encontradas**")
            st.markdown(", ".join(analise.faltando) or "Nenhuma")


st.set_page_config(page_title="Currículo ATS", page_icon=":material/description:")
st.title("Currículo ATS")
st.caption("Adapte o seu currículo a uma vaga, em um formato que os sistemas de seleção (ATS) conseguem ler. "
           "Tudo roda no seu computador.")

# --- 1. Currículo ---------------------------------------------------------------
st.header("1. Seu currículo", divider="gray")
with st.container(horizontal=True, vertical_alignment="bottom"):
    arquivo = st.file_uploader("Envie o seu currículo (PDF ou Word .docx)", type=["pdf", "docx"], key="arquivo")
    st.button("Usar o exemplo", key="usar_exemplo", on_click=carregar_exemplo, icon=":material/science:")

if arquivo is not None and arquivo.file_id != st.session_state.get("arquivo_id"):
    st.session_state["arquivo_id"] = arquivo.file_id
    try:
        preencher_secoes(extrair_texto(arquivo.name, arquivo.getvalue()))
    except ArquivoIlegivel as erro:
        st.error(str(erro), icon=":material/error:")

if st.session_state.get("carregado"):
    with st.expander("Confira as seções que reconheci (pode editar)", expanded=False, icon=":material/edit:"):
        st.caption("A divisão automática nunca é perfeita. Corrija aqui o que tiver ido para o lugar errado.")
        for chave in ORDEM:
            st.text_area(ROTULOS[chave], key=f"secao_{chave}", height=120 if chave == "experiencia" else 80)

# --- 2. Vaga --------------------------------------------------------------------
st.header("2. A vaga", divider="gray")
st.text_area("Cole aqui a descrição da vaga", key="vaga", height=200)
st.text_input("Empresa (opcional, só para o nome do arquivo)", key="empresa")

vaga = st.session_state.get("vaga", "").strip()
if not st.session_state.get("carregado") or not vaga:
    st.info("Envie o seu currículo e cole a vaga para ver a compatibilidade.", icon=":material/info:")
    st.stop()

secoes = secoes_da_tela()
curriculo = como_texto(secoes)
idioma_vaga = detectar_idioma(vaga)

# --- 3. Compatibilidade ---------------------------------------------------------
st.header("3. Compatibilidade", divider="gray")
analise = analisar(curriculo, vaga, termos())
mostrar_analise(analise, "Compatibilidade com a vaga")
st.caption("As palavras não encontradas são para você conferir se tem e esqueceu de citar. "
           "Não acrescente o que você não tem.")

# --- 4. Caminho -----------------------------------------------------------------
st.header("4. Escolha o caminho", divider="gray")
modo = st.segmented_control("Como gerar o currículo", options=list(MODOS), format_func=MODOS.get,
                            default="sem_ia", required=True, key="modo")

if modo == "sem_ia":
    idioma = detectar_idioma(curriculo)
    if idioma != idioma_vaga:
        st.info("O seu currículo e a vaga estão em idiomas diferentes. Sem IA, o conteúdo não é traduzido: "
                "para isso, use o caminho com IA.", icon=":material/translate:")
    final = secoes | {"habilidades": priorizar_habilidades(secoes["habilidades"], analise.encontradas)}
    st.caption("O currículo é reorganizado no formato ATS, e as habilidades que a vaga pede vão para o começo "
               "da lista. Nada é acrescentado.")
else:
    idioma = idioma_vaga
    st.markdown("**a.** Copie o prompt abaixo (botão no canto do quadro).")
    st.code(montar_prompt(secoes, vaga, idioma_vaga, analise.faltando), language=None, wrap_lines=True)
    st.markdown("**b.** Cole em um chat de IA gratuito:")
    with st.container(horizontal=True):
        for nome, url in CHATS.items():
            st.link_button(nome, url, icon=":material/open_in_new:")
    st.warning("Ao colar, o seu currículo é enviado para o serviço de IA que você escolher.",
               icon=":material/privacy_tip:")
    resposta = st.text_area("**c.** Cole aqui a resposta do chat", key="resposta", height=200)
    if not resposta.strip():
        st.stop()
    try:
        final = ler_resposta(resposta)
    except RespostaInvalida as erro:
        st.error(str(erro), icon=":material/error:")
        st.stop()

    novidades = conferir(curriculo, resposta, termos())
    if novidades:
        itens = ", ".join(f"**{n.valor}**" for n in novidades)
        st.warning(f"A resposta cita {itens}, que não estão no seu currículo original. "
                   "Confira e apague o que não for verdade antes de usar.", icon=":material/fact_check:")
    else:
        st.success("Nenhum número, tecnologia ou contato novo em relação ao seu currículo.",
                   icon=":material/verified:")
    mostrar_analise(analisar(como_texto(final), vaga, termos()), "Compatibilidade depois da IA", analise.nota)

# --- 5. Baixar -----------------------------------------------------------------
st.header("5. Baixar", divider="gray")
empresa = st.session_state.get("empresa", "")
with st.container(horizontal=True):
    st.download_button("Baixar .docx", gerar_docx(final, idioma), file_name=nome_arquivo(final, empresa, "docx"),
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       icon=":material/download:", on_click="ignore")
    st.download_button("Baixar PDF", gerar_pdf(final, idioma), file_name=nome_arquivo(final, empresa, "pdf"),
                       mime="application/pdf", icon=":material/download:", on_click="ignore")
