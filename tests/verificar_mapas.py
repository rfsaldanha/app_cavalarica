import argparse
import base64
from pathlib import Path
import subprocess
import sys

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
# Imagem transparente usada somente como resposta simulada nos testes.
TILE = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWQAAAABJRU5ErkJggg==")
parser = argparse.ArgumentParser(description="Verifica os mapas com respostas simuladas, sem baixar tiles externos.")
parser.add_argument("--browser-executable", help="Caminho opcional para Chrome/Chromium já instalado.")
args = parser.parse_args()
server = subprocess.Popen([sys.executable, "-X", "utf8", str(ROOT / "servidor_local.py"), "--port", "0", "--no-browser"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
try:
    url = server.stdout.readline().strip().split("http://", 1)[1]
    base = "http://" + url.rsplit("/", 1)[0]
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.browser_executable, headless=True)
        context = browser.new_context(viewport={"width": 1366, "height": 900})
        requests = []
        mode = {"fail": False}
        def route_request(route):
            req = route.request
            if req.url.startswith(base) or req.url.startswith("file:"):
                route.continue_()
            elif "tile.openstreetmap.org/" in req.url or "server.arcgisonline.com/" in req.url:
                requests.append({"url": req.url, "referer": req.headers.get("referer")})
                if mode["fail"]:
                    route.fulfill(status=403, content_type="image/png", headers={"Access-Control-Allow-Origin": "*"}, body=TILE)
                else:
                    route.fulfill(status=200, content_type="image/png", headers={"Access-Control-Allow-Origin": "*"}, body=TILE)
            else:
                route.abort()
        context.route("**/*", route_request)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        pages = sorted(f.name for f in ROOT.glob("*.html") if "L.map(" in f.read_text(encoding="utf-8"))
        for name in pages:
            page.goto(base + "/" + name, wait_until="networkidle")
            assert page.evaluate("map.hasLayer(baseLayers.Ruas)"), (name, "ruas inativa")
            assert "OpenStreetMap" in page.locator(".leaflet-control-attribution").inner_text()
            assert page.locator(".mapa-aviso").count() == 0, (name, page.locator(".mapa-aviso").inner_text())
            assert page.evaluate("Object.keys(baseLayers).length") == 3
            assert page.locator("svg path").count() > 0, (name, "dados ausentes")
            assert not errors, (name, errors)
            print("OK", name, flush=True)
        assert requests and all(r["referer"] == base + "/" for r in requests), requests[:2]
        print("OK Referer de todas as requisicoes simuladas", flush=True)

        page.goto(base + "/dengue.html", wait_until="networkidle")
        original_paths = page.locator("svg path").count()
        page.locator(".leaflet-control-layers").hover()
        page.get_by_label("Sem mapa de fundo", exact=True).check()
        assert not page.evaluate("map.hasLayer(baseLayers.Ruas)")
        assert page.locator("svg path").count() == original_paths
        page.get_by_label("Imagem de satélite", exact=True).check()
        page.wait_for_load_state("networkidle")
        assert page.evaluate("map.hasLayer(baseLayers['Imagem de satélite'])")
        assert "Esri" in page.locator(".leaflet-control-attribution").inner_text()
        print("OK troca de fundos preserva os dados", flush=True)

        mode["fail"] = True
        page.goto(base + "/dengue.html", wait_until="networkidle")
        assert page.evaluate("map.hasLayer(baseLayers['Sem mapa de fundo'])")
        assert page.locator(".mapa-aviso").is_visible()
        assert page.locator("svg path").count() == original_paths
        mode["fail"] = False
        page.locator(".leaflet-control-layers").hover()
        page.get_by_label("Ruas", exact=True).check()
        page.wait_for_load_state("networkidle")
        assert page.evaluate("map.hasLayer(baseLayers.Ruas)")
        assert page.locator(".mapa-aviso").count() == 0
        print("OK erro HTTP 403 e recuperacao", flush=True)

        before = len(requests)
        page.goto((ROOT / "dengue.html").as_uri(), wait_until="networkidle")
        assert len(requests) == before, "Requisicao externa de tiles via file://"
        assert page.evaluate("Object.keys(baseLayers).length") == 1
        assert "INICIAR_WINDOWS.bat" in page.locator(".mapa-aviso").inner_text()
        assert page.locator("svg path").count() == original_paths
        print("OK file:// sem requisicoes de tiles", flush=True)
        assert not errors, errors
        context.close()

        browser.close()
finally:
    server.terminate()
    server.communicate(timeout=10)
