# Crea un proyecto NUEVO de CapCut a partir de un plan JSON: cortes de uno o varios vídeos,
# zoom, velocidad, volumen y textos (subtítulos). No toca ningún proyecto existente: copia la
# plantilla de la skill (o un proyecto "base" del usuario, para conservar su música) en una
# carpeta nueva y la apunta en la lista de proyectos de CapCut.
# Uso: py -3 crear_proyecto.py plan.json [--comprobar]
#   --comprobar: lo genera en una carpeta temporal sin tocar CapCut (funciona con CapCut abierto).
# Formato del plan: ver references/capcut-formato.md.
import argparse, copy, glob, json, os, re, shutil, subprocess, sys, tempfile, time, uuid
from pathlib import Path

from comun import CARPETA_CAPCUT, S, capcut_abierto, cargar, ffbin, guardar, info_video

PLANTILLA = Path(__file__).resolve().parent.parent / "assets" / "plantilla-capcut"
SUBCARPETAS = ("adjust_mask", "common_attachment", "matting", "qr_upload", "Resources", "smart_crop", "subdraft")
MEDIOS = ("videos", "audios")  # materiales de medios: no se borran aunque el montaje no los use
ENTRADA = {  # entrada de la lista de proyectos (root_meta_info.json) con valores neutros
    "draft_cloud_last_action_download": False, "draft_cloud_purchase_info": "", "draft_cloud_template_id": "",
    "draft_cloud_tutorial_info": "", "draft_cloud_videocut_purchase_info": "", "draft_cover": "",
    "draft_fold_path": "", "draft_id": "", "draft_is_ai_shorts": False, "draft_is_invisible": False,
    "draft_json_file": "", "draft_name": "", "draft_new_version": "", "draft_root_path": "",
    "draft_timeline_materials_size": 0, "draft_type": "", "tm_draft_cloud_completed": "",
    "tm_draft_cloud_modified": 0, "tm_draft_create": 0, "tm_draft_modified": 0, "tm_draft_removed": 0, "tm_duration": 0}


def nid():
    return str(uuid.uuid4()).upper()


def refs(seg):
    return [seg.get("material_id")] + list(seg.get("extra_material_refs", []))


def tabla(mats):
    return {m["id"]: (k, m) for k, lst in mats.items() if isinstance(lst, list)
            for m in lst if isinstance(m, dict) and "id" in m}


def clonar(seg, mats_origen, mats_destino):
    """Copia un segmento con sus materiales auxiliares (velocidad, lienzo, animaciones...) e ids nuevos."""
    origen = tabla(mats_origen)
    nuevo = copy.deepcopy(seg)
    nuevo["id"] = nid()
    nuevo["extra_material_refs"] = []
    for r in seg.get("extra_material_refs", []):
        if r in origen:
            clave, m = origen[r]
            c = copy.deepcopy(m)
            c["id"] = nid()
            mats_destino.setdefault(clave, []).append(c)
            nuevo["extra_material_refs"].append(c["id"])
    return nuevo


def hex_rgb(h):
    h = h.lstrip("#")
    return [round(int(h[i:i + 2], 16) / 255, 4) for i in (0, 2, 4)]


def llenar(mw, mh, cw, ch):
    """Escala para que el vídeo cubra el lienzo entero (en CapCut 1 = encajar sin recortar)."""
    a, b = cw / mw, ch / mh
    return max(a, b) / min(a, b)


def fuente_capcut():
    """en.ttf de la versión más nueva de CapCut instalada (la ruta cambia con cada versión)."""
    cands = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\Apps\*\Resources\Font\SystemFont\en.ttf"))
    version = lambda p: tuple(int(x) for x in re.findall(r"\d+", Path(p).parents[3].name))
    return max(cands, key=version).replace("\\", "/") if cands else None


