# curriculo-ats: design

Data: 2026-11-18 · Autor: Luiz Arthur

## Intenção

Uma ferramenta gratuita para qualquer pessoa adaptar o próprio currículo a uma vaga e deixá-lo legível por sistemas ATS (os filtros automáticos que empresas usam antes de um recrutador ler o currículo).

O motivo de ser um projeto separado do Ultron: precisa ser **fácil de compartilhar com outras pessoas**. Por isso:

- roda na máquina de quem usa, a partir do GitHub (sem servidor, sem custo para o autor);
- **não exige chave de API nem conta paga** de nada;
- o README precisa ser o mais explicativo possível, para quem nunca programou.

## Objetivos

1. Ler o currículo atual da pessoa (PDF com texto ou Word `.docx`).
2. Ler a descrição de uma vaga (texto colado).
3. Mostrar a **compatibilidade** entre currículo e vaga: nota de 0 a 100%, palavras-chave encontradas e faltando.
4. Gerar um currículo em **formato amigável para ATS** (`.docx` e PDF).
5. **Modo IA sem chave ("copiar e colar")**: montar um prompt pronto para a pessoa colar em qualquer chat gratuito (ChatGPT, Claude, Gemini), receber a resposta de volta e transformá-la no currículo final.
6. **Conferir a resposta da IA**: apontar números e tecnologias que aparecem na resposta e não estavam no currículo original.
7. Instalação e uso com dois cliques (`iniciar.bat` no Windows, `iniciar.sh` no Mac/Linux).

## Não objetivos

- Hospedar o app na internet.
- Chamar qualquer API de IA diretamente (nem com chave da pessoa, nem do autor).
- IA local (Ollama): fica listada como melhoria futura no README.
- Ler PDF escaneado (imagem). O app avisa e pede um PDF com texto ou um `.docx`.
- Guardar currículos, contas ou histórico. Nada é salvo além dos arquivos que a pessoa baixa.
- Gerar carta de apresentação.

## Antiobjetivos (seria um fracasso mesmo funcionando)

- **Inventar** experiência, número, cargo ou tecnologia que a pessoa não tem. A ferramenta nunca acrescenta conteúdo por conta própria; o modo sem IA só reorganiza e aponta, e a resposta da IA é conferida.
- Exigir que a pessoa use terminal, crie conta ou pague algo para o caso básico.
- Enviar o currículo a qualquer servidor sem a pessoa fazer isso explicitamente (no modo copiar e colar, ela mesma cola no chat que escolher; o README deixa isso claro).
- Produzir um currículo "bonito" que o ATS não consegue ler (colunas, tabelas, ícones, cabeçalho em imagem).

## Restrições

- Python 3.10 ou mais novo. Bibliotecas só de Python puro e populares, sem dependência de sistema (nada de LibreOffice, Tesseract, wkhtmltopdf).
- Funciona offline no modo sem IA.
- Interface em português do Brasil. O currículo gerado sai no **idioma da vaga** (português ou inglês).
- Repositório público `ArthurTheWorld/curriculo-ats`, licença MIT, com testes e CI.

## Abordagens consideradas

**Forma de uso**

| Opção | Troca | Decisão |
|---|---|---|
| A. App local no navegador (Streamlit) aberto por `iniciar.bat`/`iniciar.sh` | Amigável para leigos; precisa de Python instalado (o README ensina) | **Escolhida** (decisão do Claude, depois que o usuário escolheu rodar localmente a partir do GitHub) |
| B. Linha de comando | Código mais simples; quem não usa terminal desiste | Descartada |
| C. Executável `.exe` | Dois cliques sem Python; arquivo pesado, antivírus bloqueia, só Windows | Descartada |

**Como a "inteligência" funciona** (sem chave de API, decisão do usuário)

| Opção | Troca | Decisão |
|---|---|---|
| 1. IA local (Ollama) | Sem chave e privado; exige 8 GB+ de RAM, download de 4-5 GB, lento, pior em português | Futuro |
| 2. Sem IA: análise de palavras-chave e formatação por código | Instantâneo, nunca inventa; não reescreve frases | **Escolhida** (usuário) |
| 3. Copiar e colar com chat gratuito | Reescrita de qualidade sem chave; dois passos manuais; o currículo passa pelo chat escolhido | **Escolhida** (usuário) |

