# curriculo-ats Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Um app local (Streamlit) que lê o currículo de qualquer pessoa, compara com uma vaga e gera um currículo amigável para ATS em `.docx` e PDF, sem chave de API: por código ou por um prompt de copiar e colar em chat gratuito.

**Architecture:** Módulos Python puros e testáveis em `curriculo_ats/` (leitura → seções → idioma → palavras-chave → prompt/resposta → conferência → exportação). `app.py` só orquestra. Scripts `iniciar.bat`/`iniciar.sh` criam o ambiente e abrem o app.

**Tech Stack:** Python ≥ 3.10 · streamlit · pdfplumber · python-docx · fpdf2 · pyyaml · pytest · GitHub Actions

**Spec:** `docs/superpowers/specs/2026-11-18-curriculo-ats-design.md`

## Global Constraints

- Python 3.10 ou mais novo; só bibliotecas Python puras: `streamlit>=1.40`, `pdfplumber>=0.11`, `python-docx>=1.1`, `fpdf2>=2.8`, `pyyaml>=6`. Testes: `pytest>=8`.
- Nenhuma chamada de rede no código (nem API de IA). Funciona offline.
- Nunca acrescentar conteúdo ao currículo: o código só reorganiza, reordena e aponta.
- Interface e mensagens em português do Brasil. Currículo final: títulos no idioma do currículo (modo sem IA) ou da vaga (modo IA).
- Layout ATS: uma coluna, Arial/Helvetica 10-11, títulos em texto simples, marcadores simples; sem tabelas, caixas de texto, imagens, ícones, cabeçalho/rodapé ou cores.
- Ordem das seções no arquivo final: Contato, Resumo, Habilidades, Experiência, Projetos, Formação, Certificações, Idiomas, Outros; seções vazias omitidas.
- Licença MIT, autor Luiz Arthur. Repositório `ArthurTheWorld/curriculo-ats`.

## Review Focus

