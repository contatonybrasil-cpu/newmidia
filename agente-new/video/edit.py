#!/usr/bin/env python3
"""Edição automática de Reels no padrão New York Store.
Corta silêncios, legenda palavra por palavra, título-gancho no início e cartela final.
Uso: python3 edit.py video.mov words.json config.json saida.mp4
"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
# cores ASS (&HBBGGRR)
OFF, PRETO, AREIA, CIMENTO = "&H00DCDDDF", "&H00201F23", "&H008A9BAB", "&H00AFBAC6"


def segmentos(words, dur, pad=0.12, max_gap=0.35, show_gap=2.0, show_keep=1.4):
    """Trechos a manter: fala com folga; silêncios longos viram 'respiro' curto."""
    segs = []
    s, e = max(0, words[0]["s"] - pad), words[0]["e"] + pad
    for w in words[1:]:
        gap = w["s"] - e
        if gap <= max_gap:
            e = w["e"] + pad
            continue
        segs.append((s, e))
        if gap >= show_gap:  # pausa longa = provavelmente mostrando o produto: mantém um pedaço do meio
            mid = (e + w["s"]) / 2
            segs.append((mid - show_keep / 2, mid + show_keep / 2))
        s, e = max(0, w["s"] - pad), w["e"] + pad
    segs.append((s, min(e, dur)))
    return segs


def remap(t, segs, snap=False):
    acc = 0
    for a, b in segs:
        if a <= t <= b:
            return acc + (t - a)
        if snap and t < a:
            return acc
        acc += b - a
    return acc if snap else None


def ts(t):
    h, r = divmod(max(t, 0), 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ass(words, segs, cfg, total):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Leg,Inter SemiBold,80,{OFF},{OFF},{PRETO},&H40201F23,0,0,0,0,100,100,0,0,3,18,0,2,90,90,560,1
Style: Kicker,Inter SemiBold,44,{AREIA},{AREIA},{PRETO},&H00000000,0,0,0,0,100,100,6,0,1,0,0,8,90,90,170,1
Style: Gancho,Archivo Black,118,{OFF},{OFF},{PRETO},&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,90,90,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    g = cfg.get("gancho")
    if g:
        d = g.get("duracao", 3.0)
        ev.append(f"Dialogue: 1,{ts(0)},{ts(d)},Kicker,,0,0,0,,{{\\fad(150,200)}}{g.get('kicker','').upper()}")
        ev.append(f"Dialogue: 1,{ts(0)},{ts(d)},Gancho,,0,0,0,,{{\\fad(150,200)}}{g['titulo']}")
    fix = cfg.get("correcoes", {})
    ws = []
    for w in words:
        a, b = remap(w["s"], segs), remap(w["e"], segs)
        if a is None or b is None:
            continue
        txt = w["w"]
        core = txt.strip(".,!?;:")
        txt = txt.replace(core, fix.get(core, core))
        ws.append({"t": txt.rstrip(","), "s": a, "e": b, "fim": txt.endswith((".", "?", "!"))})
    # grupos de até 3 palavras, quebrando em fim de frase
    grupos, cur = [], []
    for w in ws:
        cur.append(w)
        if len(cur) == 3 or w["fim"]:
            grupos.append(cur); cur = []
    if cur:
        grupos.append(cur)
    for gi, gr in enumerate(grupos):
        fim_grupo = grupos[gi + 1][0]["s"] if gi + 1 < len(grupos) else gr[-1]["e"] + 0.3
        for i, w in enumerate(gr):
            st = w["s"]
            en = gr[i + 1]["s"] if i + 1 < len(gr) else min(fim_grupo, w["e"] + 0.6)
            parts = []
            for j, x in enumerate(gr):
                t = x["t"].rstrip(".?!")
                parts.append(f"{{\\c{AREIA}}}{t}{{\\c{OFF}}}" if j == i else t)
            ev.append(f"Dialogue: 0,{ts(st)},{ts(en)},Leg,,0,0,0,,{' '.join(parts)}")
    return head + "\n".join(ev) + "\n"


def run(cmd):
    subprocess.run(cmd, check=True)


def main(video, words_p, cfg_p, out):
    words = json.loads(Path(words_p).read_text())
    cfg = json.loads(Path(cfg_p).read_text())
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", video]).decode())
    segs = segmentos(words, dur)
    total = sum(b - a for a, b in segs)
    work = Path(out).parent / "_work"; work.mkdir(parents=True, exist_ok=True)
    (work / "leg.ass").write_text(ass(words, segs, cfg, total))
    # 0) proxy 1080x1920 (evita estourar memória com 4K)
    prox = work / "proxy.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf",
         f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "aac", "-b:a", "192k", str(prox)])
    video = str(prox)
    # 1) cortes + reenquadramento 9:16 + legendas
    parts = "".join(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS[a{i}];"
                    for i, (a, b) in enumerate(segs))
    conc = "".join(f"[v{i}][a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[cv][ca];"
    # inserts de imagem (looks/b-roll) em cima do vídeo, com a legenda por cima
    ins, extra, chain = cfg.get("inserts", []), [], "[cv]"
    for k, it in enumerate(ins):
        a = remap(it["de"], segs, True)
        b = remap(it["ate"], segs, True) if it.get("ate") is not None else a + it.get("dur", 1.5)
        extra += ["-loop", "1", "-t", f"{total:.2f}", "-i", it["img"]]
        iw, ih, ix, iy = it.get("w", W), it.get("h", H), it.get("x", 0), it.get("y", 0)
        conc += (f"[{k+1}:v]scale={iw}:{ih},setsar=1,format=yuva420p,"
                 f"fade=t=in:st={a:.2f}:d=0.15:alpha=1,fade=t=out:st={b-0.15:.2f}:d=0.15:alpha=1[im{k}];"
                 f"{chain}[im{k}]overlay={ix}:{iy}:enable='between(t,{a:.2f},{b:.2f})'[ov{k}];")
        chain = f"[ov{k}]"
    vf = (f"{chain}ass={work/'leg.ass'}:fontsdir={HERE/'fonts'}[vo];[ca]loudnorm=I=-14:TP=-1.5:LRA=11[ao]")
    run(["ffmpeg", "-v", "error", "-y", "-i", video, *extra, "-filter_complex", parts + conc + vf,
         "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", str(work / "corpo.mp4")])
    # 2) cartela final
    card = cfg.get("cartela")
    if card and Path(card).exists():
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", "2.2", "-i", card,
             "-f", "lavfi", "-t", "2.2", "-i", "anullsrc=r=48000:cl=stereo",
             "-vf", f"scale={W}:{H},fps={FPS},fade=t=in:st=0:d=0.5", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", str(work / "card.mp4")])
        (work / "lista.txt").write_text(f"file '{work/'corpo.mp4'}'\nfile '{work/'card.mp4'}'\n")
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "lista.txt"),
             "-c", "copy", "-movflags", "+faststart", out])
    else:
        run(["ffmpeg", "-v", "error", "-y", "-i", str(work / "corpo.mp4"), "-c", "copy", "-movflags", "+faststart", out])
    print(f"original {dur:.1f}s -> editado {total:.1f}s (+cartela) | {len(segs)} trechos")


if __name__ == "__main__":
    main(*sys.argv[1:5])