## Como funciona

### Fluxo na tela

Uma página única, em etapas numeradas:

```
1. Seu currículo      [enviar PDF ou .docx]
   → o app mostra as seções que reconheceu, cada uma num campo editável
     (Contato, Resumo, Experiência, Formação, Habilidades, Idiomas, Certificações, Projetos, Outros)
2. A vaga             [colar o texto]
3. Compatibilidade    Nota 62%  ·  Encontradas: Python, SQL, Airflow…  ·  Faltando: dbt, Terraform…
                      (avisos: "Faltando" é para você conferir se tem e esqueceu de citar, não para inventar)
4. Escolha o caminho
   ( ) Só formatar para ATS (sem IA)
   ( ) Reescrever com um chat de IA gratuito (copiar e colar)
5. Baixar             [.docx]  [.pdf]
```

No caminho com IA, a etapa 4 mostra:
- o prompt pronto com botão de copiar;
- links para os chats gratuitos;
- um campo para colar a resposta;
- o resultado da conferência (ex.: "A resposta cita **Kubernetes** e **40%**, que não estão no seu currículo. Confira antes de usar.");
- a nova nota de compatibilidade, para comparar com a anterior.

Depois de colar a resposta, as seções editáveis são preenchidas com ela, e a pessoa pode ajustar antes de baixar.

### Componentes (módulos independentes, testáveis sem a interface)

| Módulo | Responsabilidade |
|---|---|
| `leitura.py` | Extrai texto de PDF (`pdfplumber`) e `.docx` (`python-docx`). Detecta PDF sem texto e devolve erro claro. |
| `secoes.py` | Divide o texto em seções reconhecendo títulos comuns em PT e EN (ex.: "Experiência Profissional", "Work Experience", "Formação Acadêmica", "Education", "Skills"). O que não reconhecer vai para "Outros". Linhas antes do primeiro título viram "Contato". |
| `palavras_chave.py` | Extrai palavras-chave da vaga e compara com o currículo. Usa um **dicionário de termos** (tecnologias, ferramentas, metodologias, certificações e idiomas, com sinônimos: "Power BI" = "PowerBI", "JS" = "JavaScript") em `dados/termos.yaml`, mais termos da vaga escritos com inicial maiúscula ou em formato técnico que se repetem. Normaliza acentos e caixa. Nota = termos da vaga encontrados ÷ termos da vaga. |
| `idioma.py` | Detecta se a vaga está em português ou inglês por palavras frequentes. Define os títulos das seções no arquivo final. |
| `prompt.py` | Monta o prompt do modo copiar e colar com: regras (não inventar nada, manter datas, cargos e empresas, usar as palavras-chave da vaga só onde forem verdade, idioma da vaga), o currículo por seções, a vaga e o **formato de resposta** com marcadores de seção (`=== EXPERIENCIA ===`), para o app conseguir ler a resposta. |
| `resposta.py` | Lê a resposta colada pelos marcadores. Se faltar marcador, tenta reconhecer os títulos como em `secoes.py`; se não der, avisa. |
| `conferencia.py` | Compara resposta com o original: números (inclusive %, R$, anos), termos do dicionário e e-mails/telefones que aparecem só na resposta. Devolve a lista de itens novos. |
| `exportar.py` | Gera `.docx` (`python-docx`) e PDF (`fpdf2`) no **layout ATS**: uma coluna, fonte padrão (Arial/Helvetica 10-11), títulos de seção em texto simples e padronizados, marcadores simples, sem tabelas, caixas de texto, ícones, imagens, cabeçalho/rodapé ou cores. Nome do arquivo: `curriculo-<nome>-<empresa ou "vaga">.docx`. |
| `app.py` | Interface Streamlit que só orquestra os módulos. |

### Instalação e execução

