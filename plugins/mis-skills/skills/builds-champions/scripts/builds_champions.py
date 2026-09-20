#!/usr/bin/env python3
"""Pipeline para mantener las builds de Pokémon Champions del bot de Discord.

Pasos (subcomandos):
  roster     Detecta la regulación vigente en metavgc, lee su roster y resuelve la clave PokeAPI de cada Pokémon.
  descargar  Descarga la página de metavgc de cada Pokémon del roster.
  generar    Genera builds__vgc_api.json (inglés) a partir de los datos descargados.
  traducir   Genera builds__vgc_api_es.json con nombres oficiales en español (PokeAPI + overrides).
  aliases    Actualiza los bloques de alias de Main.py (entre marcadores).
  validar    Comprueba el JSON como lo lee el bot y que todas las claves existen en PokeAPI.
  todo       Ejecuta todos los pasos en orden.

Uso típico:
  py builds_champions.py todo --bot-dir "C:/Users/maxlu/Documents/discord-bot/bot_0"

Todo lo que el script no pueda resolver solo (nombres nuevos, movimientos sin datos, términos sin traducción)
lo imprime bajo "REVISAR:"; se corrige añadiendo entradas a overrides.json y repitiendo el paso.
"""
import argparse, json, os, re, sys, tempfile, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0"}
METAVGC = "https://metavgc.com"
POKEAPI = "https://pokeapi.co/api/v2"
AQUI = os.path.dirname(os.path.abspath(__file__))
OVERRIDES_DEF = os.path.join(AQUI, "..", "overrides.json")
FLIGHT_RE = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')
DEC = json.JSONDecoder()
STATS = ["HP", "AT", "DEF", "SPA", "SPD", "SPEED"]

# ----------------------------------------------------------------------------- utilidades

def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def http_json(url):
    try:
        return json.loads(http_get(url))
    except Exception:
        return None

def flight(html):
    """Une los trozos self.__next_f.push([1,"..."]) de una página Next.js en un solo texto."""
    return "".join(json.loads('"' + c + '"') for c in FLIGHT_RE.findall(html))

def extract(data, key):
    """Decodifica el objeto/array JSON que sigue a "key": dentro del texto flight."""
    i = data.find(f'"{key}":')
    if i < 0:
        return None
    obj, _ = DEC.raw_decode(data, i + len(key) + 3)
    return obj

def slugify(nombre):
    s = nombre.lower().replace("’", "").replace("'", "").replace(".", "").replace(":", "")
    return re.sub(r"[\s_]+", "-", s).strip("-")

def leer_json(ruta, defecto=None):
    if os.path.exists(ruta):
        return json.load(open(ruta, encoding="utf-8"))
    return defecto

def escribir_json(ruta, obj, crlf=True):
    with open(ruta, "w", encoding="utf-8", newline="\r\n" if crlf else "\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")

def revisar(titulo, lista):
    if lista:
        print(f"REVISAR: {titulo} ({len(lista)})")
        for x in lista:
            print(f"   - {x}")

class Ctx:
    def __init__(self, args):
        self.bot_dir = os.path.abspath(args.bot_dir)
        self.cache = os.path.abspath(args.cache_dir)
        os.makedirs(os.path.join(self.cache, "mv"), exist_ok=True)
        self.ov = leer_json(os.path.abspath(args.overrides), {})
        self.regulacion = args.regulacion
        self.json_en = os.path.join(self.bot_dir, "builds__vgc_api.json")
        self.json_es = os.path.join(self.bot_dir, "builds__vgc_api_es.json")
        self.main_py = os.path.join(self.bot_dir, "Main.py")
        self.roster_path = os.path.join(self.cache, "roster.json")
        self.datos_path = os.path.join(self.cache, "mv_data.json")

# Formas regionales: sufijo PokeAPI -> prefijo inglés. En español se escribe igual que la clave
# ("raichu-alola"), así que no necesita alias.
REGIONES = {"alola": "alolan", "galar": "galarian", "hisui": "hisuian", "paldea": "paldean"}

def alias_de_clave(clave, ovr):
    """Alias que se deducen de la clave PokeAPI ('ninetales-alola' -> alolan-ninetales)
    más los manuales de overrides.roster.alias_extra."""
    out = set(ovr.get("alias_extra", {}).get(clave, []))
    for suf, pref_en in REGIONES.items():
        if clave.endswith("-" + suf):
            out.add(f"{pref_en}-{clave[:-len(suf) - 1]}")
    return out

