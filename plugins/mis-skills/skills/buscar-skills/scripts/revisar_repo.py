# Escanea una skill, un plugin o un servidor MCP descargado ANTES de instalarlo. Solo lee archivos:
# no ejecuta, importa ni instala nada de la carpeta revisada. No decide si es seguro: dice qué leer.
# Informe: inventario por tipo, lo que se ejecuta solo (hooks, MCP, postinstall), código opaco
# (candidato a REA), patrones de riesgo con archivo:línea, dominios y caracteres invisibles.
# Uso: py -3 -I revisar_repo.py CARPETA [--max N]   (N = líneas por categoría, 15 por defecto)
import json, os, re, sys, unicodedata
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CODIGO = {".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".jsx", ".tsx", ".py", ".sh", ".bash", ".zsh",
          ".ps1", ".psm1", ".bat", ".cmd", ".vbs", ".rb", ".pl", ".php", ".lua", ".go", ".rs"}
BINARIO = {".exe", ".dll", ".so", ".dylib", ".node", ".wasm", ".bin", ".jar", ".class", ".pyc", ".msi",
           ".dmg", ".pkg", ".appimage", ".apk", ".com", ".scr"}
COMPRIMIDO = {".zip", ".tar", ".gz", ".tgz", ".7z", ".rar", ".xz", ".bz2", ".asar"}
MEDIOS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".ico", ".bmp", ".mp4", ".mov", ".webm",
          ".mp3", ".wav", ".ogg", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".pdf"}
CONFIG_AUTO = {"hooks.json", ".mcp.json", "plugin.json", "marketplace.json", "settings.json",
               "settings.local.json", "package.json", "setup.py", "pyproject.toml"}
MAX_BYTES = 2_000_000  # más grande que esto no se escanea línea a línea (se avisa)