def main():
    ap = argparse.ArgumentParser(description="Crea un proyecto de CapCut a partir de un plan JSON.")
    ap.add_argument("plan")
    ap.add_argument("--comprobar", action="store_true", help="generarlo en una carpeta temporal, sin tocar CapCut")
    a = ap.parse_args()
    plan = cargar(a.plan)
    nombre = re.sub(r'[\\/:*?"<>|]', "-", plan["nombre"]).strip()
    if not plan.get("clips"):
        sys.exit("El plan no tiene clips.")
    if not a.comprobar and capcut_abierto():
        sys.exit("CapCut está abierto: ciérralo del todo (también el icono junto al reloj) y repite.")

    raiz = Path(tempfile.mkdtemp(prefix="capcut-comprobar-")) if a.comprobar else Path(CARPETA_CAPCUT)
    dst = raiz / nombre
    if dst.exists():
        sys.exit(f"Ya existe un proyecto llamado '{nombre}': usa otro nombre.")
    origen = Path(CARPETA_CAPCUT) / plan["base"] if plan.get("base") else PLANTILLA
    if not (origen / "draft_content.json").exists():
        sys.exit(f"No encuentro el proyecto base '{plan.get('base')}' en {CARPETA_CAPCUT}")
    shutil.copytree(origen, dst, ignore=shutil.ignore_patterns(".locked", "*.bak", "template-2.tmp", "draft_cover.jpg"))
    for c in SUBCARPETAS:
        (dst / c).mkdir(exist_ok=True)

    plant = cargar(PLANTILLA / "draft_content.json")
    plant_meta = cargar(PLANTILLA / "draft_meta_info.json")
    cont = cargar(dst / "draft_content.json")
    meta = cargar(dst / "draft_meta_info.json")
    mats = cont["materials"]
    ancho, alto = plan.get("lienzo", [1080, 1920])
    cont["canvas_config"].update(width=ancho, height=alto)
    draft_id = nid()
    cont["id"] = draft_id

    grupo = next((g for g in meta["draft_materials"] if g["type"] == 0), None)
    if grupo is None:
        grupo = {"type": 0, "value": []}
        meta["draft_materials"].append(grupo)
    lista_meta = grupo["value"]  # biblioteca de medios del proyecto
    if origen == PLANTILLA:  # el vídeo de la plantilla es ficticio
        mats["videos"] = []
        lista_meta.clear()

    # Se conservan las pistas de audio (la música del proyecto base); vídeo y textos se rehacen
    quitados = {r for t in cont["tracks"] if t["type"] != "audio" for s in t["segments"] for r in refs(s)}
    pv_plant = next(t for t in plant["tracks"] if t["type"] == "video")
    pt_plant = next(t for t in plant["tracks"] if t["type"] == "text")
    seg_v, seg_t = pv_plant["segments"][0], pt_plant["segments"][0]
    texto_plant = tabla(plant["materials"])[seg_t["material_id"]][1]
    video_plant = plant["materials"]["videos"][0]
    item_plant = next(g for g in plant_meta["draft_materials"] if g["type"] == 0)["value"][0]

    def pista(modelo):
        p = copy.deepcopy(modelo)
        p["id"] = nid()
        p["segments"] = []
        return p

    medios = {os.path.normcase(os.path.abspath(m["path"])): m for m in mats.get("videos", []) if m.get("path")}

    def medio(ruta):
        """Material de vídeo del proyecto para esa ruta; si no está, lo importa."""
        ruta = os.path.abspath(ruta)
        clave = os.path.normcase(ruta)
        if clave in medios:
            return medios[clave]
        if not os.path.exists(ruta):
            sys.exit(f"No existe el vídeo {ruta}")
        inf = info_video(ruta)
        m = copy.deepcopy(video_plant)
        m.update(id=nid(), local_material_id=str(uuid.uuid4()), path=ruta.replace("\\", "/"),
                 material_name=os.path.basename(ruta), duration=inf["duracion"], width=inf["ancho"], height=inf["alto"])
        m["video_algorithm"]["time_range"] = {"start": 0, "duration": inf["duracion"]}
        mats.setdefault("videos", []).append(m)
        ahora = time.time()
        it = copy.deepcopy(item_plant)
        it.update(id=m["local_material_id"], file_Path=m["path"], extra_info=m["material_name"],
                  duration=inf["duracion"], width=inf["ancho"], height=inf["alto"],
                  roughcut_time_range={"start": 0, "duration": inf["duracion"]},
                  create_time=int(ahora), import_time=int(ahora), import_time_ms=int(ahora * 1000))
        lista_meta.append(it)
        medios[clave] = m
        return m

    # Vídeo: los clips van seguidos en la pista principal
    pista_v = pista(pv_plant)
    usados, t = set(), 0
    for i, c in enumerate(plan["clips"], 1):
        m = medio(c["video"])
        ini, fin = float(c["inicio"]), float(c["fin"])
        if fin > m["duration"] / S + 0.05:
            print(f"aviso: el clip {i} acaba en {fin} s y el vídeo dura {m['duration'] / S:.2f} s; lo recorto")
            fin = m["duration"] / S
        if fin - ini < 0.05:
            sys.exit(f"El clip {i} es demasiado corto ({ini}-{fin} s).")
        vel = float(c.get("velocidad", 1.0))
        src = int(round((fin - ini) * S))
        tgt = int(round(src / vel))  # a velocidad 0,5 ocupa el doble en la línea de tiempo
        s = clonar(seg_v, plant["materials"], mats)
        s["material_id"] = m["id"]
        s["source_timerange"] = {"start": int(round(ini * S)), "duration": src}
        s["target_timerange"] = {"start": t, "duration": tgt}
        s["speed"] = vel
        for sp in mats.get("speeds", []):
            if sp["id"] in s["extra_material_refs"]:
                sp["speed"] = vel
        escala = (llenar(m["width"], m["height"], ancho, alto) if c.get("llenar", True) else 1.0) * float(c.get("zoom", 1.0))
        s["clip"]["scale"] = {"x": round(escala, 4), "y": round(escala, 4)}
        s["clip"]["transform"] = {"x": float(c.get("x", 0.0)), "y": float(c.get("y", 0.0))}
        s["volume"] = float(c.get("volumen", 1.0))
        pista_v["segments"].append(s)
        usados.add(m["path"])
        t += tgt

    # Textos: cada uno en la primera pista de texto donde no se solape con otro
    fuente = fuente_capcut()
    pistas_t, avisos = [], []
    for x in sorted(plan.get("textos", []), key=lambda x: float(x["inicio"])):
        ini, fin = float(x["inicio"]), float(x["fin"])
        txt, tam = x["texto"], float(x.get("tam", 9))
        # Reglas de subtítulos (references/estilos.md): solo avisan, no bloquean
        corto = txt.replace("\n", " ")[:24]
        if fin - ini < 0.95:
            avisos.append(f"'{corto}' dura {fin - ini:.2f} s: el mínimo es 1 s (0,6 s si es una palabra de impacto)")
        if alto > ancho:  # lienzo vertical: zonas que tapa la interfaz de TikTok
            y = float(x.get("y", -0.4))
            if y < -0.5 or y > 0.75:
                avisos.append(f"'{corto}' está en y={y}: lo tapa la interfaz de TikTok (usa entre -0,5 y 0,75)")
            if any(len(linea) > 20 for linea in txt.split("\n")):
                avisos.append(f"'{corto}' tiene líneas de más de 20 caracteres: córtalo en dos subtítulos")
        color, borde = x.get("color", "#FFFFFF"), x.get("borde", "#000000")
        tm = copy.deepcopy(texto_plant)
        tm["id"] = nid()
        c = json.loads(tm["content"])
        c["text"] = txt
        for st in c.get("styles", []):
            st["range"] = [0, len(txt.encode("utf-16-le")) // 2]  # CapCut cuenta en UTF-16 (un emoji = 2)
            st["size"] = tam
            st.setdefault("fill", {}).setdefault("content", {"render_type": "solid", "solid": {}}) \
              .setdefault("solid", {})["color"] = hex_rgb(color)
            if fuente:
                st.setdefault("font", {})["path"] = fuente
            if borde:
                st["strokes"] = [{"alpha": 1.0, "width": float(x.get("grosor_borde", 0.08)),
                                  "content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": hex_rgb(borde)}}}]
            else:
                st.pop("strokes", None)
        tm["content"] = json.dumps(c, ensure_ascii=False)
        tm.update(font_size=tam, text_color=color.upper(), text_to_audio_ids=[])
        if borde:
            tm.update(border_color=borde, check_flag=tm.get("check_flag", 7) | 8)
        mats.setdefault("texts", []).append(tm)
        s = clonar(seg_t, plant["materials"], mats)
        s["material_id"] = tm["id"]
        s["target_timerange"] = {"start": int(round(ini * S)), "duration": int(round((fin - ini) * S))}
        s["clip"]["transform"] = {"x": float(x.get("x", 0.0)), "y": float(x.get("y", -0.4))}
        destino = next((p for p in pistas_t if sum(p["segments"][-1]["target_timerange"].values()) <= s["target_timerange"]["start"]), None)
        if destino is None:
            destino = pista(pt_plant)
            pistas_t.append(destino)
        destino["segments"].append(s)

    cont["tracks"] = [pista_v] + [t for t in cont["tracks"] if t["type"] == "audio"] + pistas_t
    vivos = {r for tr in cont["tracks"] for s in tr["segments"] for r in refs(s)}
    for k, lst in mats.items():  # quitar los materiales que solo usaban las pistas rehechas
        if k not in MEDIOS and isinstance(lst, list):
            mats[k] = [m for m in lst if not (isinstance(m, dict) and m.get("id") in quitados - vivos)]
    cont["duration"] = max(sum(s["target_timerange"].values()) for tr in cont["tracks"] for s in tr["segments"])

    rotas = [r for r in vivos if r not in tabla(mats)]
    if rotas:
        sys.exit(f"Error interno: {len(rotas)} referencias rotas; no lo apunto en CapCut. Carpeta: {dst}")
    for n in ("draft_content.json", "draft_content.json.bak", "template-2.tmp"):
        guardar(dst / n, cont)

    ahora = int(time.time() * S)
    ruta = str(dst).replace("\\", "/")
    meta.update(draft_id=draft_id, draft_name=nombre, draft_fold_path=ruta, draft_root_path=str(raiz),
                draft_cover="draft_cover.jpg", tm_draft_create=ahora, tm_draft_modified=ahora,
                tm_duration=cont["duration"],
                draft_timeline_materials_size_=sum(os.path.getsize(p) for p in usados if os.path.exists(p)))
    guardar(dst / "draft_meta_info.json", meta)

    c0 = plan["clips"][0]  # portada: un fotograma del primer clip con el encuadre del lienzo
    subprocess.run([ffbin("ffmpeg"), "-v", "error", "-y", "-ss", str(float(c0["inicio"]) + 0.3), "-i", c0["video"],
                    "-vf", f"scale={ancho}:{alto}:force_original_aspect_ratio=increase,crop={ancho}:{alto}",
                    "-frames:v", "1", str(dst / "draft_cover.jpg")])

    resumen = (f"{nombre} | {cont['duration'] / S:.1f} s | {len(pista_v['segments'])} clips | "
               f"{sum(len(p['segments']) for p in pistas_t)} textos en {len(pistas_t)} pistas | fuente {'ok' if fuente else 'no encontrada'}")
    if avisos:
        print(f"{len(avisos)} avisos de subtítulos:\n  - " + "\n  - ".join(avisos))
    if a.comprobar:
        print(f"Comprobado (no está en CapCut): {resumen}\nCarpeta temporal: {dst}")
        return

    indice_ruta = Path(CARPETA_CAPCUT) / "root_meta_info.json"
    indice = cargar(indice_ruta) if indice_ruta.exists() else {"all_draft_store": [], "draft_ids": 0, "root_path": CARPETA_CAPCUT}
    if indice_ruta.exists():
        shutil.copy2(indice_ruta, Path(tempfile.gettempdir()) / f"root_meta_info.{int(time.time())}.json")
    otra = indice["all_draft_store"][0] if indice["all_draft_store"] else {}
    entrada = {**otra, **ENTRADA}  # campos nuevos de la versión instalada + valores neutros
    entrada.update(draft_id=draft_id, draft_name=nombre, draft_fold_path=ruta, draft_root_path=CARPETA_CAPCUT,
                   draft_cover=f"{ruta}\\draft_cover.jpg", draft_json_file=f"{ruta}\\draft_content.json",
                   tm_draft_create=ahora, tm_draft_modified=ahora, tm_duration=cont["duration"],
                   draft_timeline_materials_size=meta["draft_timeline_materials_size_"])
    indice["all_draft_store"].insert(0, entrada)
    if isinstance(indice.get("draft_ids"), int):
        indice["draft_ids"] += 1
    guardar(indice_ruta, indice)
    print(f"Creado en CapCut: {resumen}")


if __name__ == "__main__":
    main()
