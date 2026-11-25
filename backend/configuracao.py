"""
Configurações do back-end.

Os preços e as extensões vêm do MESMO arquivo do site (dados/site.json),
então você só precisa mudar os preços em um lugar.

As senhas e chaves (API do provedor, pagamento) NUNCA ficam no código:
elas vêm de variáveis de ambiente. Veja o arquivo .env.exemplo.
"""

import json
import os
from pathlib import Path

PASTA_BACKEND = Path(__file__).resolve().parent
PASTA_PROJETO = PASTA_BACKEND.parent
ARQUIVO_SITE = PASTA_PROJETO / "dados" / "site.json"
PASTA_DADOS = PASTA_BACKEND / "dados"


def carregar_env(caminho=PASTA_BACKEND / ".env"):
    """
    Lê o arquivo .env (se existir) e coloca cada linha CHAVE=valor
    nas variáveis de ambiente. Assim não precisamos instalar nenhuma biblioteca.
    """
    if not caminho.exists():
        return

    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip())


def carregar_site():
    """
    Lê o dados/site.json.

    Retorna:
        dict: configurações do site
    """
    with open(ARQUIVO_SITE, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def extensoes_por_tld():
    """
    Retorna as extensões em um dicionário, para achar rápido pelo nome.

    Exemplo:
        {"com": {"tld": "com", "modo": "revenda", "preco": 69.9, ...}, ...}
    """
    return {extensao["tld"]: extensao for extensao in carregar_site()["extensoes"]}


carregar_env()

PORTA = int(os.environ.get("PORTA", "8080"))
ORIGEM_PERMITIDA = os.environ.get("ORIGEM_PERMITIDA", "http://localhost:8000")
ANOS_MAXIMO = 5
