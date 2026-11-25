"""
Regras dos pedidos: criar, receber o aviso de pagamento e registrar os domínios.

Regras principais:
- O preço SEMPRE é calculado aqui no servidor, a partir do site.json.
- O domínio só é registrado DEPOIS que o Mercado Pago confirma o pagamento.
"""

import re
import secrets
import threading

import banco
import disponibilidade
import email_envio
import pagamento
import provedor
from configuracao import ANOS_MAXIMO, extensoes_por_tld
from http_util import ErroApi
from validacao import documento_valido, email_valido, separar_dominio, so_digitos

UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
    "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


class ErroPedido(Exception):
    """Erro com mensagem que pode ser mostrada para o visitante."""


# ---------------------------------------------------------------- validação

def _texto(dados, campo, minimo, maximo, mensagem):
    valor = re.sub(r"\s+", " ", str(dados.get(campo, ""))).strip()
    if not minimo <= len(valor) <= maximo:
        raise ErroPedido(mensagem)
    return valor


def _validar_titular(dados):
    """
    Confere os dados do titular. Os registros de domínio exigem
    nome, e-mail, telefone e endereço de quem vai ser o dono.
    """
    email = str(dados.get("email", "")).strip()
    documento = so_digitos(str(dados.get("documento", "")))
    telefone = so_digitos(str(dados.get("telefone", "")))
    cep = so_digitos(str(dados.get("cep", "")))
    estado = str(dados.get("estado", "")).strip().upper()

    titular = {
        "nome": _texto(dados, "nome", 3, 120, "Informe o nome completo ou a razão social."),
        "email": email,
        "documento": documento,
        "telefone": telefone,
        "endereco": _texto(dados, "endereco", 5, 120, "Informe o endereço com número."),
        "cidade": _texto(dados, "cidade", 2, 80, "Informe a cidade."),
        "estado": estado,
        "cep": cep,
    }

    if not email_valido(email):
        raise ErroPedido("Informe um e-mail válido.")
    if not documento_valido(documento):
        raise ErroPedido("CPF ou CNPJ inválido.")
    if len(telefone) not in (10, 11):
        raise ErroPedido("Informe o telefone com DDD.")
    if len(cep) != 8:
        raise ErroPedido("O CEP precisa ter 8 dígitos.")
    if estado not in UFS:
        raise ErroPedido("Escolha o estado (UF).")

    return titular


