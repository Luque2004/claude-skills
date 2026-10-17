# Analiza vídeos para decidir el montaje. Todos los tiempos salen en segundos y en JSON.
# Uso:
#   py -3 analizar.py silencios  VIDEO [--umbral auto|-40] [--min 0.35] [--pista N]   tramos de voz y de silencio
#   py -3 analizar.py volumen    VIDEO [--ventana 0.5] [--top 8] [--pista N]          picos: disparos, gritos, el drop
#   py -3 analizar.py movimiento VIDEO [--ventana 0.5] [--top 8]                      tramos con más acción (entrenos)
#   py -3 analizar.py escenas    VIDEO [--umbral 0.3]                                 cortes de un vídeo ya editado
#   py -3 analizar.py fotogramas VIDEO --salida CARPETA [--cada 2]                    capturas para mirar el estilo
#   py -3 analizar.py beats      PROYECTO                                             beats de la música de un proyecto de CapCut
# Con --guardar ARCHIVO.json además se guarda el resultado.
import argparse, json, os, re, subprocess, sys
from pathlib import Path

import numpy as np
from comun import CARPETA_CAPCUT, S, cargar, ffbin, leer_audio, info_video

FR = 16000  # frecuencia a la que se analiza el audio


def nivel_db(audio, ventana):
    """Volumen (RMS en dB) de cada ventana de `ventana` segundos."""
    n = max(1, int(ventana * FR))
    k = len(audio) // n
    if k == 0:
        return np.array([])
    rms = np.sqrt(np.mean(audio[: k * n].astype(np.float64).reshape(k, n) ** 2, axis=1))
    return 20 * np.log10(np.maximum(rms, 1e-9))


def mejores(serie, ventana, top, separacion):
    """Las `top` ventanas más altas, separadas al menos `separacion` segundos entre sí."""
    elegidas = []
    for i in np.argsort(serie)[::-1]:
        t = i * ventana + ventana / 2
        if all(abs(t - e) >= separacion for e, _ in elegidas):
            elegidas.append((t, float(serie[i])))
        if len(elegidas) >= top:
            break
    return [{"t": round(t, 2), "valor": round(v, 2)} for t, v in sorted(elegidas)]


def silencios(a):
    paso = 0.02
    db = nivel_db(leer_audio(a.video, pista=a.pista), paso)
    if a.umbral == "auto":  # relativo a la voz: 22 dB por debajo de lo más alto
        umbral = float(np.clip(np.percentile(db, 95) - 22, -55, -25)) if len(db) else -40.0
    else:
        umbral = float(a.umbral)
    tramos, ini = [], None
    for i, v in enumerate(np.append(db, 0.0)):  # el 0 final cierra un silencio que llegue al final
        if v < umbral and ini is None:
            ini = i
        elif v >= umbral and ini is not None:
            if (i - ini) * paso >= a.min:
                tramos.append([round(ini * paso, 2), round(i * paso, 2)])
            ini = None
    duracion = round(len(db) * paso, 2)
    voz, t = [], 0.0
    for s0, s1 in tramos:
        if s0 > t:
            voz.append([round(t, 2), s0])
        t = s1
    if t < duracion:
        voz.append([round(t, 2), duracion])
    return {"duracion": duracion, "umbral_db": round(umbral, 1), "silencios": tramos, "voz": voz}


def volumen(a):
    db = nivel_db(leer_audio(a.video, pista=a.pista), a.ventana)
    picos = [p for p in mejores(db, a.ventana, a.top, max(1.5, 3 * a.ventana)) if p["valor"] > -60]  # fuera el silencio
    return {"duracion": round(len(db) * a.ventana, 2), "ventana": a.ventana, "media_db": round(float(np.mean(db)), 1),
            "picos": picos}