# ----------------------------------------------------------------------------- 1. roster

def regulacion_actual():
    """Devuelve el slug de la regulación más reciente listada en metavgc (p. ej. 'regulationm-c')."""
    html = http_get(f"{METAVGC}/regulations")
    slugs = sorted(set(re.findall(r'href="/regulations/(regulation[a-z0-9-]+)"', html)))
    if not slugs:
        sys.exit("No se encontraron regulaciones en metavgc.com/regulations")
    return slugs[-1]

def roster_metavgc(reg):
    """Lee la lista 'pokemon-grid' de la página de la regulación, resolviendo referencias $Lxx."""
    data = flight(http_get(f"{METAVGC}/regulations/{reg}"))
    i = data.find('"id":"pokemon-grid"')
    if i < 0:
        sys.exit(f"La página de {reg} no tiene lista pokemon-grid")
    children = extract(data[i:], "children")
    filas = {m.group(1): m.start() for m in re.finditer(r"^([0-9a-f]+):", data, re.M)}
    nombres = []
    for el in children:
        if isinstance(el, str) and el.startswith("$L"):
            pos = filas.get(el[2:])
            if pos is None:
                continue
            el, _ = DEC.raw_decode(data, data.index(":", pos) + 1)
        if isinstance(el, list) and len(el) >= 3 and el[1] == "li":
            nombres.append(el[2])
    return nombres

def nombre_en(nombre, ov):
    """Nombre bonito en inglés a partir del nombre de metavgc ('Persian Alola' -> 'Alolan Persian')."""
    if nombre in ov.get("nombres_en", {}):
        return ov["nombres_en"][nombre]
    for suf, pref in (("Alola", "Alolan"), ("Galar", "Galarian"), ("Hisui", "Hisuian"), ("Paldea", "Paldean")):
        if nombre.endswith(" " + suf):
            return f"{pref} {nombre[:-len(suf) - 1]}"
    for suf in ("Female", "Male"):
        if nombre.endswith(" " + suf):
            return f"{nombre[:-len(suf) - 1]} ({suf})"
    return nombre

def resolver_clave(nombre, ov):
    """Clave PokeAPI del Pokémon: override > /pokemon/slug > variedad por defecto de /pokemon-species/slug."""
    if nombre in ov.get("claves", {}):
        return ov["claves"][nombre], "override"
    slug = slugify(nombre)
    if http_json(f"{POKEAPI}/pokemon/{slug}"):
        return slug, "pokemon"
    sp = http_json(f"{POKEAPI}/pokemon-species/{slug}")
    if sp:
        for v in sp.get("varieties", []):
            if v.get("is_default"):
                return v["pokemon"]["name"], "species"
    return None, None

