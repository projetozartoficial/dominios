"""
Ligação com o Mercado Pago (Checkout Pro).

Fluxo:
    1. criar_cobranca() cria uma "preferência" e devolve o link de pagamento
       (Pix, cartão ou boleto, na página do próprio Mercado Pago).
    2. O cliente paga.
    3. O Mercado Pago avisa o nosso servidor em /api/pagamento/notificacao.
    4. assinatura_valida() confere se o aviso veio mesmo do Mercado Pago.
    5. buscar_pagamento() consulta o pagamento e confirma se foi aprovado.

Chaves no .env:
    MERCADOPAGO_ACCESS_TOKEN      (Suas integrações > Credenciais)
    MERCADOPAGO_SEGREDO_WEBHOOK   (Suas integrações > Webhooks > Assinatura secreta)
"""

import hashlib
import hmac

from configuracao import MP_SEGREDO_WEBHOOK, MP_TOKEN, URL_API, URL_SITE
from http_util import requisitar

URL_MP = "https://api.mercadopago.com"


def pagamento_configurado():
    return bool(MP_TOKEN)


def _cabecalhos():
    return {"Authorization": f"Bearer {MP_TOKEN}"}


def criar_cobranca(pedido):
    """
    Cria a cobrança (preferência) do pedido.

    Parâmetros:
        pedido (dict): pedido já validado, com "codigo", "titular" e "itens"

    Retorna:
        dict | None: {"id": id da preferência, "link": link de pagamento},
                     ou None se o Mercado Pago ainda não foi configurado
    """
    if not pagamento_configurado():
        return None

    url_pedido = f"{URL_SITE}/pedido.html?codigo={pedido['codigo']}"

    preferencia = {
        "items": [
            {
                "id": item["dominio"],
                "title": f"Domínio {item['dominio']} ({item['anos']} {'ano' if item['anos'] == 1 else 'anos'})",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": item["valor"],
            }
            for item in pedido["itens"]
        ],
        "payer": {
            "name": pedido["titular"]["nome"],
            "email": pedido["titular"]["email"],
        },
        "external_reference": pedido["codigo"],
        "back_urls": {
            "success": url_pedido,
            "pending": url_pedido,
            "failure": url_pedido,
        },
        "notification_url": f"{URL_API}/api/pagamento/notificacao",
        "statement_descriptor": "ZART DOMINIOS",
    }

    # O Mercado Pago só aceita voltar sozinho para endereços https
    if URL_SITE.startswith("https://"):
        preferencia["auto_return"] = "approved"

    resposta = requisitar("POST", f"{URL_MP}/checkout/preferences", _cabecalhos(), preferencia)
    return {"id": resposta.get("id"), "link": resposta.get("init_point")}


def assinatura_valida(cabecalho_assinatura, id_requisicao, id_dado):
    """
    Confere o cabeçalho x-signature enviado pelo Mercado Pago.

    O cabeçalho tem o formato "ts=1704908010,v1=618c85...".
    Montamos o texto "id:<data.id>;request-id:<x-request-id>;ts:<ts>;"
    e calculamos o HMAC-SHA256 com a assinatura secreta. Se bater com v1, é legítimo.
    """
    if not MP_SEGREDO_WEBHOOK or not cabecalho_assinatura:
        return False

    partes = {}
    for pedaco in cabecalho_assinatura.split(","):
        if "=" in pedaco:
            chave, valor = pedaco.split("=", 1)
            partes[chave.strip()] = valor.strip()

    ts, recebido = partes.get("ts"), partes.get("v1")
    if not ts or not recebido:
        return False

    modelo = ""
    if id_dado:
        modelo += f"id:{str(id_dado).lower()};"
    if id_requisicao:
        modelo += f"request-id:{id_requisicao};"
    modelo += f"ts:{ts};"

    calculado = hmac.new(MP_SEGREDO_WEBHOOK.encode(), modelo.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(calculado, recebido)


def buscar_pagamento(pagamento_id):
    """
    Consulta um pagamento no Mercado Pago.

    Retorna:
        dict: com "status" ("approved", "pending", "rejected"...),
              "external_reference" (código do pedido) e "transaction_amount"
    """
    return requisitar("GET", f"{URL_MP}/v1/payments/{pagamento_id}", _cabecalhos())
