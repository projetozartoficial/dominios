"""
Ligação com o provedor de revenda (Dynadot, GoDaddy, ResellerClub...).

Este arquivo é o único lugar que conversa com a API do provedor.
Quando você escolher o provedor, troque o corpo de registrar_dominio()
pela chamada real da API dele (cada um tem documentação própria).

A chave da API fica na variável de ambiente PROVEDOR_CHAVE_API (arquivo .env),
nunca aqui no código.
"""

import os


def provedor_configurado():
    """Diz se a chave da API do provedor foi informada no .env."""
    return bool(os.environ.get("PROVEDOR_CHAVE_API"))


def registrar_dominio(dominio, anos, titular):
    """
    Pede ao provedor o registro do domínio. Só deve ser chamada
    DEPOIS que o pagamento for confirmado.

    Parâmetros:
        dominio (str): ex.: "meusite.com"
        anos (int): de 1 a 5
        titular (dict): {"nome", "email", "documento"}

    Retorna:
        dict: {"status": "registrado" | "pendente", "detalhe": str}
    """
    if not provedor_configurado():
        return {
            "status": "pendente",
            "detalhe": "Provedor ainda não configurado: registro deve ser feito manualmente.",
        }

    # TODO: chamar a API real do provedor aqui.
    # Exemplo do formato (muda de provedor para provedor):
    #   resposta = chamar_api("register", domain=dominio, duration=anos, contact=titular)
    #   return {"status": "registrado", "detalhe": resposta["id"]}
    return {"status": "pendente", "detalhe": "Integração com a API do provedor ainda não implementada."}