def cmd_roster(ctx):
    reg = ctx.regulacion or regulacion_actual()
    print(f"Regulación: {reg}")
    ovr = ctx.ov.get("roster", {})
    crudos = roster_metavgc(reg)
    print(f"Pokémon listados en metavgc: {len(crudos)}")
    nombres = []
    for n in crudos:
        if n.startswith("Mega "):
            continue                                   # las Megas van dentro de su especie
        n = ovr.get("sinonimos", {}).get(n, n)
        if n is None or n in ovr.get("omitir", []):
            continue
        if n not in nombres:
            nombres.append(n)
    with ThreadPoolExecutor(8) as ex:
        claves = list(ex.map(lambda n: resolver_clave(n, ovr), nombres))
    roster, vistos, sin_clave = [], set(), []
    for n, (clave, via) in zip(nombres, claves):
        if not clave:
            sin_clave.append(n)
            continue
        if clave in vistos:
            continue
        vistos.add(clave)
        slug = slugify(n)
        aliases = alias_de_clave(clave, ovr)
        if slug != clave:
            aliases.add(slug)
        roster.append({"display": nombre_en(n, ovr), "metavgc": n, "key": clave,
                       "slug": ovr.get("slug_metavgc", {}).get(n, slug), "aliases": sorted(aliases), "via": via})
    # Formas regionales: metavgc lista solo la especie ("Arcanine"), pero Arcanine de Hisui tiene sus propios datos.
    # Se añaden como candidatas todas las variedades regionales de PokeAPI; 'generar' descarta las que no tengan uso.
    def formas_de(p):
        sp = http_json(f"{POKEAPI}/pokemon-species/{p['key'].split('-')[0]}") if p["via"] != "override" else None
        out = []
        for v in (sp or {}).get("varieties", []):
            nombre = v["pokemon"]["name"]
            m = re.match(r"^(.+)-(alola|galar|hisui|paldea)$", nombre)
            if m and nombre not in vistos:
                base = p["display"] if "-" not in p["key"] else m.group(1).capitalize()
                pref = {"alola": "Alolan", "galar": "Galarian", "hisui": "Hisuian", "paldea": "Paldean"}[m.group(2)]
                out.append({"display": f"{pref} {base}", "metavgc": nombre, "key": nombre, "slug": nombre,
                            "aliases": sorted(alias_de_clave(nombre, ovr)), "via": "forma"})
        return out
    with ThreadPoolExecutor(8) as ex:
        formas = [f for lista in ex.map(formas_de, list(roster)) for f in lista]
    for f in formas:
        if f["key"] not in vistos:
            vistos.add(f["key"])
            roster.append(f)
    escribir_json(ctx.roster_path, {"regulacion": reg, "pokemon": roster}, crlf=False)
    print(f"Roster resuelto: {len(roster)} entradas ({len(formas)} formas regionales candidatas) -> {ctx.roster_path}")
    revisar("nombres sin clave PokeAPI (añadir a overrides.roster.claves o .sinonimos)", sin_clave)
    return roster

# ----------------------------------------------------------------------------- 2. descargar

def cmd_descargar(ctx):
    roster = leer_json(ctx.roster_path)["pokemon"]
    def bajar(p):
        try:
            html = http_get(f"{METAVGC}/pokemon/{p['slug']}")
            open(os.path.join(ctx.cache, "mv", p["key"] + ".html"), "w", encoding="utf-8").write(html)
            return None
        except Exception as e:
            return f"{p['slug']}: {e}"
    with ThreadPoolExecutor(8) as ex:
        errores = [e for e in ex.map(bajar, roster) if e]
    print(f"Descargadas {len(roster) - len(errores)} páginas de metavgc en {os.path.join(ctx.cache, 'mv')}")
    revisar("descargas fallidas", errores)

# ----------------------------------------------------------------------------- 3. generar

def parse_pagina(ctx, p):
    html = open(os.path.join(ctx.cache, "mv", p["key"] + ".html"), encoding="utf-8").read()
    data = flight(html)
    det = extract(data, "initialDetails")
    if not det:
        return None
    pc = extract(data, "pcAbility") or {}
    mega = extract(data, "championsMegaAbility") or {}
    return {
        "formatId": det.get("formatId"), "period": det.get("period"),
        "rawCount": det.get("rawCount") or 0, "usage": det.get("usage") or 0,
        "natures": [(n["name"], n["pct"]) for n in det.get("natures", [])],
        "items": [(n["name"], n["pct"]) for n in det.get("items", [])],
        "abilities": [(n["name"], n["pct"]) for n in det.get("abilities", [])],
        "moves": [(n["name"], n["pct"]) for n in det.get("moves", [])],
        "pcAbility": pc.get("displayName"), "megaAbility": mega.get("displayName"),
    }

CHOICE = {"Choice Scarf", "Choice Band", "Choice Specs", "Assault Vest"}
PROTECT = {"Protect", "Detect"}
TR_NATURES = {"Brave", "Quiet", "Relaxed", "Sassy"}
SETUP = {"Swords Dance", "Nasty Plot", "Calm Mind", "Dragon Dance", "Bulk Up", "Coil", "Quiver Dance", "Iron Defense",
         "Agility", "Shell Smash", "Curse", "Belly Drum", "Shift Gear", "Victory Dance"}
