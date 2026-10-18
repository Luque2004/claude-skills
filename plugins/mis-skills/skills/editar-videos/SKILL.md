---
name: editar-videos
description: Edita vídeos en CapCut (escritorio) a partir de tomas o clips en bruto y entrega proyectos de CapCut listos para retocar, normalmente en dos versiones de estilo distinto (A dinámica, B limpia). Hace TikToks hablados con subtítulos sincronizados (Whisper), quitando silencios y tomas falsas; montajes de videojuegos (clips de Medal) y de entrenamientos cortados al ritmo de la música (beats de CapCut); y copia el estilo de vídeos de referencia o de proyectos de CapCut ya editados. Usa esta skill cuando el usuario diga que le han pasado vídeos para editar, pida editar o montar un TikTok, un reel, un montaje de gameplay o de gimnasio, subtitular un vídeo, quitar silencios, cortar al ritmo de una canción, copiar el estilo de un vídeo o de un creador, o crear un proyecto de CapCut, aunque no diga "skill". No la uses para grabar la pantalla, editar fotos, publicar en redes ni descargar vídeos de otras personas.
---

# Editar vídeos en CapCut

La skill hace la parte mecánica: cortar, subtitular, encuadrar y sincronizar con la música. El resultado es un **proyecto de CapCut** que el usuario abre y termina con lo creativo: el gancho, el humor, los efectos y el retoque final. No exporta el MP4; lo exporta él desde CapCut cuando le guste.

## 0. Reglas fijas

