"""
Servidor do back-end da Zart Domínios (parte de REVENDA).

Feito só com a biblioteca padrão do Python: não precisa instalar nada.

Rotas:
    GET  /                                          -> teste rápido ("está no ar?")
    GET  /api/disponibilidade?dominio=meusite.com  -> {"dominio", "status"}
    GET  /api/pedidos/<codigo>                      -> situação de um pedido
    POST /api/pedidos                               -> cria pedido e link de pagamento
    POST /api/contato                               -> recebe mensagem de contato
    POST /api/pagamento/notificacao                 -> aviso do Mercado Pago (webhook)

Para rodar:
    cd backend
    python servidor.py
"""

import json
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import banco
import disponibilidade
import pagamento
from configuracao import ORIGEM_PERMITIDA, PORTA, extensoes_por_tld
from http_util import ErroApi
from pedidos import ErroPedido, consultar_pedido, criar_pedido, processar_notificacao, registrar_contato
from validacao import separar_dominio

TAMANHO_MAXIMO = 20_000  # bytes aceitos no corpo de uma requisição


class Manipulador(BaseHTTPRequestHandler):
    """Recebe cada requisição e chama a função certa."""

    # ---------- respostas ----------

    def _cabecalhos_cors(self):
        """Permite que só o endereço do seu site use esta API."""
        self.send_header("Access-Control-Allow-Origin", ORIGEM_PERMITIDA)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Vary", "Origin")

    def _responder(self, codigo, dados):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self._cabecalhos_cors()
        self.end_headers()
        self.wfile.write(corpo)

    def _ler_corpo(self):
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho > TAMANHO_MAXIMO:
            raise ErroPedido("Requisição grande demais.")
        return self.rfile.read(tamanho) if tamanho > 0 else b""

    def _ler_json(self):
        try:
            return json.loads(self._ler_corpo().decode("utf-8") or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ErroPedido("Requisição inválida.")

    def _executar(self, funcao):
        """Roda uma rota tratando os erros de um jeito só."""
        try:
            codigo, resposta = funcao()
            self._responder(codigo, resposta)
        except ErroPedido as erro:
            self._responder(400, {"erro": str(erro)})
        except Exception:  # erro inesperado: não mostra detalhes internos ao visitante
            self.log_error("Erro inesperado em %s", self.path)
            traceback.print_exc()
            self._responder(500, {"erro": "Erro interno. Tente novamente mais tarde."})

    # ---------- rotas GET ----------

    def do_OPTIONS(self):
        """Pergunta prévia que o navegador faz antes de um POST (CORS)."""
        self.send_response(204)
        self._cabecalhos_cors()
        self.end_headers()

    def do_GET(self):
        endereco = urlparse(self.path)
        caminho = endereco.path.rstrip("/")

        if caminho == "":
            self._responder(200, {"ok": True, "servico": "Zart Domínios"})
        elif caminho == "/api/disponibilidade":
            self._executar(lambda: (200, self._disponibilidade(endereco.query)))
        elif caminho.startswith("/api/pedidos/"):
            codigo = caminho.rsplit("/", 1)[-1]
            self._executar(lambda: (200, consultar_pedido(codigo)))
        else:
            self._responder(404, {"erro": "Rota não encontrada."})

    def _disponibilidade(self, consulta):
        dominio = parse_qs(consulta).get("dominio", [""])[0]
        extensoes = extensoes_por_tld()
        separado = separar_dominio(dominio, extensoes.keys())
        if not separado:
            raise ErroPedido("Domínio inválido.")
        nome, tld = separado
        dominio = f"{nome}.{tld}"
        return {"dominio": dominio, "status": disponibilidade.verificar(dominio, extensoes[tld])}

    # ---------- rotas POST ----------

    def do_POST(self):
        caminho = urlparse(self.path).path.rstrip("/")

        if caminho == "/api/pedidos":
            self._executar(lambda: (201, criar_pedido(self._ler_json())))
        elif caminho == "/api/contato":
            self._executar(lambda: (201, registrar_contato(self._ler_json()) or {"ok": True}))
        elif caminho == "/api/pagamento/notificacao":
            self._notificacao_mercado_pago()
        else:
            self._responder(404, {"erro": "Rota não encontrada."})

    def _notificacao_mercado_pago(self):
        """
        Recebe o aviso do Mercado Pago. Responde 200 rápido (o Mercado Pago
        espera pouco tempo) e processa o pagamento em segundo plano.
        """
        consulta = parse_qs(urlparse(self.path).query)
        try:
            corpo = json.loads(self._ler_corpo().decode("utf-8") or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError, ErroPedido):
            corpo = {}

        tipo = consulta.get("type", [corpo.get("type", "")])[0]
        id_dado = consulta.get("data.id", [str((corpo.get("data") or {}).get("id", ""))])[0]

        if not pagamento.assinatura_valida(
            self.headers.get("x-signature"), self.headers.get("x-request-id"), id_dado
        ):
            self._responder(401, {"erro": "Assinatura inválida."})
            return

        self._responder(200, {"ok": True})

        if tipo == "payment" and id_dado:
            threading.Thread(target=self._processar_em_segundo_plano, args=(id_dado,), daemon=True).start()

    @staticmethod
    def _processar_em_segundo_plano(pagamento_id):
        try:
            processar_notificacao(pagamento_id)
        except (ErroApi, Exception):
            print(f"[notificação {pagamento_id}] falhou:")
            traceback.print_exc()


def main():
    banco.criar_tabelas()
    servidor = ThreadingHTTPServer(("0.0.0.0", PORTA), Manipulador)
    print(f"Back-end da Zart Domínios rodando na porta {PORTA}")
    print(f"Aceitando requisições do site: {ORIGEM_PERMITIDA}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor parado.")


if __name__ == "__main__":
    main()
