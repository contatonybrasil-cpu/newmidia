import sys, asyncio
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
import render as R
from playwright.async_api import async_playwright
out, larg = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 380
html = f"""<html><head><meta charset='utf-8'><style>*{{margin:0;padding:0}}
body{{width:1080px;height:1920px;background:{R.COR['preto']};display:flex;align-items:center;justify-content:center}}</style></head>
<body>{R.logo('preto', larg)}</body></html>"""
async def m():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width':1080,'height':1920}); await pg.set_content(html)
        await pg.screenshot(path=out); await b.close()
asyncio.run(m())