- `iniciar.bat` / `iniciar.sh`: verifica se há Python; se não houver, mostra a mensagem com o link e o passo do README. Na primeira vez cria `.venv` e instala `requirements.txt`; depois abre `streamlit run app.py` (o navegador abre sozinho).
- Sem `.env`, sem configuração.

### README (o mais explicativo possível)

Seções, nesta ordem:
1. O que é, em duas frases, com uma captura de tela.
2. O que é um ATS e por que o formato importa (curto, linguagem simples).
3. **Passo a passo para quem nunca programou**: instalar o Python no Windows (marcar "Add Python to PATH", com imagem) e no Mac; baixar o projeto pelo botão "Code → Download ZIP"; extrair; dois cliques em `iniciar.bat`.
4. Como usar, etapa por etapa, com capturas.
5. Modo com IA: como usar o ChatGPT, Claude ou Gemini gratuitos, e o aviso de que o currículo vai para aquele serviço.
6. Privacidade: o que fica na máquina e o que não fica.
7. Perguntas frequentes e problemas comuns ("o Windows não reconhece python", "PDF escaneado", "a nota está baixa: devo copiar todas as palavras?" → não).
8. Para desenvolvedores: estrutura, testes, como contribuir, como acrescentar termos ao dicionário.
9. Próximos passos (Ollama, mais idiomas, carta de apresentação).
10. Autor e licença.

### Qualidade

- Testes com `pytest` para todos os módulos, sem a interface: leitura de PDF/.docx de exemplo (gerados nos testes), divisão em seções PT/EN, extração e nota de palavras-chave, detecção de idioma, ida e volta do prompt e da resposta, conferência (pega número e tecnologia inventados) e exportação (o `.docx` e o PDF gerados têm o texto esperado e nenhuma tabela/imagem).
- CI no GitHub Actions rodando os testes em Windows e Ubuntu.
- Um currículo e uma vaga de exemplo fictícios em `exemplos/`, usados nos testes e no README.

## Decisões do usuário

- Projeto novo, separado do Ultron, para ser fácil de compartilhar.
- Roda na máquina de cada pessoa a partir do GitHub, com README o mais explicativo possível.
- Sem chaves de API: análise e formatação por código + modo copiar e colar com chat gratuito.

## Decisões do Claude (para o usuário conferir)

- Interface Streamlit local aberta por script de dois cliques.
- Bibliotecas: `streamlit`, `pdfplumber`, `python-docx`, `fpdf2`, `pyyaml`; testes com `pytest`.
- Currículo final no idioma da vaga; interface em português.
- Seções editáveis na tela, porque a divisão automática do currículo nunca é perfeita.
- Dicionário de termos próprio e editável, em vez de modelo de linguagem ou biblioteca de NLP pesada.
- Nome e local: `curriculo-ats`, em `C:\Users\luiza\Projetos\curriculo-ats`, repositório público.
- **Idioma no modo sem IA:** o código não traduz conteúdo. Os títulos das seções seguem o idioma do próprio currículo; se a vaga estiver em outro idioma, a tela avisa e sugere o modo com IA. No modo com IA, tudo sai no idioma da vaga.
- **Ordem das seções no arquivo final:** Contato, Resumo, Habilidades, Experiência, Projetos, Formação, Certificações, Idiomas, Outros (seções vazias são omitidas).
- **Ajuda sem inventar no modo sem IA:** na seção Habilidades, os termos que a vaga pede e o currículo já tem vão para o começo da lista. Nada é acrescentado.
- **Nome do arquivo:** o nome vem da primeira linha da seção Contato; a empresa, de um campo opcional na etapa 2. Sem eles, `curriculo-ats.docx`.
- **Idioma do README e da interface:** português. Uma versão em inglês fica para depois.

## Deixado para quem constrói

- Lista inicial de termos do dicionário (começar por dados, engenharia de software, nuvem, metodologias e idiomas; algumas centenas de termos).
- Texto exato do prompt, desde que siga as regras acima.
- Detalhes visuais da página Streamlit, mantendo as etapas numeradas.
