# Transcribe la voz de un vídeo o audio con faster-whisper, en local (internet solo para
# descargar el modelo la primera vez), y guarda el texto con el tiempo de cada palabra en JSON.
# Uso: py -3 transcribir.py VIDEO [--salida archivo.json] [--modelo large-v3-turbo]
#                           [--idioma es|auto] [--palabras "Mewgenics, Medal"] [--hasta 30] [--pista 1]
import argparse, json, os, time

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
from comun import leer_audio

try:
    from faster_whisper import WhisperModel
except ImportError:
    raise SystemExit("Falta Whisper. Instálalo con: py -3 -m pip install faster-whisper")

p = argparse.ArgumentParser(description="Transcribe la voz de un vídeo con tiempos por palabra.")
p.add_argument("video")
p.add_argument("--salida", help="JSON de salida (por defecto, junto al vídeo: <nombre>.transcripcion.json)")
p.add_argument("--modelo", default="large-v3-turbo")
p.add_argument("--idioma", default="es", help="código de idioma, o 'auto' para detectarlo")
p.add_argument("--palabras", default="", help="palabras difíciles separadas por comas (nombres, juegos...)")
p.add_argument("--hasta", type=float, help="transcribir solo los primeros N segundos")
p.add_argument("--pista", type=int, help="número de pista de audio (0, 1...) si el vídeo trae varias")
a = p.parse_args()

t0 = time.time()
audio = leer_audio(a.video, a.hasta, a.pista)

try:  # si el modelo ya está descargado, no se conecta a internet
    modelo = WhisperModel(a.modelo, device="cpu", compute_type="int8", local_files_only=True)
except Exception:
    modelo = WhisperModel(a.modelo, device="cpu", compute_type="int8")

segmentos, info = modelo.transcribe(
    audio,
    language=None if a.idioma == "auto" else a.idioma,
    word_timestamps=True,                  # tiempo de cada palabra, para subtítulos y cortes
    vad_filter=True,                       # se salta silencios y ruido sin voz
    initial_prompt=a.palabras or None,     # pista con nombres raros para que acierte más
)

resultado = {"archivo": os.path.abspath(a.video), "idioma": info.language,
             "duracion": round(info.duration, 2), "segmentos": []}
for s in segmentos:
    resultado["segmentos"].append({
        "inicio": round(s.start, 2), "fin": round(s.end, 2), "texto": s.text.strip(),
        "palabras": [{"inicio": round(w.start, 2), "fin": round(w.end, 2), "palabra": w.word.strip(),
                      "prob": round(w.probability, 2)} for w in (s.words or [])],
    })
    print(f"[{s.start:6.2f} -> {s.end:6.2f}] {s.text.strip()}")

salida = a.salida or os.path.splitext(a.video)[0] + ".transcripcion.json"
with open(salida, "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=1)
print(f"\n{len(resultado['segmentos'])} frases | idioma {info.language} | {time.time() - t0:.1f} s | guardado en {salida}")
