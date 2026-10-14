---
name: builds-champions-rea
description: Variante experimental de builds-champions que actualiza las builds de Pokémon Champions del bot de Discord (builds__vgc_api.json y builds__vgc_api_es.json) y, cuando metavgc trae los movimientos al 0 %, los calcula de los equipos de torneo de la propia página en vez de pedirlos a Pikalytics; si metavgc cambia de formato, diagnostica con REA. Úsala SOLO cuando el usuario la pida por su nombre o diga cosas como "usa la versión REA de las builds", "builds con la versión nueva", "builds-champions-rea", o quiera comparar las dos versiones. Para "actualiza las builds" sin más, usa builds-champions. No la uses para builds de Escarlata/Púrpura ni para otros juegos.
---

# Actualizar builds de Pokémon Champions (variante REA)

Un script hace el trabajo pesado; tu tarea es **ejecutarlo por pasos, revisar lo que marque como `REVISAR:` y resolverlo** editando `overrides.json`. Explica al usuario en español qué haces en cada paso.

Es una copia de `builds-champions` (plugin `mis-skills`) con una mejora descubierta investigando metavgc con REA. Las dos conviven para compararlas; escriben en los mismos archivos del bot, así que usa solo una por actualización.

## Qué cambia respecto a builds-champions

| | builds-champions | builds-champions-rea |
|---|---|---|
| Movimientos al 0 % en metavgc | `REVISAR` → buscarlos a mano en Pikalytics | Se calculan solos con los equipos de torneo que trae la misma página (`initialDetails.teams`); `REVISAR` avisa de que es una muestra pequeña |
| Habilidades de otra forma (metavgc copia las de la forma normal en algunas regionales) | No lo detecta: Ninetales de Alola sale con Drought | Las compara con PokeAPI; si ninguna es de esa forma, las corrige con los equipos de la página (Snow Warning) o, si no hay, no genera build |
| `overrides.json` → `movimientos` | Trae Maushold puesto a mano | Vacío: solo para lo que tampoco salga de los equipos |
| `overrides.json` → `habilidades` | No existe | Habilidad fija por clave, para formas sin equipos con los que corregirla |
| Si metavgc cambia de formato | Descargar una página con `curl` | Diagnosticar con REA (ver abajo), o `curl` si REA no está instalado |

El script **no necesita REA** para funcionar; REA solo se usa para diagnosticar.

## Recursos de la skill

- `scripts/builds_champions.py` — pipeline con subcomandos `roster → descargar → generar → traducir → aliases → validar` (o `todo`).
- `overrides.json` — excepciones editables (sinónimos de nombres, claves PokeAPI, movimientos sin datos, habilidades Mega, traducciones). **Es el único sitio donde se corrigen cosas a mano**; el script nunca se edita para un caso puntual.

## Cómo funciona (para explicárselo al usuario)

| Dato | Fuente | Notas |
|---|---|---|
| Regulación vigente y roster legal | `metavgc.com/regulations` (la última listada) | metavgc lista especies; las formas regionales (`-alola/-galar/-hisui/-paldea`) se descubren vía PokeAPI y se incluyen si tienen uso |
| Builds (naturaleza + spread, objeto, habilidad, movimientos) | Página de cada Pokémon en metavgc (datos de torneos) | Spreads en **Stat Points** de Champions (0-32, máx. 66); sin `tera` (no existe en Champions) |
| Movimientos cuando metavgc los da al 0 % | Equipos de torneo incluidos en esa misma página | Mismo slug o, si no aparece, otra forma que **no** sea entrada propia del roster (Maushold Familia de Cuatro sale como `maushold-family-of-three`) |
| Comprobación de habilidades | PokeAPI `/pokemon/<clave>` (caché en `habilidades_pokeapi.json`) | Si metavgc da habilidades de otra forma, se corrigen con los equipos de la página, **solo con el slug exacto** (nunca otras formas) |
| Clave del Pokémon en el JSON | Nombre de PokeAPI (`arcanine-hisui`, `basculegion-male`) | Obligatorio: el bot pide el sprite a PokeAPI con esa clave |
| Traducción al español | PokeAPI (`names` en `es`) + `overrides.traducciones` | Megapiedras y habilidades nuevas se verifican en WikiDex |

