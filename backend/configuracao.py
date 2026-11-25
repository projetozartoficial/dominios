"""
Configurações do back-end.

Os preços e as extensões vêm do MESMO arquivo do site (dados/site.json),
então você só precisa mudar os preços em um lugar.

As senhas e chaves (Dynadot, Mercado Pago, e-mail) NUNCA ficam no código:
elas vêm de variáveis de ambiente. Veja o arquivo .env.exemplo.
"""

import json
import os
from pathlib import Path

PASTA_BACKEND = Path(__file__).resolve().parent
PASTA_PROJETO = PASTA_BACKEND.parent
ARQUIVO_SITE = PASTA_PROJETO / "dados" / "site.json"


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


def env(chave, padrao=""):
    """Lê uma variável de ambiente, já sem espaços."""
    return os.environ.get(chave, padrao).strip()


carregar_env()

PASTA_DADOS = Path(env("PASTA_DADOS") or PASTA_BACKEND / "dados")

# Servidor (o Render e outros serviços informam a porta pela variável PORT)
PORTA = int(env("PORT") or env("PORTA", "8080"))
ORIGEM_PERMITIDA = env("ORIGEM_PERMITIDA", "http://localhost:8000")
ANOS_MAXIMO = 5

# Endereços públicos (usados nos links de volta e no aviso do Mercado Pago)
URL_SITE = env("URL_SITE", "http://localhost:8000").rstrip("/")
URL_API = env("URL_API", "http://localhost:8080").rstrip("/")

# Dynadot
DYNADOT_CHAVE = env("DYNADOT_CHAVE_API")
DYNADOT_TESTE = env("DYNADOT_MODO_TESTE", "sim").lower() in ("sim", "true", "1")

# Mercado Pago
MP_TOKEN = env("MERCADOPAGO_ACCESS_TOKEN")
MP_SEGREDO_WEBHOOK = env("MERCADOPAGO_SEGREDO_WEBHOOK")

# E-mail (SMTP)
SMTP_SERVIDOR = env("SMTP_SERVIDOR")
SMTP_PORTA = int(env("SMTP_PORTA", "587"))
SMTP_USUARIO = env("SMTP_USUARIO")
SMTP_SENHA = env("SMTP_SENHA")
EMAIL_REMETENTE = env("EMAIL_REMETENTE") or SMTP_USUARIO
EMAIL_ADMIN = env("EMAIL_ADMIN")