# Patrones de riesgo en código y configuración: (categoría, expresión)
PATRONES = [
    ("ejecuta procesos", r"child_process|\bspawn(Sync)?\s*\(|\bexec(Sync|File)?\s*\(|subprocess|os\.system|Popen|"
                         r"Invoke-Expression|\biex\b|Start-Process|ShellExecute|WScript\.Shell"),
    ("evalúa código", r"\beval\s*\(|new Function\s*\(|__import__\s*\(|\bcompile\s*\(|vm\.run"),
    ("red", r"\bfetch\s*\(|https?\.(get|request)\s*\(|axios|XMLHttpRequest|WebSocket|requests\.(get|post)|"
            r"urllib|\bcurl\b|\bwget\b|Invoke-WebRequest|Invoke-RestMethod|\biwr\b|net\.connect|socket\."),
    ("datos sensibles", r"\.ssh|id_rsa|id_ed25519|\.aws|\.npmrc|\.git-credentials|\.env\b|credential|password|"
                        r"passwd|secret|api[_-]?key|\btoken\b|cookie|keychain|Login Data|Local State|wallet"),
    ("entorno y perfil", r"process\.env|os\.environ|getenv|homedir\s*\(|expanduser|USERPROFILE|APPDATA|\$HOME\b"),
    ("escribe o borra", r"writeFile|appendFile|createWriteStream|\bunlink|rmSync|rmdir|\brm -r|shutil\.(rmtree|move)|"
                        r"os\.remove|Remove-Item|\bdel /|Set-ItemProperty|reg add"),
    ("ofuscación", r"\batob\s*\(|fromCharCode|b64decode|FromBase64String|Buffer\.from\([^)]*base64|"
                   r"[A-Za-z0-9+/]{200,}={0,2}|(\\x[0-9a-fA-F]{2}){12,}"),
]
# Frases sospechosas en texto que leerá el modelo (SKILL.md, referencias)
PATRONES_TEXTO = [
    ("órdenes al agente", r"ignor(e|a)\s+(all|any|previous|prior|the above|las|todas|lo anterior)|"
                          r"do not (tell|inform|mention)|without (asking|telling)|no (se lo digas|avises)|sin preguntar"),
    ("instala o ejecuta", r"curl[^\n|]*\|\s*(ba|z)?sh|wget[^\n|]*\|\s*(ba)?sh|iwr[^\n|]*\|\s*iex|irm[^\n|]*\|\s*iex|"
                          r"npm (i|install) -g|--dangerously|bypass|--yes\b|\s-y\b"),
    ("datos sensibles", r"\.ssh|id_rsa|\.aws/|\.env\b|api[_-]?key|password|contraseña|cookie"),
]
INVISIBLES = re.compile("[​-‏‪-‮⁠-⁤⁦-⁩﻿\U000e0000-\U000e007f]")
URL = re.compile(r"https?://([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def invisible_sospechoso(linea):
    # la unión invisible (U+200D) entre dos símbolos forma emojis compuestos (👩🏽‍💻): eso es legítimo
    for m in INVISIBLES.finditer(linea):
        i, c = m.start(), m.group()
        if c == "‍" and 0 < i < len(linea) - 1 and all(
                unicodedata.category(linea[j]) in {"So", "Sk"} for j in (i - 1, i + 1)):
            continue
        return True
    return False


def es_binario(ruta):
    with open(ruta, "rb") as f:
        return b"\0" in f.read(8192)


def leer(ruta):
    with open(ruta, "rb") as f:
        return f.read().decode("utf-8", errors="replace")


def minificado(texto, nombre):
    # una línea larga suelta (un texto, una tabla) no cuenta: hace falta que todo el archivo sea denso
    lineas = texto.splitlines() or [""]
    larga = max(len(l) for l in lineas)
    return ".min." in nombre or larga > 5000 or (len(texto) > 5000 and len(texto) / len(lineas) > 250)


def revisar(raiz, maximo):
    tipos = Counter()
    auto, opaco, grandes = [], [], []
    avisos = defaultdict(list)
    dominios, dominios_datos = Counter(), Counter()  # en código/configuración vs. solo en textos y datos
    invisibles = []

    for carpeta, subcarpetas, archivos in os.walk(raiz):
        subcarpetas[:] = [d for d in subcarpetas if d != ".git"]
        for nombre in archivos:
            ruta = os.path.join(carpeta, nombre)
            rel = os.path.relpath(ruta, raiz).replace("\\", "/")
            ext = os.path.splitext(nombre)[1].lower()
            if os.path.islink(ruta):
                tipos["enlaces simbólicos"] += 1
                opaco.append(f"{rel}  (enlace simbólico a {os.readlink(ruta)})")
                continue
            tamaño = os.path.getsize(ruta)

            # clasificar el archivo
            if ext in MEDIOS:
                tipos["imágenes, fuentes y medios"] += 1
                continue
            if ext in COMPRIMIDO:
                tipos["comprimidos"] += 1
                opaco.append(f"{rel}  (comprimido: no se puede revisar sin extraerlo)")
                continue
            if ext in BINARIO or es_binario(ruta):
                tipos["binarios"] += 1
                opaco.append(f"{rel}  (binario, {tamaño:,} bytes)")
                continue
            if tamaño > MAX_BYTES:
                tipos["texto grande sin escanear"] += 1
                grandes.append(f"{rel}  ({tamaño:,} bytes)")
                continue

            texto = leer(ruta)
            es_codigo = ext in CODIGO or texto.startswith("#!")
            es_md = ext in {".md", ".mdx", ".txt"}
            tipos["código" if es_codigo else "markdown y texto" if es_md else "datos y configuración"] += 1
            if es_codigo and minificado(texto, nombre):
                opaco.append(f"{rel}  (código minificado o empaquetado)")

            # lo que se ejecuta solo: hooks, servidores MCP, scripts de instalación
            if nombre in CONFIG_AUTO or "/hooks/" in f"/{rel}":
                if nombre == "package.json":
                    try:
                        scripts = json.loads(texto).get("scripts", {})
                    except ValueError:
                        scripts = {}
                    for clave in ("preinstall", "install", "postinstall", "prepare", "prepublish"):
                        if clave in scripts:
                            auto.append(f"{rel}: script \"{clave}\" → {scripts[clave]}")
                elif nombre in {"setup.py", "pyproject.toml"}:
                    auto.append(f"{rel}: instalador de Python (se ejecuta al instalar con pip)")
                elif re.search(r'"(hooks|mcpServers|command)"\s*:', texto) or nombre in {"hooks.json", ".mcp.json"}:
                    auto.append(f"{rel}: declara hooks, servidores MCP o comandos")

            # patrones línea a línea
            for n, linea in enumerate(texto.splitlines(), 1):
                for dom in URL.findall(linea):
                    (dominios if es_codigo or nombre in CONFIG_AUTO else dominios_datos)[dom.lower()] += 1
                if invisible_sospechoso(linea):
                    invisibles.append(f"{rel}:{n}")
                if es_codigo or nombre in CONFIG_AUTO:
                    lista = PATRONES
                elif es_md:
                    lista = PATRONES_TEXTO
                else:
                    continue
                for categoria, patron in lista:
                    if re.search(patron, linea, re.IGNORECASE):
                        avisos[categoria].append(f"{rel}:{n}: {linea.strip()[:140]}")

    # informe
    print(f"Revisión de: {os.path.abspath(raiz)}")
    print("\n## Inventario")
    for tipo, n in tipos.most_common():
        print(f"- {tipo}: {n}")

    print("\n## Se ejecuta solo (máxima atención: leer entero)")
    print("\n".join(f"- {a}" for a in auto) or "- nada")

    print("\n## Código opaco (no se puede leer: nivel 3 con REA o no se instala)")
    print("\n".join(f"- {o}" for o in opaco) or "- nada")
    if grandes:
        print("\n## Texto demasiado grande para escanear (mirar a mano si no son datos)")
        print("\n".join(f"- {g}" for g in grandes))

    print("\n## Patrones de riesgo (señalan qué leer; no son una condena)")
    if not avisos:
        print("- ninguno")
    for categoria, lineas in avisos.items():
        print(f"\n### {categoria} ({len(lineas)})")
        for l in lineas[:maximo]:
            print(f"- {l}")
        if len(lineas) > maximo:
            print(f"- … y {len(lineas) - maximo} más")

    print("\n## Dominios en el código y la configuración (a dónde puede conectarse)")
    print("\n".join(f"- {d} ({n})" for d, n in dominios.most_common(30)) or "- ninguno")
    if dominios_datos:
        print(f"\n## Dominios solo en textos y datos ({len(dominios_datos)} distintos; los más citados)")
        print("\n".join(f"- {d} ({n})" for d, n in dominios_datos.most_common(10)))

    print("\n## Caracteres invisibles")
    print("\n".join(f"- {i}" for i in invisibles[:maximo]) or "- ninguno")

    hay_codigo = tipos["código"] > 0
    nivel = 3 if opaco else 2 if (hay_codigo or auto) else 1
    print(f"\n## Nivel de revisión necesario: {nivel}")
    print({1: "Solo texto: leer los SKILL.md enteros.",
           2: "Hay código o cosas que se ejecutan solas: leer todo lo marcado arriba.",
           3: "Hay código opaco: REA (si la procedencia es fiable) o no instalar esa parte."}[nivel])


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in {"-h", "--help"}:
        print(__doc__ or "Uso: py -3 -I revisar_repo.py CARPETA [--max N]")
        sys.exit(0)
    maximo = int(args[args.index("--max") + 1]) if "--max" in args else 15
    if not os.path.isdir(args[0]):
        sys.exit(f"No existe la carpeta: {args[0]}")
    revisar(args[0], maximo)