def _validar_itens(itens):
    """
    Confere cada domínio do carrinho e calcula o preço de cada um.

    Retorna:
        list[dict]: itens com "dominio", "anos", "valor" e "status"
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
        validados.append({"dominio": dominio, "anos": anos, "valor": round(valor, 2), "status": "aguardando"})

    return validados


# ---------------------------------------------------------------- criar pedido

def criar_pedido(dados):
    """
    Valida, grava o pedido e cria a cobrança no Mercado Pago.

    Parâmetros:
        dados (dict): {"titular": {...}, "aceiteTermos": true, "itens": [...]}

    Retorna:
        dict: {"pedido": código, "total": valor, "pagamentoUrl": link}
    """
    if not pagamento.pagamento_configurado():
        raise ErroPedido("Os pagamentos ainda não estão ativos neste site.")
    if dados.get("aceiteTermos") is not True:
        raise ErroPedido("É preciso aceitar os termos e as políticas.")

    titular = _validar_titular(dados.get("titular") or {})
    itens = _validar_itens(dados.get("itens"))

    pedido = {
        "codigo": "Z-" + secrets.token_hex(5).upper(),
        "criadoEm": banco.agora(),
        "status": "aguardando_pagamento",
        "titular": titular,
        "itens": itens,
        "total": round(sum(item["valor"] for item in itens), 2),
    }
    banco.salvar_pedido(pedido)

    try:
        cobranca = pagamento.criar_cobranca(pedido)
    except ErroApi as erro:
        print(f"[Mercado Pago] erro ao criar cobrança de {pedido['codigo']}: {erro}")
        raise ErroPedido("Não foi possível gerar o pagamento agora. Tente novamente em instantes.")

    banco.atualizar_pedido(pedido["codigo"], preferencia_id=cobranca["id"])

    return {"pedido": pedido["codigo"], "total": pedido["total"], "pagamentoUrl": cobranca["link"]}


# ---------------------------------------------------------------- pagamento

def processar_notificacao(pagamento_id):
    """
    Chamado quando o Mercado Pago avisa sobre um pagamento.
    Consulta o pagamento direto no Mercado Pago (nunca confia só no aviso).
    """
    dados = pagamento.buscar_pagamento(pagamento_id)
    codigo = dados.get("external_reference")
    pedido = banco.buscar_pedido(codigo) if codigo else None

    if not pedido:
        print(f"[pagamento {pagamento_id}] pedido não encontrado: {codigo}")
        return

    situacao = dados.get("status")

    if situacao == "approved":
        valor_pago = float(dados.get("transaction_amount") or 0)
        if dados.get("currency_id") != "BRL" or valor_pago + 0.01 < pedido["total"]:
            email_envio.avisar_admin(
                "Pagamento com valor diferente",
                f"Pedido {codigo}: total R$ {pedido['total']:.2f}, pago {valor_pago:.2f} "
                f"{dados.get('currency_id')}. Verifique manualmente (pagamento {pagamento_id}).",
            )
            return

        # Só a primeira notificação aprovada dispara o registro
        if banco.marcar_como_pago(codigo, pagamento_id):
            threading.Thread(target=registrar_pedido, args=(codigo,), daemon=True).start()

    elif situacao in ("rejected", "cancelled", "refunded", "charged_back"):
        if pedido["status"] == "aguardando_pagamento":
            banco.atualizar_pedido(codigo, status="cancelado", pagamento_id=pagamento_id)


def registrar_pedido(codigo):
    """Registra na Dynadot todos os domínios de um pedido pago."""
    pedido = banco.buscar_pedido(codigo)
    contato_id = None

    for item in pedido["itens"]:
        if item.get("status") == "registrado":
            continue
        resultado = provedor.registrar_dominio(item["dominio"], item["anos"], pedido["titular"], contato_id)
        contato_id = resultado["contato_id"] or contato_id
        item["status"] = resultado["status"]
        item["detalhe"] = resultado["detalhe"]

    tudo_certo = all(item["status"] == "registrado" for item in pedido["itens"])
    pedido["status"] = "concluido" if tudo_certo else "registro_pendente"
    banco.atualizar_pedido(codigo, status=pedido["status"], itens=pedido["itens"])

    email_envio.avisar_cliente_pedido_concluido(pedido)

    resumo = "\n".join(
        f"- {item['dominio']} ({item['anos']} ano/s): {item['status']} — {item.get('detalhe', '')}"
        for item in pedido["itens"]
    )
    email_envio.avisar_admin(
        "Nova venda" if tudo_certo else "Venda com domínio para registrar manualmente",
        f"Pedido {codigo} — R$ {pedido['total']:.2f}\nTitular: {pedido['titular']['nome']} "
        f"<{pedido['titular']['email']}>\n\n{resumo}",
    )


# ---------------------------------------------------------------- consultas

TEXTO_STATUS = {
    "aguardando_pagamento": "Aguardando pagamento",
    "pago": "Pagamento aprovado — registrando seus domínios",
    "concluido": "Concluído",
    "registro_pendente": "Pagamento aprovado — registro em andamento",
    "cancelado": "Pagamento não aprovado",
}


def consultar_pedido(codigo):
    """
    Situação de um pedido para a página "Meu pedido".
    Não devolve dados pessoais, só os domínios e a situação.
    """
    pedido = banco.buscar_pedido(str(codigo or "").upper())
    if not pedido:
        raise ErroPedido("Pedido não encontrado.")

    return {
        "codigo": pedido["codigo"],
        "status": pedido["status"],
        "statusTexto": TEXTO_STATUS.get(pedido["status"], pedido["status"]),
        "total": pedido["total"],
        "itens": [
            {"dominio": item["dominio"], "anos": item["anos"], "status": item.get("status", "aguardando")}
            for item in pedido["itens"]
        ],
    }


def registrar_contato(dados):
    """Guarda uma mensagem do formulário de contato e avisa você por e-mail."""
    if dados.get("aceite") is not True:
        raise ErroPedido("É preciso concordar com o uso dos dados para responder.")

    contato = {
        "nome": _texto(dados, "nome", 2, 120, "Informe seu nome."),
        "email": str(dados.get("email", "")).strip(),
        "assunto": str(dados.get("assunto", ""))[:80],
        "mensagem": str(dados.get("mensagem", "")).strip()[:2000],
    }
    if not email_valido(contato["email"]) or len(contato["mensagem"]) < 5:
        raise ErroPedido("Preencha e-mail e mensagem.")

    banco.salvar_contato(contato)
    email_envio.avisar_admin(
        f"Contato: {contato['assunto']}",
        f"De: {contato['nome']} <{contato['email']}>\n\n{contato['mensagem']}",
    )
