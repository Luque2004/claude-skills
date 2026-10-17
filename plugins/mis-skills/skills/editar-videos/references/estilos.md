# Estilos

Valores pensados para un lienzo de 1080×1920. En el plan, `tam` es el tamaño del texto y `y` la posición vertical: −1 es abajo del todo y 1 arriba del todo.

## A · Dinámico

- **Cortes**: fuera todos los silencios de más de 0,3 s y las tomas repetidas. Deja 0,08 s antes y 0,12 s después de cada tramo de voz para no comerse sílabas. Planos de 1–3 s.
- **Subtítulos**: bloques de 2–3 palabras (máximo unos 14 caracteres), en MAYÚSCULAS, blancos con borde negro (grosor 0,08), `tam` 11–12 y un poco por debajo del centro (`y` entre −0,15 y −0,25). Cada bloque aparece y desaparece con sus palabras.
- **Zoom**: alterna 1,0 y 1,15–1,2 cada uno o dos clips, y pon zoom siempre en la frase clave o el remate. Al cambiar el zoom en un corte de la misma toma, el salto se nota menos.
- **Montajes**: un corte en cada beat.

## B · Limpio

- **Cortes**: solo los silencios de más de 0,8 s y las tomas falsas. Márgenes de 0,15 s antes y 0,25 s después.
- **Subtítulos**: frase completa (hasta unos 40 caracteres, dos líneas como mucho), con mayúscula solo al principio, blancos con borde y `tam` 8–9. Van abajo, con `y` entre −0,55 y −0,6. No bajes de −0,65: la interfaz de TikTok tapa el 15 % inferior.
- **Zoom**: ninguno, o uno suave (1,08) en el gancho.
- **Montajes**: un corte cada dos beats y cámara lenta (0,5) en el momento fuerte.

## Ficha de estilo a partir de referencias (`estilo.md` del encargo)

Mide en los vídeos de referencia y traduce cada cosa a parámetros del plan:

- formato y duración total;
- plano medio y cortes por segundo (`analizar.py escenas`);
- subtítulos: tamaño relativo a la pantalla, posición, color, borde, palabras por bloque y si van en mayúsculas;
- zoom: cuántas veces y cuánto;
- textos fijos (título, llamada a la acción) y si hay música y a qué volumen.

Termina la ficha con una línea por versión: "A = …" y "B = …".

## Estilos propios del usuario (proyectos de su PC, febrero de 2026)

Sirven para vlogs y gameplays largos cuando no haya otra referencia.

- **Vlogs** (horizontales, 1920×1080):
  - Clips del iPhone casi sin cortar: cada plano dura de media entre 19 y 29 s.
  - Los clips verticales van a ×1,78 sobre fondo de color, así que quedan franjas a los lados.
  - Superpuestos pequeños de memes, a escala 0,4–0,65.
  - Música sin copyright con fundidos.
  - Un texto blanco de unos 13 s con un "Like porque…" de broma, y remates en texto negro con borde ("Mentira").
- **Gameplays** (grabados con Medal):
  - Intro con una imagen, el texto del reto ("En el día de hoy… Reto: …") y voz en off.
  - Stickers de memes.
  - La partida casi entera.
  - Final con "Continuará…" y música épica.
- **Texto**: fuente del sistema de CapCut (`en.ttf`), tamaño 15 en lienzo horizontal, blanco y sin borde.
