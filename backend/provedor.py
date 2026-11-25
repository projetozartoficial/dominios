"""
Ligação com a Dynadot (provedor de revenda).

Usa a API "api3.json" da Dynadot:
    1. create_contact -> cria o contato do titular (o cliente vira dono do domínio)
    2. register       -> registra o domínio usando esse contato

Importante:
- A Dynadot cobra do SALDO da sua conta (em dólar). Mantenha saldo suficiente.
- Com DYNADOT_MODO_TESTE=sim, tudo vai para o sandbox (ambiente de testes),
  sem registrar de verdade.
- A chave fica na variável DYNADOT_CHAVE_API (arquivo .env).

Documentação: https://www.dynadot.com/domain/api3.html
A Dynadot marcou essa API como "legada" e tem uma API nova (RESTful).
Se um dia a antiga for desligada, só este arquivo precisa mudar.
"""

from urllib.parse import urlencode

from configuracao import DYNADOT_CHAVE, DYNADOT_TESTE
from http_util import ErroApi, requisitar

URL_PRODUCAO = "https://api.dynadot.com/api3.json"
URL_TESTE = "https://api-sandbox.dynadot.com/api3.json"


def provedor_configurado():
    """Diz se a chave da Dynadot foi informada."""
    return bool(DYNADOT_CHAVE)


def _chamar(comando, **parametros):
    """
    Chama um comando da Dynadot e devolve o "miolo" da resposta.

    Exemplo de resposta da Dynadot:
        {"RegisterResponse": {"ResponseCode": 0, "Status": "success", ...}}
    """
    url_base = URL_TESTE if DYNADOT_TESTE else URL_PRODUCAO
    consulta = urlencode({"key": DYNADOT_CHAVE, "command": comando, **parametros})
    resposta = requisitar("GET", f"{url_base}?{consulta}")

    # A resposta vem dentro de uma chave tipo "RegisterResponse"
    conteudo = next(iter(resposta.values()), {}) if resposta else {}
    codigo = str(conteudo.get("ResponseCode", conteudo.get("SuccessCode", "")))

    if codigo != "0" or str(conteudo.get("Status", "")).lower() != "success":
        raise ErroApi(conteudo.get("Error") or f"Dynadot respondeu: {conteudo}")

    return conteudo


def criar_contato(titular):
    """
    Cria na Dynadot o contato do titular (exigido pelos registros de domínio).

    Parâmetros:
        titular (dict): nome, email, telefone, endereco, cidade, estado, cep

    Retorna:
        str: ContactId criado
    """
    conteudo = _chamar(
        "create_contact",
        name=titular["nome"],
        email=titular["email"],
        phonecc="55",
        phonenum=titular["telefone"],
        address1=titular["endereco"],
        city=titular["cidade"],
        state=titular["estado"],
        zip=titular["cep"],
        country="BR",
    )
    return str(conteudo["CreateContactContent"]["ContactId"])


def registrar_dominio(dominio, anos, titular, contato_id=None):
    """
    Registra o domínio no nome do titular. Só deve ser chamada
    DEPOIS que o pagamento for confirmado.

    Parâmetros:
        dominio (str): ex.: "meusite.com"
        anos (int): de 1 a 5
        titular (dict): dados do titular
        contato_id (str | None): reaproveita um contato já criado no mesmo pedido

    Retorna:
        dict: {"status": "registrado" | "falhou", "detalhe": str, "contato_id": str | None}
    """
    if not provedor_configurado():
        return {
            "status": "falhou",
            "detalhe": "Dynadot não configurada: registrar manualmente.",
            "contato_id": contato_id,
        }

    try:
        contato_id = contato_id or criar_contato(titular)
        conteudo = _chamar(
            "register",
            domain=dominio,
            duration=anos,
            currency="USD",
            registrant_contact=contato_id,
            admin_contact=contato_id,
            technical_contact=contato_id,
            billing_contact=contato_id,
        )
        return {
            "status": "registrado",
            "detalhe": f"Expira em {conteudo.get('Expiration', '?')}",
            "contato_id": contato_id,
        }
    except ErroApi as erro:
        return {"status": "falhou", "detalhe": str(erro)[:300], "contato_id": contato_id}
