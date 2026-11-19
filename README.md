# MODO LEONIDA · canal de GTA 6 listo para subir

- `canal/` → avatar, banner, marca de agua, descripción y orden de subida (`CANAL.md`).
- `videos/NN-…/` → por vídeo: `video.mp4` (1080p30), `miniatura.jpg` (1280×720), `subtitulos.srt`, `metadata.md` (título, descripción con capítulos y fuentes, etiquetas, comentario fijado).
- `pipeline/` → código que genera todo: guiones (`guiones.py`), motor gráfico (`render.py`), música original (`musica.py`), metadatos (`metadatos.py`).

## Regenerar
```
pip install kokoro-onnx soundfile scipy pillow numpy
# modelo de voz en /opt/tts (kokoro-v1.0.onnx y voices-v1.0.bin, releases de thewh1teagle/kokoro-onnx)
cd pipeline
python3 build.py tts          # voz
python3 build.py render 0 1 2 # vídeos (índice 0-9)
python3 build.py thumbs && python3 build.py canal && python3 metadatos.py
```
Para cambiar un dato: edita la escena en `guiones.py` y vuelve a lanzar `tts` y `render N` de ese vídeo.
