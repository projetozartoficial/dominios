"""
Verifica se um domínio está livre usando o RDAP, o serviço público
de consulta dos registros de domínios.

    Resposta 404 -> ninguém registrou -> "disponivel"
    Resposta 200 -> já tem dono        -> "registrado"
    Qualquer erro                      -> "verificar"
"""

import urllib.error
import urllib.request

TEMPO_LIMITE = 6  # segundos


def verificar(dominio, extensao):
    """
    Consulta o RDAP da extensão.

    Parâmetros:
        dominio (str): ex.: "meusite.com"
        extensao (dict): a extensão do site.json (precisa do campo "rdap")

    Retorna:
        str: "disponivel", "registrado" ou "verificar"
    """
    endereco_rdap = extensao.get("rdap")
    if not endereco_rdap:
        return "verificar"

    pedido = urllib.request.Request(
        endereco_rdap + dominio,
        headers={"Accept": "application/rdap+json", "User-Agent": "site-dominios/1.0"},
    )

    try:
        with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE):
            return "registrado"
    except urllib.error.HTTPError as erro:
        return "disponivel" if erro.code == 404 else "verificar"
    except (urllib.error.URLError, TimeoutError):
        return "verificar"