STATUS = {"Tailwind", "Trick Room", "Helping Hand", "Follow Me", "Rage Powder", "Reflect", "Light Screen", "Will-O-Wisp",
          "Thunder Wave", "Spore", "Sleep Powder", "Yawn", "Taunt", "Encore", "Coaching", "Ally Switch", "Wide Guard",
          "Quick Guard", "Recover", "Roost", "Substitute", "Toxic", "Hypnosis", "Sunny Day", "Rain Dance", "Snowscape",
          "Sandstorm", "Haze", "Parting Shot", "Trick", "Disable", "Imprison", "Safeguard", "Heal Pulse", "Life Dew",
          "Wish", "Decorate", "Charm", "Confuse Ray", "Torment", "Shed Tail", "Stun Spore", "Fake Tears", "Screech",
          "Aurora Veil", "Lunar Blessing", "Sing", "Lovely Kiss", "Dark Void", "Skill Swap", "Psych Up", "Instruct",
          "After You", "Quash", "Stealth Rock", "Spikes", "Sticky Web", "Transform", "Baton Pass", "Memento",
          "Final Gambit"}
STONE_RE = re.compile(r"^[A-Z][a-z]+ite( [XYZ])?$")

def es_piedra(item):
    return bool(STONE_RE.match(item))

def parse_nature(s):
    m = re.match(r"^([A-Za-z]+) (\d+)/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)$", s)
    if not m:
        return None
    sp = tuple(int(x) for x in m.groups()[1:])
    if sum(sp) > 66 or max(sp) > 32:
        return None
    return m.group(1).capitalize(), sp

def rol(nature, sp, moves):
    hp, at, df, spa, spd, spe = sp
    top = [m.split(" / ")[0] for m in moves]
    setup = [m for m in top if m in SETUP]
    if setup:
        return setup[0]
    if nature in TR_NATURES or "Trick Room" in top:
        return "Trick Room"
    if sum(1 for m in top if m in STATUS) >= 2:
        return "Support"
    off, fast, bulk = (at >= 24 or spa >= 24), spe >= 24, (hp >= 24 or df >= 24 or spd >= 24)
    if off and fast and bulk:
        return "Bulky Offensive"
    if off and fast:
        return "Offensive"
    if off and bulk:
        return "Bulky Attacker"
    if bulk:
        return "Bulky"
    if fast:
        return "Fast Support"
    return "Standard"

def nombre_build(item, nature, sp, moves):
    r = rol(nature, sp, moves)
    if es_piedra(item):
        suf = item.split(" ")[1] if " " in item else ""
        return f"Mega{(' ' + suf) if suf else ''} {r}".strip()
    return f"{r} {item}"

def habilidad(d, item, ov):
    abs_ = [(a, p) for a, p in d["abilities"] if p and p > 0]
    base = abs_[0][0] if abs_ else (d["pcAbility"] or (d["abilities"][0][0] if d["abilities"] else "-"))
    if es_piedra(item):
        mega = ov.get("habilidad_piedra", {}).get(item, d["megaAbility"])
        if base == mega and d["pcAbility"]:
            base = d["pcAbility"]
        return f"{base} (Mega: {mega})" if mega else f"{base} (Mega)"
    if base == d["megaAbility"] and d["pcAbility"]:
        base = d["pcAbility"]
    return base

def movimientos(d, item, key, ov):
    mv = ov.get("movimientos", {}).get(key) or [(m, p) for m, p in d["moves"] if p and p > 0]
    if not mv:
        return None
    mv = [tuple(x) for x in mv]
    names = [m for m, _ in mv]
    if item in CHOICE:
        names = [m for m in names if m not in PROTECT]
    elif "Protect" in names and "Detect" in names:
        names.remove("Detect")
    top, resto = names[:4], [m for m in names[4:] if m not in PROTECT]
    alt = resto[0] if resto and dict(mv)[resto[0]] >= 6 else None
    prot = [m for m in top if m in PROTECT]
    top = [m for m in top if m not in PROTECT] + prot
    if alt:
        i = len(top) - 1 - len(prot)
        if i >= 0:
            top[i] = f"{top[i]} / {alt}"
    while len(top) < 4:
        top.append("-")
    return top

