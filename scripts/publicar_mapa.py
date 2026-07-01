"""Publica el mapa operacional (reports_out/mapa_operacional.html) como un ENLACE
público vía GitHub Pages (rama `gh-pages`, aislada del código).

Reejecutar actualiza el mapa en el mismo enlace. El mapa es AGREGADO (sin PII).

Requiere un token de GitHub con scope `repo` en la variable de entorno GH_TOKEN.

Uso:
    GH_TOKEN=ghp_xxx python scripts/publicar_mapa.py
    GH_TOKEN=ghp_xxx python scripts/publicar_mapa.py --repo jhonny-nolatech/ReportVenApp
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings  # noqa: E402

API = "https://api.github.com"


def _req(method: str, url: str, token: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or "{}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default="jhonny-nolatech/ReportVenApp")
    p.add_argument("--branch", default="gh-pages")
    p.add_argument("--html", default=None, help="Ruta del HTML (def.: reports_out/mapa_operacional.html)")
    args = p.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ Falta GH_TOKEN (token de GitHub con scope 'repo').")
        return 1
    owner_repo = args.repo
    html_path = args.html or os.path.join(Settings().reports_out_dir, "mapa_operacional.html")
    if not os.path.exists(html_path):
        print(f"❌ No existe {html_path}. Corre antes: python scripts/generar_mapa.py")
        return 1
    content = open(html_path, "rb").read()

    base = f"{API}/repos/{owner_repo}/git"
    # 1) blob
    _, blob = _req("POST", f"{base}/blobs", token,
                   {"content": base64.b64encode(content).decode(), "encoding": "base64"})
    # 2) tree (index.html en la raíz de gh-pages)
    _, tree = _req("POST", f"{base}/trees", token,
                   {"tree": [{"path": "index.html", "mode": "100644", "type": "blob", "sha": blob["sha"]}]})
    # 3) ¿existe la rama? -> parents
    st, ref = _req("GET", f"{base}/refs/heads/{args.branch}", token)
    parents = [ref["object"]["sha"]] if st == 200 else []
    # 4) commit
    _, commit = _req("POST", f"{base}/commits", token,
                     {"message": "Actualizar mapa operacional (Terremoto 24J)",
                      "tree": tree["sha"], "parents": parents})
    # 5) crear/actualizar ref
    if st == 200:
        _req("PATCH", f"{base}/refs/heads/{args.branch}", token, {"sha": commit["sha"], "force": True})
    else:
        _req("POST", f"{base}/refs", token, {"ref": f"refs/heads/{args.branch}", "sha": commit["sha"]})
    # 6) habilitar Pages (si ya está, devuelve error y se ignora)
    _req("POST", f"{API}/repos/{owner_repo}/pages", token,
         {"source": {"branch": args.branch, "path": "/"}})
    # 7) URL final
    _, pages = _req("GET", f"{API}/repos/{owner_repo}/pages", token)
    url = pages.get("html_url") or f"https://{owner_repo.split('/')[0]}.github.io/{owner_repo.split('/')[1]}/"
    print("✅ Mapa publicado.")
    print(f"   Enlace: {url}")
    print("   (GitHub Pages tarda ~1 min en propagar el primer despliegue.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
