# Utilidades compartidas por los scripts de la skill: localizar ffmpeg y CapCut,
# leer el audio de un vídeo y sacar sus datos (duración, tamaño, rotación, pistas).
import glob, json, os, shutil, subprocess, sys

sys.stdout.reconfigure(errors="replace")  # la consola de Windows no siempre acepta UTF-8

S = 1_000_000  # CapCut mide el tiempo en microsegundos
CARPETA_CAPCUT = os.path.expandvars(r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft")


def ffbin(nombre):
    """Ruta de ffmpeg/ffprobe: el del PATH o el que instala winget (Gyan.FFmpeg)."""
    ruta = shutil.which(nombre)
    if ruta:
        return ruta
    hallados = glob.glob(os.path.expandvars(
        rf"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\{nombre}.exe"))
    if not hallados:
        sys.exit(f"No encuentro {nombre}. Instálalo con: winget install Gyan.FFmpeg")
    return sorted(hallados)[-1]


def leer_audio(ruta, hasta=None, pista=None, frecuencia=16000):
    """Audio mono en decimales (numpy float32). Lo saca ffmpeg porque el lector de
    faster-whisper falla con PyAV 19 (TypeError: metadata_errors)."""
    import numpy as np
    cmd = [ffbin("ffmpeg"), "-v", "error", "-i", ruta]
    if pista is not None:
        cmd += ["-map", f"0:a:{pista}"]  # p. ej. los clips de Medal traen juego y micro por separado
    if hasta:
        cmd += ["-t", str(hasta)]
    cmd += ["-vn", "-ac", "1", "-ar", str(frecuencia), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)


def info_video(ruta):
    """Duración (µs), ancho y alto tal como se ve (con la rotación del móvil aplicada) y nº de pistas de audio."""
    salida = subprocess.run([ffbin("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", ruta],
                            capture_output=True, text=True, encoding="utf-8", check=True).stdout
    d = json.loads(salida)
    v = next((s for s in d["streams"] if s.get("codec_type") == "video"), None)
    if v is None:
        sys.exit(f"{ruta} no tiene imagen de vídeo")
    ancho, alto = v["width"], v["height"]
    rot = 0
    for sd in v.get("side_data_list", []):
        rot = sd.get("rotation", rot)
    rot = int(float(v.get("tags", {}).get("rotate", rot) or 0))
    if abs(rot) % 180 == 90:  # vídeo vertical del iPhone guardado en horizontal + rotación
        ancho, alto = alto, ancho
    return {"duracion": int(float(d["format"]["duration"]) * S), "ancho": ancho, "alto": alto,
            "pistas_audio": sum(1 for s in d["streams"] if s.get("codec_type") == "audio")}


def capcut_abierto():
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe"], capture_output=True, text=True)
    return "CapCut.exe" in r.stdout


def cargar(ruta):
    with open(ruta, encoding="utf-8-sig") as f:  # -sig: acepta JSON guardados con BOM (PowerShell, Bloc de notas)
        return json.load(f)


def guardar(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(json.dumps(datos, ensure_ascii=False, separators=(",", ":")))
