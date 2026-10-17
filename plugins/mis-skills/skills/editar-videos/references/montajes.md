# Montajes con música (videojuegos y entrenamientos)

Aquí manda la música: los cortes caen en los beats. No hace falta Whisper.

## Lo que prepara el usuario

1. En CapCut, crea un proyecto nuevo y pon una canción de la **biblioteca de CapCut** al principio (en el segundo 0). Si quiere, importa también los clips.
2. Guarda y cierra CapCut.

Ese proyecto es la `base` del plan: la música y sus beats se conservan, y el vídeo y los textos se rehacen.

La música de la biblioteca de CapCut tiene dos ventajas: CapCut guarda sus beats en un archivo y TikTok la silencia menos por derechos de autor. Si usa un mp3 propio, tiene que marcar los beats a mano en CapCut.

## Beats y drop

- `analizar.py beats <proyecto>` devuelve los beats en tiempo de la línea de tiempo y el bpm.
- Estilo A: un corte en cada beat. Estilo B: uno cada dos. Si la canción pasa de 140 bpm, uno cada dos en A y uno cada cuatro en B.
- **El drop** es la subida fuerte de la canción. Búscalo con `analizar.py volumen <mp3>`, usando el mp3 de la caché de CapCut (`%LOCALAPPDATA%\CapCut\User Data\Cache\music\`), o pregúntale al usuario en qué segundo está. Ahí va el mejor momento.
- **Duración**: entre 10 y 30 s, terminando en un beat. Si la canción sigue, el usuario la recorta en CapCut con un fundido.

## Videojuegos (clips de Medal)

- **Momento fuerte de cada clip**: `analizar.py volumen clip.mp4 --pista <la del juego>`. Los picos son disparos y kills. Coge el trozo que acaba unos 0,3 s después del pico.
- **Orden**: el mejor clip primero (el gancho, 1–2 s), luego de menos a más, y el mejor de todos en el drop.
- **Encuadre vertical**: `llenar` recorta el centro (×3,16 para un vídeo 16:9). Si la acción no está en el centro (HUD, minimapa), propón para B `"llenar": false`, que enseña la imagen entera con fondo negro.
- **Pico de la mejor jugada**: zoom de 1,2 en A y cámara lenta (`"velocidad": 0.5`) en B.
- **Textos**: los que dicte el usuario ("1v4", "ACE").

## Entrenamientos

- **Tramo activo de cada clip**: `analizar.py movimiento clip.mp4`. Los picos son las repeticiones. Descarta el principio (colocar el móvil) y el final (soltar la barra).
- **Ritmo**: una o dos repeticiones por beat. La más dura, a cámara lenta en el drop.
- **Textos**: los que dicte el usuario ("Press banca · 80 kg", "PR").
- Los vídeos verticales del móvil ya llenan el lienzo (escala 1). Los horizontales se recortan igual que los gameplays.