- **No se toca nada que ya exista.**
  - Los vídeos se **copian** a `Documents\editar-videos\videos\<AAAA-MM-DD>-<encargo>\` y se trabaja con esas copias.
  - `crear_proyecto.py` siempre crea un proyecto nuevo. Nunca edites un `draft_content.json` existente.
- **CapCut tiene que estar cerrado del todo** al crear proyectos, también el icono junto al reloj. Si no, al cerrarse puede pisar la lista de proyectos. El script lo comprueba. Con CapCut abierto, usa solo `--comprobar`.
- **Los vídeos de `videos\` no se mueven ni se borran** mientras se usen los proyectos. CapCut los enlaza por ruta y, si faltan, sale "Media not found".
- **El material de clientes nunca va al repo de skills**, que es público. Fichas de estilo, transcripciones y planes van en la carpeta del encargo.
- **Dos versiones por encargo**, A dinámica y B limpia ([references/estilos.md](references/estilos.md)), para que elija el usuario o su cliente. Si hay vídeo de referencia, una de las dos lo imita.
- **Lo creativo lo decide el usuario**: el texto del reto, los ejercicios y kilos, la canción y el gancho cuando el material no tenga uno claro. Pregunta todo lo que falte en un solo mensaje.
- **Solo se edita material del usuario** o que le hayan pasado para editar. Copiar el estilo de otro creador mirando sus vídeos públicos sí; usar su contenido (clips, música, logo) no.

## 1. Requisitos (compruébalos al empezar)

| Qué | Cómo comprobarlo | Si falta (lo instala el usuario) |
|---|---|---|
| ffmpeg | `ffmpeg -version`. Si no está en el PATH, `comun.py` lo busca en la carpeta de winget | `winget install Gyan.FFmpeg` |
| Whisper (solo si hay voz) | `py -3 -c "import faster_whisper"` | `py -3 -m pip install faster-whisper`. El modelo (1,6 GB) se descarga solo la primera vez |
| CapCut de escritorio | existe `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft` | instalar CapCut |

Usa `py -3` para Python (`python` no está en el PATH). Los scripts están en `scripts/` de esta skill: ejecútalos con la ruta completa.

## 2. Flujo

1. **Encargo.** Averigua:
   - el tipo: TikTok hablado, montaje de juego, montaje de entreno, o vlog/gameplay largo;
   - dónde están los vídeos;
   - la referencia de estilo: vídeos "target" o un proyecto de CapCut ya editado;
   - los textos fijos;
   - en montajes, el proyecto de CapCut con la canción ([references/montajes.md](references/montajes.md)).
2. **Copiar los vídeos** a `Documents\editar-videos\videos\<fecha>-<encargo>\`. Copiarlos, no moverlos.
3. **Sacar el estilo.**
   - **Si la referencia es un proyecto de CapCut**: `resumen_capcut.py <proyecto>`. Es exacto y gasta poco.
   - **Si son MP4**:
     - `analizar.py escenas` para el ritmo de cortes;
     - `analizar.py fotogramas --cada 2` y mira 3–4 capturas: tamaño, posición, color y palabras por línea de los subtítulos, zooms y formato;
     - `transcribir.py` si se habla.

     Las imágenes gastan tokens: pocas capturas y a 540 px.
   - **Sin referencia**: los estilos A y B por defecto.

   Escribe la ficha `estilo.md` en la carpeta del encargo y enséñasela al usuario en 4–6 líneas antes de montar.
4. **Analizar el material** según el tipo: [references/tiktok-hablado.md](references/tiktok-hablado.md) o [references/montajes.md](references/montajes.md).
5. **Planear.** Escribe `plan-A.json` y `plan-B.json` en la carpeta del encargo (formato en [references/capcut-formato.md](references/capcut-formato.md)). Los textos cumplen las reglas de subtítulos de [references/estilos.md](references/estilos.md). Pruébalos con `crear_proyecto.py plan-A.json --comprobar`: avisa si algún texto dura menos de 1 s, cae en la zona que tapa TikTok o tiene líneas demasiado largas. Corrige los avisos antes de crear, salvo las palabras de impacto.
6. **Crear** con CapCut cerrado: `crear_proyecto.py plan-A.json` y lo mismo con B. Nombres: `<encargo> · A dinámico` y `<encargo> · B limpio`.
7. **Entregar.** Para cada versión, di qué hace (duración, cortes, qué se ha quitado) y qué tiene que revisar el usuario: nombres raros en los subtítulos, el gancho y la música. Él exporta desde CapCut. Ajusta según lo que te diga.

## 3. Scripts (`scripts/`)

| Script | Para qué |
|---|---|
| `resumen_capcut.py [proyecto…]` | Estilo de proyectos ya editados: cortes, escalas, textos, música, fondos. Sin nombres, los resume todos |
| `transcribir.py VIDEO [--palabras "…"] [--pista N] [--hasta S]` | Texto con el tiempo de cada palabra. Lo guarda en `<video>.transcripcion.json`. En local, sin internet |
| `analizar.py silencios VIDEO` | Tramos de voz y de silencio (el umbral se adapta solo) |
| `analizar.py volumen VIDEO [--pista N]` | Picos de volumen: disparos, gritos, el drop de una canción |
| `analizar.py movimiento VIDEO` | Tramos con más movimiento: las repeticiones de un entreno |
| `analizar.py escenas VIDEO` | Cortes de un vídeo ya editado y duración media de cada plano |
| `analizar.py fotogramas VIDEO --salida DIR` | Capturas para mirar el estilo |
| `analizar.py beats PROYECTO` | Beats de la música de un proyecto de CapCut, en tiempo de la línea de tiempo, y el bpm |
| `crear_proyecto.py plan.json [--comprobar]` | Proyecto nuevo de CapCut desde un plan |

`comun.py` es compartido (ffmpeg, audio, datos del vídeo). `assets/plantilla-capcut/` es un proyecto vacío guardado por CapCut, que sirve de base.

## 4. Errores conocidos

- **"Media not found" al abrir un proyecto**: el vídeo ya no está en esa ruta. Pasó el 16/10/2026 con un gameplay borrado del Escritorio.
- **`TypeError: metadata_errors` en faster-whisper**: incompatibilidad con PyAV 19. Los scripts leen el audio con ffmpeg; no uses `decode_audio`.
- **Clips de Medal**: traen dos pistas de audio, el juego y el micro. Para la voz usa `--pista` con la del micro; para los picos de acción, la del juego. Averigua cuál es cuál con `analizar.py volumen --pista 0` y `--pista 1`.
- **Whisper se salta las muletillas** ("eh", "mmm"): para cortarlas, cruza la transcripción con `analizar.py silencios` y los huecos entre palabras.
- **Los JSON guardados desde PowerShell llevan BOM**: los scripts lo aceptan.
- **Si una versión nueva de CapCut no abre los proyectos creados**, sigue "Si CapCut cambia de formato" en [references/capcut-formato.md](references/capcut-formato.md).

## 5. Estado (v0.1, 17/10/2026)

- **Probado en CapCut**: proyecto vertical con varios cortes, zoom y subtítulos (demo del 16/10/2026).
- **Probado solo en seco** (`--comprobar`): varios vídeos, cámara lenta, volumen, vídeos verticales del móvil, textos que se solapan (van a otra pista), emojis y proyecto base con música.
- **El primer encargo real sirve de prueba** de todo esto: pide al usuario que lo revise con calma.
- **No se genera** (lo añade el usuario en CapCut): transiciones, efectos, stickers, animaciones de texto, y música sin proyecto base.