def builds_de(d, key, ov):
    n = d["rawCount"]
    max_b = 1 if n < 30 else (2 if n < 200 else 3)
    spreads = [x for x in (parse_nature(s) for s, p in d["natures"] if p >= 10) if x]
    if not spreads:
        spreads = [x for x in (parse_nature(s) for s, p in d["natures"]) if x][:1]
    items = [i for i, p in d["items"] if p >= 10] or [i for i, p in d["items"]][:1] or ["-"]
    if not spreads:
        return []
    out, vistos = [], []
    for i in range(min(max_b, max(len(spreads), len(items)))):
        nature, evs = spreads[min(i, len(spreads) - 1)]
        item = items[min(i, len(items) - 1)]
        if any(vi == item and vn == nature and sum(abs(a - b) for a, b in zip(ve, evs)) <= 6 for vi, vn, ve in vistos):
            continue
        vistos.append((item, nature, evs))
        moves = movimientos(d, item, key, ov)
        if moves is None:
            return []
        nombre = nombre_build(item, nature, evs, moves)
        if any(b["build_name"] == nombre for b in out):
            nombre = f"{nombre} ({nature})"
        if any(b["build_name"] == nombre for b in out):
            nombre = f"{nombre_build(item, nature, evs, moves)} ({'/'.join(map(str, evs))})"
        out.append({"build_name": nombre, "item": item, "nature": nature, "ability": habilidad(d, item, ov),
                    "moves": {f"move{j + 1}": m for j, m in enumerate(moves)},
                    "evs": dict(zip(STATS, (str(v) for v in evs)))})
    return out

def cmd_generar(ctx):
    roster = leer_json(ctx.roster_path)["pokemon"]
    datos, entradas, sin_datos, sin_moves, pocos, formatos = {}, [], [], [], [], {}
    for p in roster:
        try:
            d = parse_pagina(ctx, p)
        except FileNotFoundError:
            d = None
        if not d or not d["natures"]:
            if p["via"] != "forma":                    # las formas candidatas sin uso se descartan en silencio
                sin_datos.append(p["display"])
            continue
        datos[p["key"]] = d
        formatos[d["formatId"]] = formatos.get(d["formatId"], 0) + 1
        b = builds_de(d, p["key"], ctx.ov)
        if not b:
            sin_moves.append(f"{p['display']} ({p['key']}, {d['rawCount']} muestras)")
            continue
        if d["rawCount"] < 10:
            pocos.append(f"{p['display']} ({d['rawCount']})")
        entradas.append((d["usage"], p, b))
    escribir_json(ctx.datos_path, datos, crlf=False)
    resultado = {}
    for _, p, b in sorted(entradas, key=lambda t: -t[0]):
        resultado[p["key"]] = [{"pokemon_name": p["display"], "builds": {str(i + 1): x for i, x in enumerate(b)}}]
    anterior = leer_json(ctx.json_en, {})
    escribir_json(ctx.json_en, resultado)
    nuevos = [k for k in resultado if k not in anterior]
    quitados = [k for k in anterior if k not in resultado]
    print(f"Escrito {ctx.json_en}: {len(resultado)} Pokémon, {sum(len(v[0]['builds']) for v in resultado.values())} builds")
    print(f"Formatos de los datos: {formatos}")
    print(f"Nuevos respecto al archivo anterior ({len(nuevos)}): {nuevos}")
    print(f"Quitados respecto al archivo anterior ({len(quitados)}): {quitados}")
    print(f"Con menos de 10 muestras ({len(pocos)}): {pocos}")
    revisar("sin datos en metavgc (se omiten)", sin_datos)
    revisar("con spreads pero sin movimientos: buscar en Pikalytics y añadir a overrides.movimientos", sin_moves)

# ----------------------------------------------------------------------------- 4. traducir

ROLES_ES = {"Bulky Offensive": "Ofensiva defensiva", "Bulky Attacker": "Atacante defensivo", "Bulky": "Defensiva",
            "Offensive": "Ofensiva", "Trick Room": "Espacio Raro", "Support": "Apoyo", "Fast Support": "Apoyo rápido",
            "Standard": "Estándar"}
FORMAS_ES = (("Alolan ", " de Alola"), ("Galarian ", " de Galar"), ("Hisuian ", " de Hisui"), ("Paldean ", " de Paldea"))