Reglas de generación: 1-3 builds por Pokémon según muestras (<30 → 1, <200 → 2, resto 3), combinando spreads y objetos con ≥10 % de uso; top 4 movimientos con alternativa en el tercero si el quinto supera el 6 %; sin Protect con objetos Choice/Assault Vest; habilidad de Mega anotada como `Base (Mega: X)`. Los Pokémon se ordenan por uso.

## Flujo

1. **Localiza la carpeta del bot** (contiene `Main.py` y `builds__vgc_api.json`; la habitual es `C:\Users\maxlu\Documents\discord-bot\bot_0`). Haz una copia de seguridad de los dos JSON en el scratchpad antes de tocar nada.

2. **Roster**
   ```bash
   py <ruta-skill>/scripts/builds_champions.py roster --bot-dir "<carpeta-bot>"
   ```
   Confirma que la regulación detectada es la vigente (si dudas, compruébalo con una búsqueda web: "Pokémon Champions regulation" + fecha). Si el usuario quiere otra, pásala con `--regulacion regulationm-x`.
   `REVISAR: nombres sin clave PokeAPI` → decide si es un sinónimo raro de metavgc (`roster.sinonimos`, p. ej. `"Patrat": "Watchog"`) o una forma con clave distinta en PokeAPI (`roster.claves`, p. ej. `"Floette": "floette-eternal"`). Repite el paso.

3. **Descargar** (`descargar`): ~250 páginas en paralelo, un minuto aprox. Si falla alguna, repite el paso.

