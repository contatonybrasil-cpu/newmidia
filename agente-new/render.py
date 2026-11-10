#!/usr/bin/env python3
"""Gera telas de carrossel (1080x1350) da New York Store seguindo o manual de marca v1.

Uso: python3 render.py carrossel.json pasta_saida/
"""
import json, re, sys, base64, html, asyncio
from pathlib import Path

KIT = Path(__file__).resolve().parent
COR = {"preto": "#231F20", "off": "#DFDDDC", "cimento": "#C6BAAF",
       "areia": "#AB9B8A", "grafite": "#7B7168", "dourado": "#C6B097"}
CLARO = {"off", "cimento"}
W, H = 1080, 1350


def b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode()


def fontes():
    css = []
    for fam, arq, peso in [("Archivo Black", "ArchivoBlack", 400), ("Archivo Black", "ArchivoBlack-ext", 400),
                           ("Inter", "Inter-400", 400), ("Inter", "Inter-ext-400", 400),
                           ("Inter", "Inter-500", 500), ("Inter", "Inter-ext-500", 500),
                           ("Inter", "Inter-600", 600), ("Inter", "Inter-ext-600", 600)]:
        css.append(f"@font-face{{font-family:'{fam}';font-weight:{peso};"
                   f"src:url(data:font/woff2;base64,{b64(KIT/'fonts'/(arq+'.woff2'))}) format('woff2');}}")
    return "\n".join(css)


def logo(fundo, largura, vertical=False):
    """Logo oficial; os vazados internos recebem a cor do fundo (sem recolorir a marca)."""
    claro = fundo in CLARO
    nome = ("vertical" if vertical else "horizontal") + ("-escuro" if claro else "-branco")
    svg = (KIT / "logos" / f"{nome}.svg").read_text()
    if claro:  # logo preto: vazados brancos viram a cor do fundo
        svg = re.sub(r'fill="rgb\((?:99\.99|100%)[^"]*"', f'fill="{COR[fundo]}"', svg)
    else:      # logo branco: vazados escuros viram a cor do fundo
        svg = re.sub(r'fill="rgb\(13\.72[^"]*"', f'fill="{COR[fundo]}"', svg)
    svg = re.sub(r'class="lg"', f'style="width:{largura}px;height:auto;display:block"', svg, count=1)
    return svg


def e(t):
    return html.escape(t or "").replace("\n", "<br>")


