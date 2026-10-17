# Formato de CapCut y plan de montaje

## Plan JSON (lo que lee `crear_proyecto.py`)

```json
{
  "nombre": "encargo · A dinámico",
  "lienzo": [1080, 1920],
  "base": "proyecto-con-la-cancion",
  "clips": [
    {"video": "C:/ruta/toma.mp4", "inicio": 1.2, "fin": 3.4, "zoom": 1.0, "llenar": true,
     "velocidad": 1.0, "volumen": 1.0, "x": 0.0, "y": 0.0}
  ],
  "textos": [
    {"texto": "HOLA", "inicio": 0.0, "fin": 1.1, "tam": 9, "color": "#FFFFFF",
     "borde": "#000000", "grosor_borde": 0.08, "x": 0.0, "y": -0.4}
  ]
}
```

- **`base`** (opcional) es el nombre de la carpeta de un proyecto de CapCut. Se copia conservando sus pistas de audio (la música y sus beats) y su biblioteca de medios; el vídeo y los textos se rehacen. Sin `base`, se usa `assets/plantilla-capcut`.
- **Clips**: van seguidos en la pista principal.
  - `inicio` y `fin` son segundos **del vídeo original**.
  - `zoom` se multiplica por la escala base. Con `llenar: true` (por defecto) el vídeo cubre el lienzo recortando lo que sobre; con `false`, se ve entero.
  - `velocidad` 0,5 es cámara lenta y ocupa el doble en la línea de tiempo.
  - `volumen` va de 0 a 1 o más.
  - `x` e `y` desplazan el clip, en unidades de medio lienzo.
- **Textos**:
  - `inicio` y `fin` son segundos **de la línea de tiempo**.
  - `y` va de −1 (abajo) a 1 (arriba); por defecto −0,4.
  - `borde` es un color, o `null` para no ponerlo.
  - Si dos textos se solapan, cada uno va en su propia pista.
- **Nombre**: no puede repetir el de un proyecto que ya exista. Los caracteres `\ / : * ? " < > |` se cambian por `-`.

## Dónde está cada cosa

- **Proyectos**: `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\<nombre>\`.
  - `draft_content.json`: la edición.
  - `draft_meta_info.json`: id, nombre, rutas y la biblioteca de medios.
  - `draft_cover.jpg`: la miniatura.
- **Lista de proyectos**: `root_meta_info.json` (`all_draft_store`), en la misma carpeta. Si un proyecto no está ahí, CapCut no lo muestra. Antes de tocarla, el script guarda una copia en `%TEMP%`.
- **`.locked`** dentro de la carpeta de un proyecto significa que está abierto en CapCut.
- **Música de la biblioteca**: `%LOCALAPPDATA%\CapCut\User Data\Cache\music\`. Ahí están el `.mp3` y su `.beat`, un JSON `{"time": [ms, …]}`.
- **Fuente del sistema**: `%LOCALAPPDATA%\CapCut\Apps\<versión>\Resources\Font\SystemFont\en.ttf`. La ruta cambia con cada versión y el script la busca solo.

## Reglas del formato (comprobadas en CapCut 9.6, octubre de 2026)

- **Tiempos**: en microsegundos.
  - `source_timerange` es el trozo del vídeo original.
  - `target_timerange` es la posición en la línea de tiempo.
  - Duración en la línea de tiempo = duración del trozo / `speed`. Además, el material `speeds` del segmento lleva el mismo valor.
- **Materiales propios de cada segmento**: cada uno tiene `extra_material_refs` a sus propios `speeds`, `canvases`, `placeholder_infos`, `sound_channel_mappings`, `vocal_separations`, `audio_fades`, `material_colors`, `loudnesses` y `material_animations`. Al copiar un segmento, se copian también con ids nuevos.
- **Escala**: 1 = el vídeo entero encajado en el lienzo. Para cubrir un lienzo 9:16 con un vídeo 16:9 hace falta ×3,16.
- **Posición**: `clip.transform` x/y en unidades de medio lienzo; `y` negativo es abajo.
- **Texto**:
  - `content` es un JSON en forma de texto con `text` y `styles`. Cada estilo tiene `range` (contado en UTF-16), `size`, `fill`, `font.path` y `strokes` (el borde).
  - Con borde, se suma 8 a `check_flag` (`check_flag |= 8`).
- **Lienzo vertical**: `canvas_config` 1080×1920 con `ratio: "original"` funciona.
- **Vídeos verticales del iPhone**: ffprobe los da como 1920×1080 con rotación de 90°. CapCut los guarda como 1080×1920 y `comun.info_video` hace el mismo cambio.
- **Al abrir un proyecto**: CapCut lo reescribe en JSON legible (sin cifrar) y conserva lo que entiende. Si algo desaparece tras abrirlo, CapCut no lo ha aceptado.
- **Beats**: los segmentos de audio enlazan materiales `beats`.
  - `ai_beats.beats_path` apunta al `.beat` de la biblioteca.
  - `user_beats` son marcas a mano, en µs. Se suponen relativas al inicio de la canción, pero no está verificado.

## Si CapCut cambia de formato

1. Pide al usuario que cree en CapCut un proyecto con un clip y un texto, que lo guarde y que cierre CapCut.
2. Compáralo con `assets/plantilla-capcut`: claves nuevas, renombradas o que falten. Si `draft_content.json` ya no es JSON legible, CapCut ha empezado a cifrar y esta vía deja de servir. En ese caso, la alternativa es exportar con ffmpeg.
3. Sustituye la plantilla por ese proyecto, quitando rutas y nombres personales porque el repo es público, y prueba con un plan pequeño.