4. **Generar** (`generar`): escribe el JSON en inglés y muestra **nuevos / quitados** respecto al archivo anterior; esa lista es la parte principal del informe al usuario.
   - `sin datos en metavgc` → Pokémon legales sin ninguna partida registrada. Se omiten; dilo en el informe.
   - `habilidades de otra forma en metavgc, corregidas con los equipos de su página` → informativo. Dilo en el informe (p. ej. Ninetales de Alola: Drought → Snow Warning).
   - `habilidades de otra forma en metavgc y sin equipos para corregirlas` → se omiten. Si la página no tiene ni equipos con esa forma, lo normal es que **toda** la página sea de la forma normal (Farfetch'd y Mr. Mime de Galar tienen las mismas muestras que los normales), así que no los rellenes: déjalos omitidos y dilo. Usa `overrides.habilidades` solo si compruebas que el resto de datos sí son de esa forma.
   - `movimientos al 0 % en metavgc, calculados de los equipos de su página` → informativo. Dilo en el informe con el número de sets usados y comprueba que los movimientos encajan con el Pokémon.
   - `sin movimientos ni en los equipos de su página` → busca los movimientos en Pikalytics (`https://www.pikalytics.com/pokedex/<formato-vigente>/<slug>`) y añádelos a `movimientos` en `overrides.json` como `[["Movimiento", %], ...]` (mínimo 4). Si tampoco hay datos, deja que se omita y dilo. **No inventes sets.**
   - Si aparece una especie con varias megapiedras (X/Y/Z) nueva, añade su habilidad Mega en `habilidad_piedra`.
   Repite `generar` tras cada cambio en overrides.

5. **Traducir** (`traducir`): escribe el JSON en español con la **misma estructura y las mismas claves** (el bot puede leerlo tal cual). `REVISAR: sin traducción oficial` → busca el nombre en WikiDex (`wikidex.net/wiki/<Nombre>`), añádelo a `traducciones.<tipo>` y repite. Usa nombres de España (PokeAPI no distingue Latinoamérica).

6. **Alias** (`aliases`): regenera los bloques de `Main.py` entre `# --- alias builds-champions ... ---` y `# --- fin alias builds-champions ---` (hay uno por comando; son los mismos marcadores que usa builds-champions). Si el script dice que faltan los marcadores, colócalos tú dentro de cada comando justo antes de usar `nombre_pokemon`, sin borrar los alias manuales del usuario. Los alias ingleses de formas regionales salen solos (`alolan-ninetales`; en español se escribe como la clave, `ninetales-alola`); los de otras formas (`indeedee-hembra`, `lycanroc-diurno`, `toxtricity-aguda`…) se mantienen en `overrides.json` → `roster.alias_extra`, y basta ejecutar `aliases` tras editarlo (no hace falta repetir `roster`). Comprueba que compila: `py -m py_compile Main.py`.

7. **Validar** (`validar`): simula la lectura del bot sobre ambos JSON y comprueba que cada clave existe en PokeAPI. No des por terminado el trabajo con errores aquí.

8. **Informe** al usuario: regulación, totales (Pokémon y builds), lista de nuevos y quitados, omitidos y por qué, Pokémon con <10 muestras (builds poco fiables), habilidades corregidas, movimientos calculados de equipos, y qué se añadió a `overrides.json`. Recuerda que el bot lee el JSON desde **GitHub Pages** (`luque2004.github.io/pokemon_api/`): hasta que suba los archivos allí, Discord seguirá mostrando la versión antigua. No hagas commit ni push salvo que lo pida.

## Comparar con builds-champions

Para ver qué cambia entre las dos versiones sin tocar el bot:

1. Copia `builds__vgc_api.json` del bot a dos carpetas del scratchpad (`ab/bot_orig` y `ab/bot_rea`).
2. Ejecuta `roster` y `descargar` una sola vez con `--cache-dir <scratchpad>/ab/cache` (las dos versiones descargan igual).
3. Ejecuta `generar` con cada script (el de `mis-skills` y este), cada uno con su `--bot-dir` y el mismo `--cache-dir`.
4. Compara los dos JSON entrada por entrada y enseña al usuario solo las diferencias.

Comparativas (Reg M-C, mismos datos):
- 13/10/2026, v0.1.0: 446 builds idénticas salvo Maushold (Familia de Cuatro). La original tenía Follow Me / Population Bomb / Super Fang / Protect (Pikalytics, a mano); esta saca Follow Me / Population Bomb / Taunt / Feint / Protect de 10 equipos de metavgc.
- 14/10/2026, v0.2.0: además, Ninetales de Alola pasa de Drought (error de metavgc, la del Ninetales normal) a Snow Warning, sacada de 9 equipos. Farfetch'd y Mr. Mime de Galar siguen omitidos, ahora por el motivo correcto (su página es la de la forma normal).

## Diagnóstico con REA si metavgc cambia

Úsalo cuando un paso deje de encontrar datos (`initialDetails`, `pokemon-grid`) y estén disponibles las herramientas `mcp__rea__*` (instalación: README del repo, "Herramientas externas"):

1. Abre un Chrome aparte con perfil vacío y depuración solo en local, en la página que falla:
   `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --user-data-dir="<scratchpad>\rea-chrome" --no-first-run https://metavgc.com/pokemon/<slug>`
2. `list_browser_targets` (endpoint `http://127.0.0.1:9222`) para obtener el `target_id`, y `analyze_web_bundle` para ver framework, scripts y `fetch` que hace la página.
3. Compara con lo esperado: Next.js con los datos del Pokémon dentro del HTML (`self.__next_f.push`), sin `fetch` de datos de builds.
4. Cierra solo ese Chrome (los procesos cuya línea de comandos contiene `rea-chrome`) y explica al usuario qué ha cambiado antes de tocar el script.

Sin REA, descarga una página con `curl` y busca a mano `initialDetails`.

## Limitaciones conocidas

- Depende de la estructura interna de metavgc (Next.js flight data: `initialDetails`, `pokemon-grid`, `teams`).
- metavgc **no tiene API pública de builds**: los únicos `fetch` del navegador son de login, notificaciones y foro, y su `robots.txt` prohíbe `/api/` a cualquier programa. No uses `/api/` aunque aparezca en el código de la web; usa solo las páginas (`/regulations`, `/pokemon/<slug>`).
- En algunas formas regionales metavgc copia las habilidades (y a veces la página entera) de la forma normal, con los mismos porcentajes: Ninetales de Alola (solo habilidades), Farfetch'd y Mr. Mime de Galar (todo). La comprobación con PokeAPI lo detecta; si aparece un caso nuevo, compara `rawCount` y habilidades con la página de la forma normal.
- Un mismo Pokémon puede tener varios nombres en metavgc: Maushold es `maushold-family-of-four` en la URL (y `/pokemon/maushold` redirige ahí), `maushold-four` como slug interno y `maushold-family-of-three` dentro de los equipos.
- Los movimientos calculados de equipos salen de unos 10 sets: sirven para no dejar al Pokémon sin build, pero son menos fiables que la estadística completa.
- Las builds son agregados estadísticos (spread más usado + objeto más usado + movimientos más usados), no sets publicados por jugadores concretos.
- Si cambias `overrides.json` o el script, **sube la versión de este plugin** (`plugins/builds-champions-rea/.claude-plugin/plugin.json` y su entrada en `.claude-plugin/marketplace.json`) o la caché instalada no se actualizará.