def movimiento(a):
    # YDIF = cuánto cambia la imagen de un fotograma al siguiente (a 10 fps y en pequeño, para ir rápido)
    cmd = [ffbin("ffmpeg"), "-v", "error", "-i", a.video, "-an", "-vf",
           "fps=10,scale=160:-2,signalstats,metadata=print:key=lavfi.signalstats.YDIF:file=-", "-f", "null", "-"]
    salida = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    tiempos = [float(x) for x in re.findall(r"pts_time:([\d.]+)", salida)]
    valores = [float(x) for x in re.findall(r"YDIF=([\d.]+)", salida)]
    if not valores:
        return {"error": "no se pudo medir el movimiento"}
    n = int(max(tiempos) // a.ventana) + 1
    suma, cuenta = np.zeros(n), np.zeros(n)
    for t, v in zip(tiempos, valores):
        suma[int(t // a.ventana)] += v
        cuenta[int(t // a.ventana)] += 1
    serie = suma / np.maximum(cuenta, 1)
    return {"duracion": round(max(tiempos), 2), "ventana": a.ventana, "media": round(float(np.mean(serie)), 2),
            "picos": mejores(serie, a.ventana, a.top, max(1.5, 3 * a.ventana))}


def escenas(a):
    cmd = [ffbin("ffmpeg"), "-v", "error", "-i", a.video, "-an", "-vf",
           f"scale=320:-2,select='gt(scene,{a.umbral})',metadata=print:file=-", "-f", "null", "-"]
    salida = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    cortes = [round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", salida)]
    dur = info_video(a.video)["duracion"] / S
    return {"duracion": round(dur, 2), "cortes": cortes, "plano_medio_s": round(dur / (len(cortes) + 1), 2)}


def fotogramas(a):
    os.makedirs(a.salida, exist_ok=True)
    patron = os.path.join(a.salida, Path(a.video).stem + "_%03d.jpg")
    subprocess.run([ffbin("ffmpeg"), "-v", "error", "-y", "-i", a.video, "-vf", f"fps=1/{a.cada},scale=540:-2", patron],
                   check=True)
    return {"capturas": sorted(str(p) for p in Path(a.salida).glob(Path(a.video).stem + "_*.jpg")), "cada_s": a.cada}


def beats(a):
    """Beats de cada canción del proyecto, en tiempo de la línea de tiempo. Salen del archivo .beat
    que CapCut descarga para su biblioteca de música (ms) o de las marcas manuales `user_beats` (µs)."""
    carpeta = Path(a.video) if Path(a.video).is_dir() else Path(CARPETA_CAPCUT) / a.video
    d = cargar(carpeta / "draft_content.json")
    mats = {m["id"]: (k, m) for k, l in d["materials"].items() if isinstance(l, list)
            for m in l if isinstance(m, dict) and "id" in m}
    canciones = []
    for pista in d["tracks"]:
        if pista["type"] != "audio":
            continue
        for s in pista["segments"]:
            nombre = mats.get(s["material_id"], (None, {}))[1].get("name", "?")
            b = next((mats[r][1] for r in s.get("extra_material_refs", []) if r in mats and mats[r][0] == "beats"), None)
            if not b:
                continue
            en_cancion, origen = [], "ninguno"
            ruta = (b.get("ai_beats") or {}).get("beats_path")
            if ruta and os.path.exists(ruta):
                en_cancion, origen = [ms * 1000 for ms in cargar(ruta).get("time", [])], "capcut"
            if b.get("user_beats"):
                en_cancion, origen = sorted(set(en_cancion) | set(b["user_beats"])), origen + "+manuales"
            src, tgt, vel = s["source_timerange"], s["target_timerange"], s.get("speed", 1) or 1
            linea = [round((tgt["start"] + (x - src["start"]) / vel) / S, 3) for x in en_cancion
                     if src["start"] <= x <= src["start"] + src["duration"]]
            bpm = round(60 / float(np.median(np.diff(linea))), 1) if len(linea) > 2 else None
            canciones.append({"cancion": nombre, "origen": origen, "bpm": bpm,
                              "en_linea_de_tiempo": [round(tgt["start"] / S, 2), round((tgt["start"] + tgt["duration"]) / S, 2)],
                              "beats": linea})
    if not canciones:
        return {"error": "ninguna pista de audio con beats: usa una canción de la biblioteca de CapCut o marca los beats a mano"}
    return {"proyecto": carpeta.name, "canciones": canciones}


def main():
    ap = argparse.ArgumentParser(description="Analiza vídeos para planear el montaje.")
    sub = ap.add_subparsers(dest="orden", required=True)
    for nombre, f in (("silencios", silencios), ("volumen", volumen), ("movimiento", movimiento),
                      ("escenas", escenas), ("fotogramas", fotogramas), ("beats", beats)):
        p = sub.add_parser(nombre)
        p.set_defaults(f=f)
        p.add_argument("video", help="vídeo (o nombre/carpeta del proyecto de CapCut para 'beats')")
        p.add_argument("--guardar", help="guardar también el resultado en este JSON")
        if nombre in ("silencios", "volumen"):
            p.add_argument("--pista", type=int, help="pista de audio (0, 1...) si hay varias")
        if nombre == "silencios":
            p.add_argument("--umbral", default="auto", help="dB por debajo de los cuales es silencio, o 'auto'")
            p.add_argument("--min", type=float, default=0.35, help="duración mínima de un silencio (s)")
        if nombre in ("volumen", "movimiento"):
            p.add_argument("--ventana", type=float, default=0.5)
            p.add_argument("--top", type=int, default=8)
        if nombre == "escenas":
            p.add_argument("--umbral", type=float, default=0.3, help="0-1: cuánto debe cambiar la imagen para contar como corte")
        if nombre == "fotogramas":
            p.add_argument("--salida", required=True)
            p.add_argument("--cada", type=float, default=2.0, help="una captura cada N segundos")
    a = ap.parse_args()
    r = a.f(a)
    texto = json.dumps(r, ensure_ascii=False)
    if a.guardar:
        with open(a.guardar, "w", encoding="utf-8") as f:
            f.write(texto)
    print(texto)


if __name__ == "__main__":
    main()
