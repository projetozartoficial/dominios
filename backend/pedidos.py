"""
Criação de pedidos e registro de mensagens de contato.

Regra principal: o preço SEMPRE é calculado aqui no servidor, a partir do
site.json. O valor que aparece no navegador é só para mostrar.
"""

import json
import secrets
import threading
from datetime import datetime, timezone

import disponibilidade
import pagamento
from configuracao import ANOS_MAXIMO, PASTA_DADOS, extensoes_por_tld
from validacao import documento_valido, email_valido, separar_dominio, so_digitos

_trava = threading.Lock()  # evita que dois pedidos escrevam no arquivo ao mesmo tempo


class ErroPedido(Exception):
    """Erro com mensagem que pode ser mostrada para o visitante."""


def _agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _salvar(nome_arquivo, registro):
    """Acrescenta um registro a um arquivo JSON dentro de backend/dados/."""
    PASTA_DADOS.mkdir(exist_ok=True)
    caminho = PASTA_DADOS / nome_arquivo

    with _trava:
        registros = json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else []
        registros.append(registro)
        caminho.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")


def _validar_titular(titular):
    nome = str(titular.get("nome", "")).strip()
    email = str(titular.get("email", "")).strip()
    documento = so_digitos(str(titular.get("documento", "")))

    if len(nome) < 3:
        raise ErroPedido("Informe o nome completo ou a razão social.")
    if not email_valido(email):
        raise ErroPedido("Informe um e-mail válido.")
    if not documento_valido(documento):
        raise ErroPedido("CPF ou CNPJ inválido.")

    # Só os dados necessários são guardados
    return {"nome": nome[:120], "email": email, "documento": documento}


def _validar_itens(itens):
    """
    Confere cada domínio do carrinho e calcula o preço de cada um.

    Retorna:
        list[dict]: itens com "dominio", "anos" e "valor"
    """
    if not isinstance(itens, list) or not itens:
        raise ErroPedido("O carrinho está vazio.")
    if len(itens) > 20:
        raise ErroPedido("Limite de 20 domínios por pedido.")

    extensoes = extensoes_por_tld()
    validados = []
    vistos = set()

    for item in itens:
        separado = separar_dominio(item.get("dominio"), extensoes.keys())
        if not separado:
            raise ErroPedido(f"Domínio inválido: {item.get('dominio')}")

        nome, tld = separado
        dominio = f"{nome}.{tld}"
        extensao = extensoes[tld]

        if dominio in vistos:
            continue
        vistos.add(dominio)

        if extensao["modo"] != "revenda":
            raise ErroPedido(f"A extensão .{tld} não é vendida diretamente por aqui.")

        anos = item.get("anos")
        if not isinstance(anos, int) or not 1 <= anos <= ANOS_MAXIMO:
            raise ErroPedido(f"Período inválido para {dominio}.")

        if disponibilidade.verificar(dominio, extensao) == "registrado":
            raise ErroPedido(f"{dominio} acabou de ser registrado por outra pessoa.")

        # 1º ano pelo preço de registro, os demais pelo preço de renovação
        valor = extensao["preco"] + extensao["renovacao"] * (anos - 1)
        validados.append({"dominio": dominio, "anos": anos, "valor": round(valor, 2)})

    return validados


def criar_pedido(dados):
    """
    Valida e cria um pedido.

    Parâmetros:
        dados (dict): {"titular": {...}, "aceiteTermos": bool, "itens": [...]}

    Retorna:
        dict: {"pedido": código, "total": valor, "pagamentoUrl": link ou None}
    """
    if dados.get("aceiteTermos") is not True:
        raise ErroPedido("É preciso aceitar os termos e as políticas.")

    titular = _validar_titular(dados.get("titular") or {})
    itens = _validar_itens(dados.get("itens"))
    total = round(sum(item["valor"] for item in itens), 2)

    pedido = {
        "codigo": "P-" + secrets.token_hex(4).upper(),
        "criadoEm": _agora(),
        "status": "aguardando_pagamento",
        "titular": titular,
        "itens": itens,
        "total": total,
    }

    _salvar("pedidos.json", pedido)

    return {
        "pedido": pedido["codigo"],
        "total": total,
        "pagamentoUrl": pagamento.criar_cobranca(pedido),
    }


def registrar_contato(dados):
    """Guarda uma mensagem do formulário de contato."""
    nome = str(dados.get("nome", "")).strip()
    email = str(dados.get("email", "")).strip()
    mensagem = str(dados.get("mensagem", "")).strip()

    if dados.get("aceite") is not True:
        raise ErroPedido("É preciso concordar com o uso dos dados para responder.")
    if len(nome) < 2 or not email_valido(email) or len(mensagem) < 5:
        raise ErroPedido("Preencha nome, e-mail e mensagem.")

    _salvar("contatos.json", {
        "recebidoEm": _agora(),
        "nome": nome[:120],
        "email": email,
        "assunto": str(dados.get("assunto", ""))[:80],
        "mensagem": mensagem[:2000],
    })
