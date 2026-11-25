"""
Funções de validação. O back-end nunca confia no que vem do navegador:
tudo é conferido de novo aqui.
"""

import re

PADRAO_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PADRAO_NOME_DOMINIO = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")


def so_digitos(texto):
    """Remove tudo que não é número. Ex.: '123.456.789-09' -> '12345678909'"""
    return re.sub(r"\D", "", texto or "")


def cpf_valido(cpf):
    """
    Confere os dois dígitos verificadores do CPF.

    Parâmetros:
        cpf (str): só números, 11 dígitos

    Retorna:
        bool: True se o CPF for válido
    """
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for posicao in (9, 10):
        soma = sum(int(cpf[i]) * (posicao + 1 - i) for i in range(posicao))
        digito = (soma * 10) % 11 % 10
        if digito != int(cpf[posicao]):
            return False

    return True


def cnpj_valido(cnpj):
    """
    Confere os dois dígitos verificadores do CNPJ.

    Parâmetros:
        cnpj (str): só números, 14 dígitos

    Retorna:
        bool: True se o CNPJ for válido
    """
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos_2 = [6] + pesos_1

    for pesos, posicao in ((pesos_1, 12), (pesos_2, 13)):
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(posicao))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if digito != int(cnpj[posicao]):
            return False

    return True


def documento_valido(documento):
    """Aceita CPF (11 dígitos) ou CNPJ (14 dígitos)."""
    numeros = so_digitos(documento)
    if len(numeros) == 11:
        return cpf_valido(numeros)
    if len(numeros) == 14:
        return cnpj_valido(numeros)
    return False


def email_valido(email):
    return bool(email) and len(email) <= 120 and bool(PADRAO_EMAIL.match(email))


def separar_dominio(dominio, tlds):
    """
    Separa 'meusite.com.br' em ('meusite', 'com.br').

    Parâmetros:
        dominio (str): domínio completo
        tlds (iterable): extensões aceitas pelo site

    Retorna:
        tuple | None: (nome, tld), ou None se o domínio for inválido
    """
    dominio = (dominio or "").strip().lower()

    # Testa as extensões maiores primeiro: "com.br" antes de "br"
    for tld in sorted(tlds, key=len, reverse=True):
        if dominio.endswith("." + tld):
            nome = dominio[: -(len(tld) + 1)]
            if not PADRAO_NOME_DOMINIO.match(nome):
                return None
            if tld.endswith("br") and not 2 <= len(nome) <= 26:
                return None
            return nome, tld

    return None
