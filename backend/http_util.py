"""
Função para chamar APIs externas (Dynadot e Mercado Pago) usando só a
biblioteca padrão do Python.
"""

import json
import urllib.error
import urllib.request

TEMPO_LIMITE = 30  # segundos


class ErroApi(Exception):
    """Falha ao falar com uma API externa."""


def requisitar(metodo, url, cabecalhos=None, corpo=None):
    """
    Faz uma requisição HTTP e devolve a resposta já convertida de JSON.

    Parâmetros:
        metodo (str): "GET" ou "POST"
        url (str): endereço completo
        cabecalhos (dict): cabeçalhos extras
        corpo (dict | None): enviado como JSON

    Retorna:
        dict: resposta da API

    Erros:
        ErroApi: se a API responder com erro ou não responder
    """
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    pedido = urllib.request.Request(url, data=dados, method=metodo)
    pedido.add_header("Accept", "application/json")
    pedido.add_header("User-Agent", "ZartDominios/1.0")
    if dados is not None:
        pedido.add_header("Content-Type", "application/json")
    for chave, valor in (cabecalhos or {}).items():
        pedido.add_header(chave, valor)

    try:
        with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE) as resposta:
            return json.loads(resposta.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", "replace")[:500]
        raise ErroApi(f"HTTP {erro.code}: {detalhe}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as erro:
        raise ErroApi(str(erro)) from None
