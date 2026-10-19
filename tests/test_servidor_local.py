"""Verificações do servidor local; executar com python -m unittest discover -s tests."""

from http.client import HTTPConnection
import subprocess
import sys
import tempfile
import threading
import unittest

from servidor_local import PASTA_PAINEL, criar_servidor


class ServidorLocalTest(unittest.TestCase):
    def setUp(self):
        self.servidor = criar_servidor(0)
        self.thread = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.thread.start()
        self.conexao = HTTPConnection(*self.servidor.server_address, timeout=10)

    def tearDown(self):
        self.conexao.close()
        self.servidor.shutdown()
        self.servidor.server_close()
        self.thread.join(timeout=5)

    def test_paginas_e_arquivos_do_painel(self):
        arquivos = [p.name for p in PASTA_PAINEL.glob("*.html")]
        arquivos += ["js/mapas-base.js", "leaflet/leaflet.js", "data/rj_banco.js"]
        for arquivo in arquivos:
            with self.subTest(arquivo=arquivo):
                self.conexao.request("GET", "/" + arquivo)
                resposta = self.conexao.getresponse()
                self.assertEqual(resposta.status, 200)
                self.assertEqual(resposta.getheader("Referrer-Policy"), "strict-origin-when-cross-origin")
                self.assertEqual(resposta.read(), (PASTA_PAINEL / arquivo).read_bytes())

    def test_acesso_somente_local_e_porta_ocupada(self):
        self.assertEqual(self.servidor.server_address[0], "127.0.0.1")
        with criar_servidor(self.servidor.server_port) as outro:
            self.assertNotEqual(outro.server_port, self.servidor.server_port)
            self.assertEqual(outro.server_address[0], "127.0.0.1")

    def test_arquivo_inexistente(self):
        self.conexao.request("GET", "/arquivo-inexistente.html")
        resposta = self.conexao.getresponse()
        self.assertEqual(resposta.status, 404)
        resposta.read()

    def test_inicia_a_partir_de_outra_pasta(self):
        with tempfile.TemporaryDirectory(prefix="cavalarica com espacos ") as pasta:
            processo = subprocess.Popen(
                [sys.executable, "-X", "utf8", str(PASTA_PAINEL / "servidor_local.py"), "--port", "0", "--no-browser"],
                cwd=pasta, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
            )
            try:
                linha = processo.stdout.readline().strip()
                self.assertIn("http://127.0.0.1:", linha)
                porta = int(linha.split("127.0.0.1:", 1)[1].split("/", 1)[0])
                conexao = HTTPConnection("127.0.0.1", porta, timeout=10)
                try:
                    conexao.request("GET", "/index.html")
                    resposta = conexao.getresponse()
                    self.assertEqual(resposta.status, 200)
                    self.assertEqual(resposta.read(), (PASTA_PAINEL / "index.html").read_bytes())
                finally:
                    conexao.close()
            finally:
                processo.terminate()
                processo.communicate(timeout=10)

    def test_porta_invalida(self):
        resultado = subprocess.run(
            [sys.executable, "-X", "utf8", str(PASTA_PAINEL / "servidor_local.py"), "--port", "65536", "--no-browser"],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        self.assertEqual(resultado.returncode, 2)
        self.assertIn("65535", resultado.stderr)


if __name__ == "__main__":
    unittest.main()
