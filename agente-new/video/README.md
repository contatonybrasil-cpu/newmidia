# Edição automática de Reels — New York Store

Padrão aprovado em 10/11/2026 (vídeo New Balance 204L).

1. Transcrição com tempo por palavra (faster-whisper, modelo small int8 em português).
   Modelo sem HuggingFace: `npm pack @skillninja/shortmovie-telop-model-p0..p3`, juntar `model.bin.part0..3`
   em `model.bin` (sha256 em model.sha256) + config.json, tokenizer.json, vocabulary.json, preprocessor_config.json.
   Carregar o áudio como numpy (wav 16 kHz mono) — o `av` do ambiente quebra o decode do faster-whisper.
   Salvar `words.json` = [{"w","s","e"}].
2. `python3 cartela_logo.py cartela.png 380` — cartela final: só o logo horizontal branco, pequeno, fundo preto.
3. `config.json`:
   - `gancho`: {kicker, titulo, duracao} — título nos 3 primeiros segundos (Archivo Black, topo).
   - `correcoes`: {"palavra_errada": "certa"} para a legenda.
   - `inserts`: fotos/b-roll [{img, de, ate|dur, w, h, x, y}] em tempo do vídeo ORIGINAL.
     Padrão aprovado: card pequeno (380×545) posicionado onde a pessoa aponta no vídeo, com fade.
   - `cartela`: caminho do png.
4. `python3 edit.py video.mov words.json config.json saida.mp4`
   Corta silêncios (pausas longas viram 1,4 s, ex.: mostrando o produto), 1080×1920 30fps,
   legenda Inter SemiBold 80 em caixa preta translúcida, palavra atual em areia, grupos de até 3 palavras,
   áudio normalizado -14 LUFS, cartela de 2,2 s com fade.