def tela(t, i, total):
    tipo = t.get("tipo", "texto")
    fundo = t.get("fundo") or {"capa": "preto", "cta": "preto", "foto": "preto"}.get(tipo, "off")
    claro = fundo in CLARO
    tx = COR["preto"] if claro else COR["off"]
    apoio = COR["grafite"] if claro else COR["areia"]
    pag = f'<div class="pag" style="color:{apoio}">{i}/{total}</div>'

    if tipo == "capa":
        corpo = f"""
        <div class="topo">{logo(fundo, 260)}{pag}</div>
        <div class="base">
          <div class="kicker" style="color:{COR['areia']}">{e(t.get('kicker'))}</div>
          <h1 style="color:{tx}">{e(t.get('titulo'))}</h1>
          <p class="sub" style="color:{COR['cimento'] if not claro else COR['grafite']}">{e(t.get('sub'))}</p>
        </div>"""
    elif tipo == "foto":
        img = t.get("imagem")
        if img and Path(img).exists():
            mime = "image/png" if img.lower().endswith(".png") else "image/jpeg"
            foto = f'<div class="foto" style="background-image:url(data:{mime};base64,{b64(img)})"></div>'
        else:
            foto = (f'<div class="foto vazio" style="background:{COR["cimento"]};color:{COR["grafite"]}">'
                    f'[FOTO: {e(t.get("descricao_foto") or "produto na loja")}]</div>')
        corpo = f"""
        {foto}
        <div class="faixa" style="background:{COR[fundo]}">
          <div>
            <h2 style="color:{tx};font-size:56px">{e(t.get('titulo'))}</h2>
            <p class="leg" style="color:{apoio}">{e(t.get('texto'))}</p>
          </div>
          {pag}
        </div>"""
    elif tipo == "cta":
        corpo = f"""
        <div class="topo"><span></span>{pag}</div>
        <div class="meio">
          <h1 style="color:{tx};font-size:96px">{e(t.get('titulo'))}</h1>
          <p class="txt" style="color:{COR['cimento'] if not claro else COR['preto']}">{e(t.get('texto'))}</p>
          <div class="linha" style="background:{COR['areia']}"></div>
          <p class="leg" style="color:{apoio}">{e(t.get('contato') or 'WhatsApp (18) 99614-2832 · Loja Parque do Povo · usenewyork.com.br')}</p>
        </div>
        <div class="rodape">{logo(fundo, 300)}</div>"""
    else:  # texto
        num = t.get("numero") or f"{t.get('_n', i-1):02d}"
        corpo = f"""
        <div class="topo"><div class="num" style="color:{COR['areia']}">{e(num)}</div>{pag}</div>
        <div class="meio">
          <h2 style="color:{tx}">{e(t.get('titulo'))}</h2>
          <div class="linha" style="background:{COR['areia']}"></div>
          <p class="txt" style="color:{tx}">{e(t.get('texto'))}</p>
        </div>
        <div class="rodape">{logo(fundo, 170)}</div>"""
    return f'<section class="t t-{tipo}" style="background:{COR[fundo]}">{corpo}</section>'


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:%dpx}
.t{width:%dpx;height:%dpx;position:relative;overflow:hidden;font-family:Inter;display:flex;flex-direction:column;padding:96px}
h1{font-family:'Archivo Black';font-weight:400;font-size:112px;line-height:1.02;letter-spacing:-1px}
h2{font-family:'Archivo Black';font-weight:400;font-size:76px;line-height:1.08}
.topo{display:flex;justify-content:space-between;align-items:flex-start}
.pag{font-size:26px;font-weight:500;letter-spacing:2px}
.base{margin-top:auto}
.kicker{font-size:28px;font-weight:600;letter-spacing:6px;text-transform:uppercase;margin-bottom:32px}
.sub{font-size:38px;line-height:1.45;margin-top:36px;max-width:820px}
.meio{margin:auto 0}
.num{font-family:'Archivo Black';font-size:120px;line-height:1}
.linha{width:96px;height:4px;margin:44px 0}
.txt{font-size:40px;line-height:1.55;max-width:860px}
.leg{font-size:28px;line-height:1.5;margin-top:16px}
.rodape{margin-top:auto}
.t-foto{padding:0}
.foto,.foto.vazio{height:%dpx;background-size:cover;background-position:center}
.foto.vazio{display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:500;letter-spacing:2px;text-align:center;padding:80px}
.faixa{flex:1;display:flex;justify-content:space-between;align-items:center;padding:0 96px;gap:40px}
""" % (W, W, H, int(H * .72))


async def main(spec_path, out_dir):
    from playwright.async_api import async_playwright
    spec = json.loads(Path(spec_path).read_text())
    telas = spec["telas"]
    n = 0
    for t in telas:
        if t.get("tipo", "texto") == "texto":
            n += 1; t["_n"] = n
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    doc = f"<html><head><meta charset='utf-8'><style>{fontes()}{CSS}</style></head><body>" + \
          "".join(tela(t, i + 1, len(telas)) for i, t in enumerate(telas)) + "</body></html>"
    (out / "_preview.html").write_text(doc)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": W, "height": H})
        await pg.set_content(doc)
        await pg.evaluate("document.fonts.ready")
        nome = spec.get("nome", "carrossel")
        for i, el in enumerate(await pg.query_selector_all("section.t")):
            f = out / f"{nome}-{i+1:02d}.png"
            await el.screenshot(path=str(f))
            print(f)
        await b.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
