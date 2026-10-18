# claude-skills

Marketplace personal de plugins para [Claude Code](https://docs.claude.com/en/docs/claude-code). Contiene el plugin `mis-skills`, con todas mis skills, para instalarlas en cualquier dispositivo con dos comandos, y el plugin experimental `builds-champions-rea`.

## Instalar en un dispositivo nuevo

```bash
claude plugin marketplace add Luque2004/claude-skills
claude plugin install mis-skills@claude-skills
```

Opcional, la variante experimental de las builds (convive con `builds-champions`):

```bash
claude plugin install builds-champions-rea@claude-skills
```

Abre una sesión nueva de Claude Code y las skills estarán disponibles.

### Herramientas externas (no forman parte del plugin)

Son de terceros: no se copian a este repo, se instalan con su propio comando.

| Herramienta | Para qué | Instalar |
|---|---|---|
| [REA](https://github.com/morluto/rea) | Ingeniería inversa de webs, apps JavaScript/Electron y .NET (servidor MCP + skill `reverse-engineer-anything`). Requiere Node.js 24.11+ y Chrome. | `npx rea-agents@6.4.0 setup` → marcar solo **Claude Code** (con Espacio) → skill: **Yes** → revisar el plan → aplicar → reiniciar Claude Code |
| ffmpeg | Cortar vídeo, analizar audio e imagen y sacar fotogramas (skill `editar-videos`). | `winget install Gyan.FFmpeg` |
| faster-whisper | Transcribir la voz en local para los subtítulos (skill `editar-videos`). El modelo (1,6 GB) se descarga solo la primera vez. | `py -3 -m pip install faster-whisper` |
| CapCut de escritorio | Donde se abren y se terminan los proyectos que crea `editar-videos`. | desde capcut.com |

Instalar REA solo desde el comando de npm o desde `morluto/rea`: hay clones falsos con "instaladores".

### Skills de terceros (instaladas a mano)

Revisadas con `buscar-skills` y copiadas a `~/.claude/skills/<carpeta>/` desde el commit indicado. Cada carpeta lleva un `ORIGEN.md`. No se actualizan solas: para reinstalarlas o actualizarlas, pídeselo a `buscar-skills` ("reinstala las skills de terceros del README").

| Carpeta | Para qué | Repositorio · carpeta · commit |
|---|---|---|
| `taste-skill` | Crear: dirección de arte para webs que no parezcan hechas por IA. Ejecuta scripts de Node 22+ y usa Chrome headless con perfil temporal. | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) · `skills/taste-skill` · `f624f37` |
| `emil-design-eng` | Pulir: hover, transiciones y detalles de interfaz. | [emilkowalski/skills](https://github.com/emilkowalski/skills) · `skills/emil-design-eng` · `2d22863` |
| `find-animation-opportunities` | Pulir: dónde merece la pena animar y dónde no. | ídem · `skills/find-animation-opportunities` · `2d22863` |
| `break-ui` | Probar: la interfaz con los peores datos realistas. | ídem · `skills/break-ui` · `2d22863` |
| `mobile-native` | Probar: fallos que solo salen en un móvil de verdad. | ídem · `skills/mobile-native` · `2d22863` |
| `web-design-guidelines` | Revisar: accesibilidad, foco y formularios antes de entregar. Descarga las reglas de Vercel en cada uso. | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) · `skills/web-design-guidelines` · `063bee9` |

## Skills incluidas

| Skill | Qué hace | Cómo invocarla |
|---|---|---|
| `comentar-codigo` | Añade comentarios breves en español encima de cada bloque (funciones, bucles, condicionales…) sin tocar la lógica. Respeta comentarios existentes y avisa de bugs que vea. | "comenta el código", "coméntame `src/api.js`", "no entiendo este script, explícamelo con comentarios" |
| `buscar-ofertas` | Busca ofertas en LinkedIn (y en InfoJobs) con tu sesión, las criba leyendo la descripción (años de experiencia, nivel, stack) y prepara las solicitudes ("Solicitud sencilla" o inscripción en InfoJobs con cuestionario y carta): eliges las ofertas con un solo "sí", te pregunta de golpe lo que no sepa y tú solo pulsas el envío final de cada una. Empieza cada pase revisando respuestas y fechas límite. Lee tus criterios de `busqueda.json`, tus cartas de `cartas.md` y lleva el registro en `solicitudes.csv` (fuera del repo, en tu carpeta personal, p. ej. `Documentos\BusquedaEmpleo`). | "busca ofertas junior de web", "aplica a las que encajen", "qué ofertas nuevas hay esta semana" |
| `builds-champions` | Actualiza las builds de Pokémon Champions del bot de Discord a la regulación vigente: detecta la regulación en metavgc, añade los Pokémon nuevos del roster, quita los que dejan de ser legales, regenera el JSON en inglés y en español y los alias de `Main.py`. Las excepciones se editan en `overrides.json`. | "actualiza las builds", "ha salido regulación nueva", "mete los pokémon nuevos de champions" |
| `editar-videos` | Edita vídeos en CapCut a partir de tomas o clips en bruto y deja dos proyectos de CapCut para elegir (A dinámico, B limpio). Hace TikToks hablados con subtítulos sincronizados (Whisper), sin silencios ni tomas falsas, y montajes de videojuegos (clips de Medal) o entrenos cortados a los beats de la música de CapCut. Copia el estilo de vídeos de referencia o de proyectos ya editados. Trabaja con copias en `Documentos\editar-videos\videos` (fuera del repo) y nunca toca proyectos que ya existan. | "me han pasado vídeos para editar", "hazme un montaje de gym con esta canción", "subtitula este TikTok" |
| `buscar-skills` | Busca skills, plugins y servidores MCP en el catálogo de Anthropic, GitHub, skills.sh y directorios MCP; las compara por función con lo que ya tienes (una por función) y revisa su código antes de instalar: un escáner propio (`revisar_repo.py`: hooks, código opaco, red, credenciales, caracteres invisibles) y, si traen binarios o JS empaquetado, REA en modo estático. Instala a mano con el commit fijado y un `ORIGEN.md`; nunca `npx skills add` ni `curl \| bash`. | "busca una skill para…", "he visto la skill X, ¿merece la pena?", "¿es segura esta skill?" |
| `builds-champions-rea` *(plugin aparte)* | Copia experimental de `builds-champions`: cuando metavgc da los movimientos al 0 % o las habilidades de otra forma (Ninetales de Alola con Drought), los corrige con los equipos de torneo de la propia página, y si metavgc cambia de formato lo diagnostica con REA. Solo se activa si la pides por su nombre. | "actualiza las builds con la versión REA", "compara las dos versiones de las builds" |

## Actualizar en un dispositivo ya instalado

```bash
claude plugin marketplace update claude-skills
claude plugin update mis-skills@claude-skills
claude plugin update builds-champions-rea@claude-skills
```

## Añadir una skill nueva

1. Crea `plugins/mis-skills/skills/<nombre-de-la-skill>/SKILL.md`.
2. El `SKILL.md` empieza con frontmatter YAML (`name`, `description`) y después las instrucciones en Markdown.
3. Sube la versión en `plugins/mis-skills/.claude-plugin/plugin.json` y en `.claude-plugin/marketplace.json`.
4. `git commit` + `git push`, y actualiza el plugin en cada dispositivo.

## Estructura

```
.claude-plugin/marketplace.json        # catálogo de plugins del repo
plugins/mis-skills/
  .claude-plugin/plugin.json           # manifiesto del plugin
  skills/
    <skill>/SKILL.md                   # una carpeta por skill
plugins/builds-champions-rea/          # plugin experimental, con su propia versión
  .claude-plugin/plugin.json
  skills/builds-champions-rea/
```
