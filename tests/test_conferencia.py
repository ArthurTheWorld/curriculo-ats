from curriculo_ats.conferencia import Novidade, conferir
from curriculo_ats.palavras_chave import Termo

TERMOS = [Termo("Python", (), "linguagem"), Termo("Kubernetes", ("k8s",), "devops")]


def test_pega_numero_e_tecnologia_inventados():
    n = conferir("Usei Python por 3 anos", "Usei Python e Kubernetes por 3 anos e reduzi custos em 40%", TERMOS)
    assert Novidade("numero", "40%") in n and Novidade("termo", "Kubernetes") in n
    assert Novidade("numero", "3") not in n


def test_formatos_equivalentes_nao_sao_novidade():
    assert conferir("R$ 1.500 e 2.000 usuários", "R$1500 e 2000 usuários", TERMOS) == []


def test_email_novo():
    assert conferir("ana@x.com", "ana@x.com\nana.souza@gmail.com", TERMOS) == [Novidade("contato", "ana.souza@gmail.com")]


def test_telefone_novo_nao_vira_numero_tambem():
    n = conferir("ana@x.com", "ana@x.com\n(11) 98765-4321", TERMOS)
    assert n == [Novidade("contato", "(11) 98765-4321")]


def test_nada_novo():
    assert conferir("Python 2020-2024", "Python (2020 - 2024)", TERMOS) == []


def test_ordem_numeros_termos_contatos_sem_repeticao():
    n = conferir("", "40% e 40% com k8s e Kubernetes, ana@y.com", TERMOS)
    assert n == [Novidade("numero", "40%"), Novidade("termo", "Kubernetes"), Novidade("contato", "ana@y.com")]