def cmd_traducir(ctx):
    d = leer_json(ctx.json_en)
    if not d:
        sys.exit("No existe el JSON en inglés; ejecuta 'generar' antes.")
    cache_path = os.path.join(ctx.cache, "traducciones_cache.json")
    cache = leer_json(cache_path, {})
    manual = ctx.ov.get("traducciones", {})

    def pokeapi_es(tipo, nombre):
        clave = f"{tipo}/{nombre}"
        if clave not in cache:
            j = http_json(f"{POKEAPI}/{tipo}/{slugify(nombre)}")
            cache[clave] = next((n["name"] for n in (j or {}).get("names", []) if n["language"]["name"] == "es"), None)
        return cache[clave]

    moves, items, abils, nats = set(), set(), set(), set()
    for v in d.values():
        for b in v[0]["builds"].values():
            for m in b["moves"].values():
                moves.update(x for x in m.split(" / ") if x != "-")
            items.add(b["item"]); nats.add(b["nature"])
            a = b["ability"]
            if " (Mega" in a:
                base, mega = a.split(" (Mega")
                abils.add(base)
                if ": " in mega:
                    abils.add(mega.split(": ")[1].rstrip(")"))
            else:
                abils.add(a)
    tareas = [("move", m) for m in moves] + [("item", i) for i in items] + [("ability", a) for a in abils] + [("nature", n) for n in nats]
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda t: pokeapi_es(*t), tareas))
    escribir_json(cache_path, cache, crlf=False)

    sin = {"move": set(), "item": set(), "ability": set(), "nature": set()}
    def tr(tipo, nombre):
        if nombre in manual.get(tipo, {}):
            return manual[tipo][nombre]
        es = cache.get(f"{tipo}/{nombre}")
        if es:
            return es
        sin[tipo].add(nombre)
        return nombre

    def tr_moves(texto):
        return " / ".join(tr("move", x) if x != "-" else "-" for x in texto.split(" / "))

    def tr_ability(a):
        if " (Mega" in a:
            base, mega = a.split(" (Mega")
            if ": " in mega:
                return f"{tr('ability', base)} (Mega: {tr('ability', mega.split(': ')[1].rstrip(')'))})"
            return f"{tr('ability', base)} (Mega)"
        return tr("ability", a)

    def tr_build_name(nombre, item_es):
        sufijo = ""
        m = re.match(r"^(.*) \(([^)]*)\)$", nombre)
        if m:
            nombre, extra = m.groups()
            sufijo = f" ({tr('nature', extra)})" if extra in nats else f" ({extra})"
        mega = re.match(r"^Mega( [XYZ])? (.*)$", nombre)
        if mega:
            r = mega.group(2)
            return f"Mega{mega.group(1) or ''} {ROLES_ES.get(r) or tr('move', r)}{sufijo}"
        for r in sorted(ROLES_ES, key=len, reverse=True):
            if nombre.startswith(r + " "):
                return f"{ROLES_ES[r]} {item_es}{sufijo}"
        for mv in sorted(moves, key=len, reverse=True):
            if nombre.startswith(mv + " "):
                return f"{tr('move', mv)} {item_es}{sufijo}"
        return nombre + sufijo

    nombres_es = ctx.ov.get("roster", {}).get("nombres_es", {})
    def tr_pokemon(n):
        if n in nombres_es:
            return nombres_es[n]
        for pref, suf in FORMAS_ES:
            if n.startswith(pref):
                return n[len(pref):] + suf
        return n.replace("(Female)", "(Hembra)").replace("(Male)", "(Macho)")

    salida = {}
    for k, v in d.items():
        builds = {}
        for num, b in v[0]["builds"].items():
            item_es = tr("item", b["item"])
            builds[num] = {"build_name": tr_build_name(b["build_name"], item_es), "item": item_es,
                           "nature": tr("nature", b["nature"]), "ability": tr_ability(b["ability"]),
                           "moves": {kk: tr_moves(mm) for kk, mm in b["moves"].items()}, "evs": dict(b["evs"])}
        salida[k] = [{"pokemon_name": tr_pokemon(v[0]["pokemon_name"]), "builds": builds}]
    escribir_json(ctx.json_es, salida)
    print(f"Escrito {ctx.json_es}: {len(salida)} Pokémon")
    for t, l in sin.items():
        revisar(f"{t} sin traducción oficial (buscar en WikiDex y añadir a overrides.traducciones.{t})", sorted(l))

# ----------------------------------------------------------------------------- 5. aliases en Main.py

