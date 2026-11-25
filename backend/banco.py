"""
Banco de dados dos pedidos e contatos (SQLite, que já vem com o Python).

O arquivo fica em backend/dados/zart.db (ou na pasta da variável PASTA_DADOS).
Em produção, essa pasta precisa ficar num disco que NÃO é apagado quando
o servidor reinicia. Veja o README.

Situações (status) de um pedido:
    aguardando_pagamento -> pago -> concluido
                                 -> registro_pendente  (algum domínio falhou)
    aguardando_pagamento -> cancelado                 (pagamento recusado)
"""

import json
import sqlite3
import threading
from datetime import datetime, timezone

from configuracao import PASTA_DADOS

_trava = threading.Lock()


def agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _conectar():
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(PASTA_DADOS / "zart.db")
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_tabelas():
    """Cria as tabelas na primeira vez que o servidor roda."""
    with _trava, _conectar() as conexao:
        conexao.executescript(
            """
            CREATE TABLE IF NOT EXISTS pedidos (
                codigo          TEXT PRIMARY KEY,
                criado_em       TEXT NOT NULL,
                atualizado_em   TEXT NOT NULL,
                status          TEXT NOT NULL,
                titular         TEXT NOT NULL,
                itens           TEXT NOT NULL,
                total           REAL NOT NULL,
                preferencia_id  TEXT,
                pagamento_id    TEXT
            );

            CREATE TABLE IF NOT EXISTS contatos (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                recebido_em  TEXT NOT NULL,
                nome         TEXT NOT NULL,
                email        TEXT NOT NULL,
                assunto      TEXT,
                mensagem     TEXT NOT NULL
            );
            """
        )


def _linha_para_pedido(linha):
    if linha is None:
        return None
    pedido = dict(linha)
    pedido["titular"] = json.loads(pedido["titular"])
    pedido["itens"] = json.loads(pedido["itens"])
    return pedido


def salvar_pedido(pedido):
    """Grava um pedido novo."""
    with _trava, _conectar() as conexao:
        conexao.execute(
            """INSERT INTO pedidos (codigo, criado_em, atualizado_em, status, titular, itens, total)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                pedido["codigo"],
                pedido["criadoEm"],
                pedido["criadoEm"],
                pedido["status"],
                json.dumps(pedido["titular"], ensure_ascii=False),
                json.dumps(pedido["itens"], ensure_ascii=False),
                pedido["total"],
            ),
        )


def buscar_pedido(codigo):
    """Retorna o pedido (dict) ou None."""
    with _conectar() as conexao:
        linha = conexao.execute("SELECT * FROM pedidos WHERE codigo = ?", (codigo,)).fetchone()
    return _linha_para_pedido(linha)


def atualizar_pedido(codigo, **campos):
    """
    Muda campos de um pedido. Ex.: atualizar_pedido("P-1A2B", status="pago")
    Listas e dicionários (itens) são convertidos para texto automaticamente.
    """
    permitidos = {"status", "itens", "preferencia_id", "pagamento_id"}
    campos = {chave: valor for chave, valor in campos.items() if chave in permitidos}
    if not campos:
        return

    if "itens" in campos:
        campos["itens"] = json.dumps(campos["itens"], ensure_ascii=False)
    campos["atualizado_em"] = agora()

    colunas = ", ".join(f"{chave} = ?" for chave in campos)
    with _trava, _conectar() as conexao:
        conexao.execute(f"UPDATE pedidos SET {colunas} WHERE codigo = ?", (*campos.values(), codigo))


def marcar_como_pago(codigo, pagamento_id):
    """
    Muda o pedido de "aguardando_pagamento" para "pago" de forma segura:
    se o Mercado Pago mandar o mesmo aviso duas vezes, só a primeira vale.

    Retorna:
        bool: True se ESTA chamada marcou como pago (e deve registrar os domínios)
    """
    with _trava, _conectar() as conexao:
        cursor = conexao.execute(
            """UPDATE pedidos SET status = 'pago', pagamento_id = ?, atualizado_em = ?
               WHERE codigo = ? AND status = 'aguardando_pagamento'""",
            (str(pagamento_id), agora(), codigo),
        )
        return cursor.rowcount == 1


def salvar_contato(contato):
    with _trava, _conectar() as conexao:
        conexao.execute(
            "INSERT INTO contatos (recebido_em, nome, email, assunto, mensagem) VALUES (?, ?, ?, ?, ?)",
            (agora(), contato["nome"], contato["email"], contato["assunto"], contato["mensagem"]),
        )
