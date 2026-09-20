---
name: builds-champions
description: Actualiza los archivos de builds de Pokémon Champions del bot de Discord (builds__vgc_api.json en inglés y builds__vgc_api_es.json en español) a la regulación vigente, añadiendo los Pokémon nuevos del roster, quitando los que dejan de ser legales y regenerando los alias de Main.py. Usa esta skill cuando el usuario pida actualizar/regenerar las builds, adaptar el bot a una regulación nueva (Reg M-D, M-E…), añadir los Pokémon nuevos de Champions, traducir las builds al español, o diga cosas como "actualiza las builds", "ha salido regulación nueva", "mete los pokémon nuevos", "regenera el json del bot". No la uses para builds de Escarlata/Púrpura ni para otros juegos.
---

# Actualizar builds de Pokémon Champions

Un script hace el trabajo pesado; tu tarea es **ejecutarlo por pasos, revisar lo que marque como `REVISAR:` y resolverlo** editando `overrides.json`. Explica al usuario en español qué haces en cada paso.

## Recursos de la skill

- `scripts/builds_champions.py` — pipeline con subcomandos `roster → descargar → generar → traducir → aliases → validar` (o `todo`).
- `overrides.json` — excepciones editables (sinónimos de nombres, claves PokeAPI, movimientos sin datos, habilidades Mega, traducciones). **Es el único sitio donde se corrigen cosas a mano**; el script nunca se edita para un caso puntual.

## Cómo funciona (para explicárselo al usuario)

| Dato | Fuente | Notas |
|---|---|---|
| Regulación vigente y roster legal | `metavgc.com/regulations` (la última listada) | metavgc lista especies; las formas regionales (`-alola/-galar/-hisui/-paldea`) se descubren vía PokeAPI y se incluyen si tienen uso |
| Builds (naturaleza + spread, objeto, habilidad, movimientos) | Página de cada Pokémon en metavgc (datos de torneos) | Spreads en **Stat Points** de Champions (0-32, máx. 66); sin `tera` (no existe en Champions) |
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
   - `con spreads pero sin movimientos` → metavgc devuelve el learnset a 0 %. Busca los movimientos en Pikalytics (`https://www.pikalytics.com/pokedex/<formato-vigente>/<slug>`) y añádelos a `movimientos` en `overrides.json` como `[["Movimiento", %], ...]` (mínimo 4). Si tampoco hay datos, deja que se omita y dilo. **No inventes sets.**
   - Si aparece una especie con varias megapiedras (X/Y/Z) nueva, añade su habilidad Mega en `habilidad_piedra`.
   Repite `generar` tras cada cambio en overrides.

5. **Traducir** (`traducir`): escribe el JSON en español con la **misma estructura y las mismas claves** (el bot puede leerlo tal cual). `REVISAR: sin traducción oficial` → busca el nombre en WikiDex (`wikidex.net/wiki/<Nombre>`), añádelo a `traducciones.<tipo>` y repite. Usa nombres de España (PokeAPI no distingue Latinoamérica).

6. **Alias** (`aliases`): regenera los bloques de `Main.py` entre `# --- alias builds-champions ... ---` y `# --- fin alias builds-champions ---` (hay uno por comando). Si el script dice que faltan los marcadores, colócalos tú dentro de cada comando justo antes de usar `nombre_pokemon`, sin borrar los alias manuales del usuario. Los alias ingleses de formas regionales salen solos (`alolan-ninetales`; en español se escribe como la clave, `ninetales-alola`); los de otras formas (`indeedee-hembra`, `lycanroc-diurno`, `toxtricity-aguda`…) se mantienen en `overrides.json` → `roster.alias_extra`, y basta ejecutar `aliases` tras editarlo (no hace falta repetir `roster`). Comprueba que compila: `py -m py_compile Main.py`.

7. **Validar** (`validar`): simula la lectura del bot sobre ambos JSON y comprueba que cada clave existe en PokeAPI. No des por terminado el trabajo con errores aquí.

8. **Informe** al usuario: regulación, totales (Pokémon y builds), lista de nuevos y quitados, omitidos y por qué, Pokémon con <10 muestras (builds poco fiables), y qué se añadió a `overrides.json`. Recuerda que el bot lee el JSON desde **GitHub Pages** (`luque2004.github.io/pokemon_api/`): hasta que suba los archivos allí, Discord seguirá mostrando la versión antigua. No hagas commit ni push salvo que lo pida.

## Limitaciones conocidas

- Depende de la estructura interna de metavgc (Next.js flight data: `initialDetails`, `pokemon-grid`). Si un paso deja de encontrar datos, lo primero es descargar una página con `curl` y comprobar si cambió el formato; avisa al usuario en vez de improvisar.
- Las builds son agregados estadísticos (spread más usado + objeto más usado + movimientos más usados), no sets publicados por jugadores concretos.
- Si cambias `overrides.json` o el script, **sube la versión del plugin** (`plugin.json` y `marketplace.json`) o la caché instalada no se actualizará.