INICIO = "    # --- alias builds-champions (generado; no editar a mano) ---"
FIN = "    # --- fin alias builds-champions ---"

def cmd_aliases(ctx):
    roster = leer_json(ctx.roster_path)["pokemon"]
    d = leer_json(ctx.json_en, {})
    ovr = ctx.ov.get("roster", {})
    alias = {}
    for p in roster:
        if p["key"] not in d:
            continue
        for a in set(p["aliases"]) | alias_de_clave(p["key"], ovr):
            if a != p["key"]:
                alias[a] = p["key"]
    lineas = ["    nombre_pokemon = nombre_pokemon.lower()"]
    lineas += [f'    if nombre_pokemon =="{a}": nombre_pokemon ="{k}"' for a, k in sorted(alias.items())]
    bloque = "\n".join([INICIO] + lineas + [FIN])
    src = open(ctx.main_py, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in src else "\n"
    src = src.replace("\r\n", "\n")
    n = src.count(INICIO)
    if n == 0 or n != src.count(FIN):
        sys.exit(f"Main.py no tiene los marcadores '{INICIO.strip()}' / '{FIN.strip()}' (o están desparejados). "
                 "Colócalos dentro de cada comando, justo antes de usar nombre_pokemon.")
    src = re.sub(re.escape(INICIO) + r".*?" + re.escape(FIN), lambda _: bloque, src, flags=re.S)
    open(ctx.main_py, "w", encoding="utf-8", newline=nl).write(src)
    print(f"Main.py: {n} bloque(s) de alias actualizados con {len(alias)} alias")

# ----------------------------------------------------------------------------- 6. validar

def cmd_validar(ctx):
    errores = []
    for ruta in (ctx.json_en, ctx.json_es):
        d = leer_json(ruta)
        if d is None:
            errores.append(f"falta {ruta}")
            continue
        for k, v in d.items():
            for num, b in v[0].get("builds", {}).items():
                try:
                    evs = [int(b["evs"][s]) for s in STATS]
                    _ = (b["build_name"], b["nature"], b["ability"], b["item"], *[b["moves"][f"move{i}"] for i in range(1, 5)])
                except (KeyError, ValueError) as e:
                    errores.append(f"{os.path.basename(ruta)} {k} build {num}: campo inválido {e}")
                    continue
                if sum(evs) > 66 or max(evs) > 32:
                    errores.append(f"{os.path.basename(ruta)} {k} build {num}: spread inválido {evs}")
                if "tera" in b:
                    errores.append(f"{os.path.basename(ruta)} {k} build {num}: campo tera presente")
    en, es = leer_json(ctx.json_en, {}), leer_json(ctx.json_es, {})
    if list(en) != list(es):
        errores.append("las claves del JSON inglés y español no coinciden")
    def existe(k):
        return k if http_json(f"{POKEAPI}/pokemon/{k}") else None
    with ThreadPoolExecutor(8) as ex:
        ok = set(filter(None, ex.map(existe, en.keys())))
    errores += [f"clave sin sprite en PokeAPI: {k}" for k in en if k not in ok]
    print(f"Validación: {len(en)} Pokémon, {sum(len(v[0]['builds']) for v in en.values())} builds")
    revisar("errores", errores)
    return not errores

# ----------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paso", choices=["roster", "descargar", "generar", "traducir", "aliases", "validar", "todo"])
    ap.add_argument("--bot-dir", default=".", help="carpeta con Main.py y builds__vgc_api.json")
    ap.add_argument("--cache-dir", default=os.path.join(tempfile.gettempdir(), "builds-champions"))
    ap.add_argument("--overrides", default=OVERRIDES_DEF)
    ap.add_argument("--regulacion", help="slug de metavgc, p. ej. regulationm-c (por defecto: la más reciente)")
    args = ap.parse_args()
    ctx = Ctx(args)
    pasos = {"roster": cmd_roster, "descargar": cmd_descargar, "generar": cmd_generar,
             "traducir": cmd_traducir, "aliases": cmd_aliases, "validar": cmd_validar}
    orden = list(pasos) if args.paso == "todo" else [args.paso]
    for p in orden:
        print(f"\n=== {p} ===")
        pasos[p](ctx)

if __name__ == "__main__":
    main()
