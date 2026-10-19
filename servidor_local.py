"""Inicia o painel nesta máquina, usando apenas a biblioteca padrão do Python."""

import argparse
import errno
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import webbrowser


PASTA_PAINEL = Path(__file__).resolve().parent


class ArquivosPainel(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Permite identificar a origem das imagens requisitadas ao OpenStreetMap.
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        super().end_headers()


class ServidorPainel(ThreadingHTTPServer):
    # Evita duas instâncias na mesma porta, inclusive no Windows.
    allow_reuse_address = False


def criar_servidor(porta):
    handler = partial(ArquivosPainel, directory=str(PASTA_PAINEL))
    try:
        return ServidorPainel(("127.0.0.1", porta), handler)
    except OSError as erro:
        if erro.errno not in (errno.EADDRINUSE, 10048):
            raise
        # Outra instância ou programa pode estar usando a porta escolhida.
        return ServidorPainel(("127.0.0.1", 0), handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000, help="Porta preferida (padrão: 8000).")
    parser.add_argument("--no-browser", action="store_true", help="Não abrir o navegador automaticamente.")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("A porta deve estar entre 0 e 65535.")

    try:
        servidor = criar_servidor(args.port)
    except OSError as erro:
        print("Não foi possível iniciar o painel: {}".format(erro), flush=True)
        return 1

    with servidor:
        url = "http://127.0.0.1:{}/index.html".format(servidor.server_port)
        print("Painel disponível em: {}".format(url), flush=True)
        print("Mantenha esta janela aberta durante o uso. Para encerrar, pressione Ctrl+C.", flush=True)
        if not args.no_browser:
            abertura = threading.Timer(0.5, webbrowser.open, args=(url,))
            abertura.daemon = True
            abertura.start()
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            print("\nPainel encerrado.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
