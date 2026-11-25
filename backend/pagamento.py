"""
Ligação com o serviço de pagamento (por exemplo, Mercado Pago ou Stripe).

Fluxo:
    1. criar_cobranca() gera um link de pagamento para o pedido.
    2. O visitante paga no site do serviço de pagamento.
    3. O serviço avisa o nosso servidor (webhook) que o pagamento foi aprovado.
    4. Só então chamamos provedor.registrar_dominio().

A chave fica na variável de ambiente PAGAMENTO_CHAVE_API (arquivo .env).
"""

import os


def pagamento_configurado():
    return bool(os.environ.get("PAGAMENTO_CHAVE_API"))


def criar_cobranca(pedido):
    """
    Cria a cobrança no serviço de pagamento.

    Parâmetros:
        pedido (dict): pedido já validado, com "codigo", "itens" e "total"

    Retorna:
        str | None: link para o visitante pagar, ou None se ainda não configurado
    """
    if not pagamento_configurado():
        return None

    # TODO: chamar a API real do serviço de pagamento aqui e devolver o link.
    # Exemplo (Mercado Pago): criar uma "preferência" com os itens e devolver "init_point".
    return None
