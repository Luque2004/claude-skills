# Resume proyectos de CapCut (draft_content.json) sin modificarlos: lienzo, cortes, escalas,
# velocidades, textos con su estilo, efectos, música y vídeos fuente. Sirve para sacar el
# estilo de un proyecto ya editado.
# Uso: py -3 resumen_capcut.py [PROYECTO ...]   (sin nombres: todos los proyectos)
import json, os, re, statistics, sys
from collections import Counter

from comun import CARPETA_CAPCUT, cargar


def seg(us):  # microsegundos -> segundos
    return round(us / 1_000_000, 2)


proyectos = sys.argv[1:] or sorted(os.listdir(CARPETA_CAPCUT))
for nombre in proyectos:
    ruta = os.path.join(CARPETA_CAPCUT, nombre, "draft_content.json")
    if not os.path.exists(ruta):
        continue
    d = cargar(ruta)
    c = d.get("canvas_config", {})
    print(f"\n=== {nombre} | {c.get('width')}x{c.get('height')} | {seg(d.get('duration', 0))} s | fps {d.get('fps')}")
    m = d.get("materials", {})
    videos = {v["id"]: v for v in m.get("videos", [])}

    for t in d.get("tracks", []):
        segs = t.get("segments", [])
        if not segs:
            continue
        durs = [seg(s["target_timerange"]["duration"]) for s in segs]
        extra = ""
        if t["type"] == "video":
            # escala junto al tamaño del medio, para distinguir zoom de "llenar el lienzo"
            escalas = Counter((round(s.get("clip", {}).get("scale", {}).get("x", 1), 2),
                               f"{videos.get(s['material_id'], {}).get('width')}x{videos.get(s['material_id'], {}).get('height')}")
                              for s in segs)
            velocidades = Counter(round(s.get("speed", 1), 2) for s in segs)
            kf = sum(1 for s in segs if s.get("common_keyframes"))
            extra = f" | escala×medio {dict(escalas)} | velocidad {dict(velocidades)} | con keyframes {kf}"
        print(f"  pista {t['type']}: {len(segs)} segmentos, media {statistics.mean(durs):.2f} s, "
              f"min {min(durs)} s, max {max(durs)} s{extra}")

    print("  materiales:", {k: len(v) for k, v in m.items() if isinstance(v, list) and v})
    fondos = Counter(f"{x.get('type')}{':' + str(x.get('blur')) if x.get('type') == 'canvas_blur' else ''}"
                     for x in m.get("canvases", []))
    if fondos:
        print(f"  fondos del lienzo: {dict(fondos)}")

    for tx in m.get("texts", [])[:5]:
        contenido = tx.get("content", "")
        try:
            cj = json.loads(contenido)
            st = (cj.get("styles") or [{}])[0]
            print(f"  texto: {cj.get('text', '')[:40]!r} | fuente {os.path.basename(st.get('font', {}).get('path', ''))} "
                  f"| tam {st.get('size')} | color {st.get('fill', {}).get('content', {}).get('solid', {}).get('color')} "
                  f"| borde {bool(st.get('strokes'))}")
        except (json.JSONDecodeError, AttributeError):
            print(f"  texto: {re.sub('<[^>]+>', '', contenido)[:40]!r} | tam {tx.get('font_size')} | color {tx.get('text_color')}")
    if m.get("texts"):
        print(f"  ({len(m['texts'])} textos)")

    for clave in ("video_effects", "effects", "transitions", "filters", "stickers", "audios", "material_animations"):
        nombres = Counter(x.get("name") or x.get("type") for x in m.get(clave, []) if (x.get("name") or x.get("type")))
        if nombres:
            print(f"  {clave}: {dict(nombres.most_common(6))}")
    fuentes = Counter(os.path.basename(v.get("path", "")) for v in m.get("videos", []))
    print(f"  vídeos fuente: {len(fuentes)} ({', '.join(list(fuentes)[:3])})")
