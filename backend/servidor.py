"""
Servidor do back-end (parte de REVENDA).

Feito só com a biblioteca padrão do Python: não precisa instalar nada.

Rotas:
    GET  /api/disponibilidade?dominio=meusite.com  -> {"dominio", "status"}
    POST /api/pedidos                               -> cria um pedido
    POST /api/contato                               -> recebe mensagem de contato

Para rodar:
    cd backend
    python servidor.py
"""

import json
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import disponibilidade
from configuracao import ORIGEM_PERMITIDA, PORTA, extensoes_por_tld
from pedidos import ErroPedido, criar_pedido, registrar_contato
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

    def _ler_json(self):
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho <= 0 or tamanho > TAMANHO_MAXIMO:
            raise ErroPedido("Requisição inválida.")
        try:
            return json.loads(self.rfile.read(tamanho).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ErroPedido("Requisição inválida.")

    # ---------- rotas ----------

    def do_OPTIONS(self):
        """Pergunta prévia que o navegador faz antes de um POST (CORS)."""
        self.send_response(204)
        self._cabecalhos_cors()
        self.end_headers()

    def do_GET(self):
        endereco = urlparse(self.path)

        if endereco.path != "/api/disponibilidade":
            self._responder(404, {"erro": "Rota não encontrada."})
            return

        dominio = parse_qs(endereco.query).get("dominio", [""])[0]
        extensoes = extensoes_por_tld()
        separado = separar_dominio(dominio, extensoes.keys())

        if not separado:
            self._responder(400, {"erro": "Domínio inválido."})
            return

        nome, tld = separado
        dominio = f"{nome}.{tld}"
        status = disponibilidade.verificar(dominio, extensoes[tld])
        self._responder(200, {"dominio": dominio, "status": status})

    def do_POST(self):
        rotas = {
            "/api/pedidos": lambda dados: (201, criar_pedido(dados)),
            "/api/contato": lambda dados: (201, registrar_contato(dados) or {"ok": True}),
        }

        acao = rotas.get(urlparse(self.path).path)
        if not acao:
            self._responder(404, {"erro": "Rota não encontrada."})
            return

        try:
            codigo, resposta = acao(self._ler_json())
            self._responder(codigo, resposta)
        except ErroPedido as erro:
            self._responder(400, {"erro": str(erro)})
        except Exception:  # erro inesperado: não mostra detalhes internos ao visitante
            self.log_error("Erro inesperado em %s", self.path)
            traceback.print_exc()
            self._responder(500, {"erro": "Erro interno. Tente novamente mais tarde."})


def main():
    servidor = ThreadingHTTPServer(("0.0.0.0", PORTA), Manipulador)
    print(f"Back-end rodando em http://localhost:{PORTA}")
    print(f"Aceitando requisições do site: {ORIGEM_PERMITIDA}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor parado.")


if __name__ == "__main__":
    main()
