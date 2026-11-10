# Agente New — New York Store

Kit usado pelo agente diário para gerar as artes de carrossel (1080×1350) seguindo o manual de marca v1.

```
python3 render.py carrossel.json saida/
```

Tipos de tela no JSON: `capa`, `texto`, `foto`, `cta`. Fundos: `preto`, `off`, `cimento`. Veja `exemplo.json`.
Requer Playwright + Chrome/Chromium.
