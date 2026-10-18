# Estilos

Valores pensados para un lienzo de 1080×1920. En el plan, `tam` es el tamaño del texto y `y` la posición vertical: −1 es abajo del todo y 1 arriba del todo.

## Reglas de subtítulos (los dos estilos)

Se cumplen siempre. `crear_proyecto.py` avisa si un texto del plan se salta alguna.

1. **Mínimo 1 s en pantalla.** Si un bloque dura menos porque se habla rápido, júntalo con el siguiente (en A, hasta 4 palabras y 19 caracteres) o alárgalo hasta que empiece el siguiente. Única excepción: una palabra de impacto en A ("¡BOOM!"), con un mínimo de 0,6 s.
2. **Sin huecos en el habla seguida.** Si entre dos subtítulos hay menos de 0,3 s, el primero se queda hasta que sale el siguiente; así no parpadean. En las pausas de verdad (más largas), la pantalla se queda sin texto.
3. **Longitud.** En A, 19 caracteres como mucho por bloque y en una línea. En B, dos líneas de 20 caracteres como mucho. Más largo, cortarlo en dos subtítulos.
4. **Zona segura de TikTok.** La interfaz tapa unas zonas de la pantalla:
   - el 20 % de abajo (descripción y música): el centro del texto no debe bajar de `y` −0,5;
   - el 10 % de arriba (pestañas): no subir de 0,75;
   - la columna de la derecha (me gusta, comentarios, compartir): textos centrados (`x` 0) y líneas cortas, como en la regla 3.

## A · Dinámico

- **Cortes**: fuera todos los silencios de más de 0,3 s y las tomas repetidas. Deja 0,08 s antes y 0,12 s después de cada tramo de voz para no comerse sílabas. Planos de 1–3 s.
- **Subtítulos**: bloques de 2–3 palabras, en MAYÚSCULAS, blancos con borde negro (grosor 0,08), `tam` 11–12 y un poco por debajo del centro (`y` entre −0,15 y −0,25). Cada bloque aparece con sus palabras, respetando las reglas de arriba.
- **Zoom**: alterna 1,0 y 1,15–1,2 cada uno o dos clips, y pon zoom siempre en la frase clave o el remate. Al cambiar el zoom en un corte de la misma toma, el salto se nota menos.
- **Montajes**: un corte en cada beat.

## B · Limpio

- **Cortes**: solo los silencios de más de 0,8 s y las tomas falsas. Márgenes de 0,15 s antes y 0,25 s después.
- **Subtítulos**: frase completa (dos líneas como mucho), con mayúscula solo al principio, blancos con borde y `tam` 8–9. Van en la parte baja pero por encima de la zona tapada, con `y` entre −0,45 y −0,5.
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