1. PDF escaneado (só imagem) ou vazio → erro claro pedindo PDF com texto ou `.docx`, nunca uma tela vazia. (Task 1)
2. Currículo sem nenhum título reconhecível → tudo cai em "contato"/"outros" e o fluxo continua. (Task 2)
3. Resposta da IA colada com markdown (` ``` `, `**negrito**`, `### Experiência`, marcadores com acento ou caixa diferente) → seções lidas mesmo assim. (Task 5)
4. Caracteres fora do latin-1 no PDF (– — “ ” • … emoji) → PDF gerado sem erro, com substitutos ASCII. (Task 7)
5. Termos com símbolos e acentos (`C++`, `C#`, `.NET`, `Node.js`, "Gestão" × "gestao") casam certo, e não há falso positivo de substring (`Java` dentro de `JavaScript`, `R` dentro de `React`). (Task 4)

---

## Estrutura de arquivos

```
curriculo-ats/
├── app.py                         # interface Streamlit (Task 8)
├── curriculo_ats/
│   ├── __init__.py
│   ├── modelos.py                 # Secoes, ORDEM, chaves canônicas (Task 2)
│   ├── leitura.py                 # Task 1
│   ├── secoes.py                  # Task 2
│   ├── idioma.py                  # Task 3
│   ├── palavras_chave.py          # Task 4
│   ├── prompt.py, resposta.py     # Task 5
│   ├── conferencia.py             # Task 6
│   └── exportar.py                # Task 7
├── dados/termos.yaml              # Task 4
├── exemplos/curriculo_exemplo.docx, vaga_exemplo.txt   # Task 9
├── tests/ (um arquivo por módulo + conftest.py)
├── iniciar.bat, iniciar.sh        # Task 9
├── requirements.txt, requirements-dev.txt, pytest.ini, .gitignore, LICENSE
├── .github/workflows/testes.yml   # Task 9
└── README.md                      # Task 9
```

Comandos abaixo assumem a raiz do projeto e o venv: `.venv\Scripts\python -m pytest` (Windows). Abreviado como `pytest`.

---

### Task 1: Base do projeto e leitura de arquivos

**Files:**
- Create: `requirements.txt`, `requirements-dev.txt`, `pytest.ini` (`testpaths = tests`, `pythonpath = .`), `.gitignore` (`.venv/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`), `LICENSE` (MIT, "Copyright (c) 2026 Luiz Arthur"), `curriculo_ats/__init__.py`, `curriculo_ats/leitura.py`
- Test: `tests/conftest.py`, `tests/test_leitura.py`

**Interfaces:**
- Produces: `class ArquivoIlegivel(Exception)`; `extrair_texto(nome_arquivo: str, conteudo: bytes) -> str` (texto com quebras de linha; tipo pelo sufixo `.pdf`/`.docx`, sem diferenciar maiúsculas).
- Produces (fixtures em `conftest.py`): `docx_bytes(paragrafos: list[str]) -> bytes` e `pdf_bytes(linhas: list[str]) -> bytes` (fpdf2, Helvetica), expostas como fixtures `fazer_docx` e `fazer_pdf` que devolvem essas funções.

- [ ] **Step 1: Criar venv e instalar** — `py -3.12 -m venv .venv` e `.venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt`. Esperado: instala sem erro.
- [ ] **Step 2: Escrever os testes que falham**

```python
def test_le_docx(fazer_docx):
    assert extrair_texto("cv.DOCX", fazer_docx(["Ana Souza", "Experiência"])) == "Ana Souza\nExperiência"

def test_le_pdf_com_texto(fazer_pdf):
    texto = extrair_texto("cv.pdf", fazer_pdf(["Ana Souza", "Python e SQL"]))
    assert "Ana Souza" in texto and "Python e SQL" in texto

def test_pdf_sem_texto_da_erro_claro(fazer_pdf):
    with pytest.raises(ArquivoIlegivel, match="PDF com texto ou um arquivo .docx"):
        extrair_texto("scan.pdf", fazer_pdf([]))

def test_formato_nao_suportado():
    with pytest.raises(ArquivoIlegivel, match="PDF ou .docx"):
        extrair_texto("cv.odt", b"x")

def test_arquivo_corrompido():
    with pytest.raises(ArquivoIlegivel):
        extrair_texto("cv.docx", b"nao e um zip")
```

- [ ] **Step 3: Rodar** — `pytest tests/test_leitura.py -v`. Esperado: FAIL (módulo não existe).
- [ ] **Step 4: Implementar `extrair_texto`** — `.docx`: `docx.Document(BytesIO)`, parágrafos não vazios + texto de tabelas, unidos por `\n`. `.pdf`: `pdfplumber.open(BytesIO)`, `page.extract_text()` de cada página. Texto final com `strip()`; vazio → `ArquivoIlegivel("Não encontrei texto neste arquivo. Se for um PDF escaneado, envie um PDF com texto ou um arquivo .docx.")`. Qualquer exceção da biblioteca vira `ArquivoIlegivel` com mensagem em português.
- [ ] **Step 5: Rodar** — `pytest -v`. Esperado: PASS.
- [ ] **Step 6: Commit** — `git add -A && git commit -m "feat: leitura de PDF e docx"`

---

### Task 2: Divisão em seções

**Files:**
- Create: `curriculo_ats/modelos.py`, `curriculo_ats/secoes.py`
- Test: `tests/test_secoes.py`

**Interfaces:**
- Produces (`modelos.py`): `Secoes = dict[str, str]`; `ORDEM: tuple[str, ...] = ("contato", "resumo", "habilidades", "experiencia", "projetos", "formacao", "certificacoes", "idiomas", "outros")`.
- Produces (`secoes.py`): `identificar_titulo(linha: str) -> str | None` (chave canônica); `dividir_secoes(texto: str) -> Secoes` (sempre todas as chaves de `ORDEM`, vazias como `""`).

- [ ] **Step 1: Testes que falham**

```python
def test_titulos_pt_e_en():
    assert identificar_titulo("EXPERIÊNCIA PROFISSIONAL") == "experiencia"
    assert identificar_titulo("Work Experience:") == "experiencia"
    assert identificar_titulo("Formação Acadêmica") == "formacao"
    assert identificar_titulo("Skills") == "habilidades"
    assert identificar_titulo("Trabalhei com experiência em vendas por 3 anos") is None

def test_divide_e_contato_antes_do_primeiro_titulo():
    s = dividir_secoes("Ana Souza\nana@x.com\nResumo\nEngenheira de dados\nHabilidades\nPython, SQL")
    assert s["contato"] == "Ana Souza\nana@x.com"
    assert s["resumo"] == "Engenheira de dados"
    assert s["habilidades"] == "Python, SQL"
    assert set(s) == set(ORDEM)

def test_titulo_desconhecido_vai_para_outros():
    s = dividir_secoes("Ana\nResumo\nTexto\nVoluntariado\nONG X")
    assert s["outros"] == "ONG X" and s["resumo"] == "Texto"

def test_sem_nenhum_titulo():
    s = dividir_secoes("Ana Souza\nPython SQL dbt")
    assert s["contato"] == "Ana Souza\nPython SQL dbt"
```

- [ ] **Step 2: Rodar** — esperado FAIL.
- [ ] **Step 3: Implementar** — `identificar_titulo`: linha curta (≤ 5 palavras, sem ponto final), normalizada (sem acento, minúscula, sem `:#*-`), comparada a um dicionário de sinônimos PT/EN por chave (ex.: experiencia ← "experiencia", "experiencia profissional", "historico profissional", "experience", "work experience", "professional experience", "employment history"; cobrir todas as chaves exceto contato; "outros" inclui títulos comuns que não têm seção própria: voluntariado, atividades, interesses, prêmios, publicações, volunteering, interests, awards, publications). Linhas que não casam com nenhum sinônimo: tratadas como conteúdo. `dividir_secoes`: percorre linhas; texto antes do primeiro título → contato; cada bloco recebe a chave do título; mesma chave repetida concatena com `\n`.
- [ ] **Step 4: Rodar** — PASS.
- [ ] **Step 5: Commit** — `feat: divisão do currículo em seções`

---

### Task 3: Detecção de idioma e títulos

**Files:**
- Create: `curriculo_ats/idioma.py`
- Test: `tests/test_idioma.py`

**Interfaces:**
- Produces: `detectar_idioma(texto: str) -> str` (`"pt"` ou `"en"`; empate ou texto vazio → `"pt"`); `TITULOS: dict[str, dict[str, str]]` (`TITULOS["en"]["experiencia"] == "Professional Experience"`, `TITULOS["pt"]["experiencia"] == "Experiência Profissional"`, uma entrada para cada chave de `ORDEM` exceto `contato`).

- [ ] **Step 1: Testes que falham**

```python
def test_portugues():
    assert detectar_idioma("Buscamos pessoa engenheira de dados com experiência em Python para atuar no time") == "pt"

def test_ingles():
    assert detectar_idioma("We are looking for a data engineer with experience in Python to join the team") == "en"

def test_vazio_e_pt():
    assert detectar_idioma("") == "pt"

def test_titulos_cobrem_todas_as_secoes():
    for lingua in ("pt", "en"):
        assert set(TITULOS[lingua]) == set(ORDEM) - {"contato"}
```

- [ ] **Step 2: Rodar** — FAIL.
- [ ] **Step 3: Implementar** — contagem de palavras funcionais (~20 por idioma: "de, para, com, que, em, uma, dos, você, será..." / "the, and, with, for, you, will, to, of, our..."), sobre palavras normalizadas.
- [ ] **Step 4: Rodar** — PASS.
- [ ] **Step 5: Commit** — `feat: detecção de idioma`

---

### Task 4: Dicionário e análise de palavras-chave

**Files:**
- Create: `dados/termos.yaml`, `curriculo_ats/palavras_chave.py`
- Test: `tests/test_palavras_chave.py`

**Interfaces:**
- Produces: `@dataclass(frozen=True) class Termo: nome: str; sinonimos: tuple[str, ...]; categoria: str`; `carregar_termos(caminho: Path | None = None) -> list[Termo]` (padrão `dados/termos.yaml`, com cache); `extrair_termos(texto: str, termos: list[Termo]) -> list[str]` (nomes canônicos, sem repetição, na ordem em que aparecem); `termos_extras(vaga: str, ja_encontrados: list[str]) -> list[str]`; `@dataclass class Analise: nota: int; encontradas: list[str]; faltando: list[str]`; `analisar(curriculo: str, vaga: str, termos: list[Termo]) -> Analise`; `priorizar_habilidades(habilidades: str, encontradas: list[str]) -> str`.

Formato do YAML (lista): `- {nome: "Power BI", sinonimos: ["PowerBI"], categoria: ferramenta}`. Conteúdo inicial: algumas centenas de termos (linguagens, dados, nuvem, devops, frameworks web, metodologias, certificações comuns, idiomas, soft skills técnicas como "Scrum"). Termos ambíguos de 1 letra (`R`, `C`) só com sinônimos explícitos ("linguagem R", "R language").

- [ ] **Step 1: Testes que falham**

```python
TERMOS = [Termo("Java", (), "linguagem"), Termo("JavaScript", ("JS",), "linguagem"),
          Termo("C++", (), "linguagem"), Termo("C#", (), "linguagem"), Termo(".NET", ("dotnet",), "framework"),
          Termo("Node.js", ("NodeJS",), "framework"), Termo("Gestão de projetos", (), "metodologia"),
          Termo("React", (), "framework"), Termo("Power BI", ("PowerBI",), "ferramenta")]

def test_simbolos_sinonimos_e_acentos():
    assert extrair_termos("C++, C#, dotnet, NodeJS e gestao de projetos", TERMOS) == \
        ["C++", "C#", ".NET", "Node.js", "Gestão de projetos"]

def test_sem_falso_positivo_de_substring():
    assert extrair_termos("JavaScript e React", TERMOS) == ["JavaScript", "React"]

def test_analise_nota_e_faltando():
    a = analisar("Sei Java e PowerBI", "Vaga: Java, Power BI, React e C#", TERMOS)
    assert a.encontradas == ["Java", "Power BI"]
    assert a.faltando == ["React", "C#"]
    assert a.nota == 50

def test_vaga_sem_termos_da_nota_zero_sem_erro():
    assert analisar("x", "texto sem nada técnico", TERMOS).nota == 0

def test_termos_extras_repetidos_da_vaga():
    vaga = "Experiência com Looker. O Looker é central. Também Airbyte."
    assert termos_extras(vaga, []) == ["Looker"]

def test_priorizar_habilidades_nao_acrescenta():
    assert priorizar_habilidades("Excel, Python, SQL", ["SQL", "Python", "Rust"]) == "SQL, Python, Excel"

def test_dicionario_real_carrega_e_nao_tem_duplicados():
    termos = carregar_termos()
    nomes = [t.nome.casefold() for t in termos]
    assert len(termos) >= 200 and len(nomes) == len(set(nomes))
```

- [ ] **Step 2: Rodar** — FAIL.
- [ ] **Step 3: Implementar** — normalização: `unicodedata` NFKD sem acentos + `casefold`. Casamento por regex com `re.escape(forma)` e fronteiras `(?<![\w+#.])` / `(?![\w+#])` (para `.NET` no início e `C++`/`C#` no fim). `termos_extras`: tokens da vaga com inicial maiúscula, dígito ou `.+#` no meio, que aparecem ≥ 2 vezes, não estão no começo de frase em todas as ocorrências e não são palavra funcional (reusar a lista de `idioma.py`). `analisar`: termos da vaga = `extrair_termos(vaga)` + `termos_extras`; nota = `round(100 * len(encontradas) / len(termos_da_vaga))`, 0 se vazio. `priorizar_habilidades`: separa por `,`, `;`, `•`, `|` ou quebra de linha; itens que contêm um termo de `encontradas` vão para a frente na ordem de `encontradas`; o resto mantém a ordem; junta com `", "`.
- [ ] **Step 4: Rodar** — PASS.
- [ ] **Step 5: Commit** — `feat: dicionário de termos e análise de compatibilidade`

---

### Task 5: Prompt de copiar e colar e leitura da resposta

**Files:**
- Create: `curriculo_ats/prompt.py`, `curriculo_ats/resposta.py`
- Test: `tests/test_prompt_resposta.py`

**Interfaces:**
- Consumes: `Secoes`, `ORDEM` (Task 2), `identificar_titulo` (Task 2), `TITULOS` (Task 3).
- Produces: `MARCADOR = "=== {chave} ==="` com a chave em maiúsculas sem acento (`=== EXPERIENCIA ===`); `montar_prompt(secoes: Secoes, vaga: str, idioma: str, faltando: list[str]) -> str`; `class RespostaInvalida(Exception)`; `ler_resposta(texto: str) -> Secoes`.

Regras que o prompt **deve** conter (verificadas no teste por trechos): não inventar empresas, cargos, datas, números, tecnologias ou certificações; manter datas, cargos e empresas como estão; usar palavras-chave da vaga só onde forem verdade; termos em `faltando` são apenas para a pessoa conferir, não para incluir; escrever no idioma da vaga (`"português do Brasil"` ou `"English"`); responder **somente** no formato de marcadores, uma seção por marcador, na ordem de `ORDEM`, sem markdown.

- [ ] **Step 1: Testes que falham**

```python
def test_prompt_tem_regras_curriculo_vaga_e_formato():
    p = montar_prompt({"contato": "Ana", "experiencia": "Empresa X"}, "Vaga de dados", "en", ["dbt"])
    assert "Ana" in p and "Empresa X" in p and "Vaga de dados" in p
    assert "Não invente" in p and "English" in p and "dbt" in p
    assert "=== EXPERIENCIA ===" in p

def test_ida_e_volta():
    original = {k: "" for k in ORDEM} | {"contato": "Ana", "resumo": "Dados", "experiencia": "Empresa X\n- Fiz pipelines"}
    resposta = "\n".join(f"=== {k.upper()} ===\n{v}" for k, v in original.items() if v)
    assert ler_resposta(resposta) == original

def test_resposta_com_markdown_e_acentos():
    texto = "```\n**=== Experiência ===**\nEmpresa X\n### === RESUMO ===\nDados\n```"
    s = ler_resposta(texto)
    assert s["experiencia"] == "Empresa X" and s["resumo"] == "Dados"

def test_resposta_sem_marcadores_usa_titulos():
    s = ler_resposta("Ana\nProfessional Experience\nEmpresa X\nSkills\nPython")
    assert s["experiencia"] == "Empresa X" and s["habilidades"] == "Python"

def test_resposta_vazia_ou_irreconhecivel():
    with pytest.raises(RespostaInvalida):
        ler_resposta("   ")
```

- [ ] **Step 2: Rodar** — FAIL.
- [ ] **Step 3: Implementar** — `ler_resposta`: remove cercas ` ``` `, `**`, `__` e `#` iniciais; procura marcadores `=== X ===` (normalizando acento e caixa). Sem marcadores, cai em `dividir_secoes` (Task 2); se o resultado só tiver contato preenchido e o texto tiver mais de 3 linhas, levanta `RespostaInvalida("Não reconheci as seções da resposta. Peça ao chat para responder no formato com === SEÇÃO ===.")`.
- [ ] **Step 4: Rodar** — PASS.
- [ ] **Step 5: Commit** — `feat: prompt de copiar e colar e leitura da resposta`

---

### Task 6: Conferência da resposta da IA

**Files:**
- Create: `curriculo_ats/conferencia.py`
- Test: `tests/test_conferencia.py`

**Interfaces:**
- Consumes: `Termo`, `extrair_termos` (Task 4).
- Produces: `@dataclass(frozen=True) class Novidade: tipo: str  # "numero" | "termo" | "contato"; valor: str`; `conferir(original: str, resposta: str, termos: list[Termo]) -> list[Novidade]` (ordem: números, termos, contatos; sem repetição).

- [ ] **Step 1: Testes que falham**

```python
TERMOS = [Termo("Python", (), "linguagem"), Termo("Kubernetes", ("k8s",), "devops")]

def test_pega_numero_e_tecnologia_inventados():
    n = conferir("Usei Python por 3 anos", "Usei Python e Kubernetes por 3 anos e reduzi custos em 40%", TERMOS)
    assert Novidade("numero", "40%") in n and Novidade("termo", "Kubernetes") in n
    assert Novidade("numero", "3") not in n

def test_formatos_equivalentes_nao_sao_novidade():
    assert conferir("R$ 1.500 e 2.000 usuários", "R$1500 e 2000 usuários", TERMOS) == []

def test_email_novo():
    assert conferir("ana@x.com", "ana@x.com\nana.souza@gmail.com", TERMOS) == [Novidade("contato", "ana.souza@gmail.com")]

def test_nada_novo():
    assert conferir("Python 2020-2024", "Python (2020 - 2024)", TERMOS) == []
```

- [ ] **Step 2: Rodar** — FAIL.
- [ ] **Step 3: Implementar** — números: regex `\d[\d.,]*\s?%?`; normalizar removendo separadores de milhar e espaços, mantendo `%` (valor exibido = forma como apareceu na resposta). Termos: `extrair_termos` nos dois textos, diferença. Contatos: e-mails (`[\w.+-]+@[\w-]+\.[\w.]+`) e telefones (sequências com ≥ 8 dígitos) presentes só na resposta.
- [ ] **Step 4: Rodar** — PASS.
- [ ] **Step 5: Commit** — `feat: conferência de conteúdo novo na resposta`

---

### Task 7: Exportação ATS (.docx e PDF)

**Files:**
- Create: `curriculo_ats/exportar.py`
- Test: `tests/test_exportar.py`

**Interfaces:**
- Consumes: `Secoes`, `ORDEM` (Task 2), `TITULOS` (Task 3), `extrair_texto` (Task 1, usado nos testes para ler o resultado).
- Produces: `gerar_docx(secoes: Secoes, idioma: str) -> bytes`; `gerar_pdf(secoes: Secoes, idioma: str) -> bytes`; `nome_arquivo(secoes: Secoes, empresa: str | None, extensao: str) -> str`.

Layout: contato no topo (primeira linha em negrito, 14 pt; demais linhas 10 pt); cada seção com título em maiúsculas, negrito, 11 pt, seguido do conteúdo em 10-11 pt; linhas que começam com `-`, `*` ou `•` viram marcador simples (`List Bullet` no docx; `- ` no PDF). Fonte Arial (docx) / Helvetica (PDF), preto, margens de 2 cm.

- [ ] **Step 1: Testes que falham**

```python
SECOES = {k: "" for k in ORDEM} | {"contato": "Ana Souza\nana@x.com", "experiencia": "Empresa X\n- Fiz pipelines", "habilidades": "Python, SQL"}

def test_docx_ordem_titulos_e_sem_tabelas_ou_imagens():
    dados = gerar_docx(SECOES, "en")
    texto = extrair_texto("cv.docx", dados)
    assert texto.index("SKILLS") < texto.index("PROFESSIONAL EXPERIENCE")
    assert "PROJECTS" not in texto  # seção vazia omitida
    doc = docx.Document(io.BytesIO(dados))
    assert not doc.tables and not doc.inline_shapes
    assert not any(s.header.paragraphs[0].text for s in doc.sections)

def test_pdf_legivel():
    texto = extrair_texto("cv.pdf", gerar_pdf(SECOES, "pt"))
    assert "Ana Souza" in texto and "EXPERIÊNCIA PROFISSIONAL" in texto and "Fiz pipelines" in texto

def test_pdf_com_caracteres_fora_do_latin1():
    s = SECOES | {"resumo": "Dados – “ETL” • 10× mais rápido… 🚀"}
    texto = extrair_texto("cv.pdf", gerar_pdf(s, "pt"))
    assert "ETL" in texto and "mais rápido" in texto

def test_nome_arquivo():
    assert nome_arquivo(SECOES, "Nubank S.A.", "pdf") == "curriculo-ana-souza-nubank-s-a.pdf"
    assert nome_arquivo({k: "" for k in ORDEM}, None, "docx") == "curriculo-ats.docx"
```

- [ ] **Step 2: Rodar** — FAIL.
- [ ] **Step 3: Implementar** — PDF com fontes padrão do fpdf2 (latin-1): antes de escrever, trocar `– —` → `-`, `“ ” „` → `"`, `‘ ’` → `'`, `•` → `-`, `…` → `...`, `×` → `x`, e descartar o que ainda não couber em latin-1. `nome_arquivo`: slug (sem acento, minúsculo, não alfanumérico → `-`, sem `-` repetido) do nome (1ª linha do contato) e da empresa.
- [ ] **Step 4: Rodar** — PASS.
- [ ] **Step 5: Commit** — `feat: exportação ATS em docx e PDF`

---

### Task 8: Interface Streamlit

**Files:**
- Create: `app.py`
- Test: `tests/test_app.py` (com `streamlit.testing.v1.AppTest`)

**Interfaces:**
- Consumes: tudo das Tasks 1-7.
- Produces: `app.py` executável com `streamlit run app.py`. Estado em `st.session_state["secoes"]` (`Secoes`), `["analise"]` (`Analise`), `["secoes_finais"]` (`Secoes`).

Tela (textos em português, etapas numeradas como no spec):
1. `st.file_uploader` (pdf, docx) → `extrair_texto` → `dividir_secoes`; erro de `ArquivoIlegivel` com `st.error`. Um `st.text_area` por seção de `ORDEM` (rótulo com o título em português), editável. Botão "Usar o exemplo" (`key="usar_exemplo"`) carrega `exemplos/curriculo_exemplo.docx` e `exemplos/vaga_exemplo.txt`.
2. `st.text_area` da vaga + `st.text_input` "Empresa (opcional)".
3. Compatibilidade: `st.metric` com a nota, listas de encontradas e faltando, e o aviso: "As palavras faltando são para você conferir se tem e esqueceu de citar. Não acrescente o que você não tem."
4. `st.radio` com "Só formatar para ATS (sem IA)" e "Reescrever com um chat de IA gratuito (copiar e colar)".
   - Sem IA: idioma = `detectar_idioma(currículo)`; se ≠ idioma da vaga, `st.info` sugerindo o modo com IA. Habilidades passam por `priorizar_habilidades`.
   - Com IA: `st.code(montar_prompt(...))` (tem botão de copiar), links para chatgpt.com, claude.ai e gemini.google.com, aviso de privacidade ("o seu currículo vai para o serviço que você escolher"), `st.text_area` para a resposta → `ler_resposta` → `conferir` (lista de novidades com `st.warning`) → nova nota com `analisar`. Idioma = idioma da vaga.
5. `st.download_button` para `.docx` e `.pdf` com `nome_arquivo`.

- [ ] **Step 1: Testes que falham**

```python
def test_app_abre_sem_erro():
    at = AppTest.from_file("app.py").run()
    assert not at.exception

def test_exemplo_gera_nota_e_downloads():
    at = AppTest.from_file("app.py").run()
    at.button(key="usar_exemplo").click().run()
    assert not at.exception
    assert at.metric[0].value.endswith("%")
```

- [ ] **Step 2: Rodar** — FAIL (depende de `exemplos/`: criar já aqui um `.docx` e uma vaga fictícios mínimos; a Task 9 os completa).
- [ ] **Step 3: Implementar `app.py`**.
- [ ] **Step 4: Rodar** — `pytest -v`. Esperado: PASS. Depois `streamlit run app.py` e conferir no navegador as 5 etapas, os dois caminhos e os downloads.
- [ ] **Step 5: Commit** — `feat: interface Streamlit`

---

### Task 9: Execução em dois cliques, exemplos, README e CI

**Files:**
- Create: `iniciar.bat`, `iniciar.sh`, `exemplos/curriculo_exemplo.docx` (gerado por `exemplos/gerar_exemplo.py`), `exemplos/vaga_exemplo.txt`, `.github/workflows/testes.yml`, `README.md`
- Test: `tests/test_exemplos.py`

**Interfaces:**
- Consumes: todos os módulos.

`iniciar.bat`: procura `py -3` e depois `python`; sem Python, mostra "Python não encontrado. Veja o passo 1 do README." e pausa. Cria `.venv` se não existir, instala `requirements.txt` (só na primeira vez ou se `requirements.txt` mudou: guardar uma cópia em `.venv\requirements.instalado`), roda `streamlit run app.py`. `iniciar.sh`: o mesmo com `python3`, executável (`git update-index --chmod=+x`).

Exemplo fictício: "Ana Souza", analista de dados (Python, SQL, Power BI, Excel), com experiência, formação e idiomas; vaga de "Engenheira de Dados" que pede Python, SQL, dbt, Airflow, AWS e inglês.

CI: `ubuntu-latest` e `windows-latest`, Python 3.10 e 3.12, `pip install -r requirements.txt -r requirements-dev.txt`, `pytest`.

README: as 10 seções do spec, nessa ordem, em português simples. Capturas de tela em `docs/imagens/` (tiradas do app rodando com o exemplo).

- [ ] **Step 1: Teste que falha**

```python
def test_exemplo_de_ponta_a_ponta():
    texto = extrair_texto("cv.docx", Path("exemplos/curriculo_exemplo.docx").read_bytes())
    secoes = dividir_secoes(texto)
    a = analisar(texto, Path("exemplos/vaga_exemplo.txt").read_text(encoding="utf-8"), carregar_termos())
    assert secoes["experiencia"] and secoes["formacao"]
    assert "dbt" in a.faltando and "Python" in a.encontradas
    assert gerar_pdf(secoes, "pt").startswith(b"%PDF")
```

- [ ] **Step 2: Rodar** — FAIL.
- [ ] **Step 3: Gerar os exemplos, escrever os scripts, o workflow e o README**.
- [ ] **Step 4: Verificar** — `pytest -v` (PASS); dois cliques em `iniciar.bat` numa pasta copiada sem `.venv` abre o app; README revisado lendo como alguém que nunca programou.
- [ ] **Step 5: Commit** — `docs: README, exemplos, scripts de execução e CI`
- [ ] **Step 6: Publicar (pedir confirmação ao usuário antes)** — `gh repo create ArthurTheWorld/curriculo-ats --public --source=. --push` e conferir o CI verde.
