# TikTok hablado

Para vídeos en los que alguien habla a cámara. Quien manda es la voz.

1. **Transcribe cada toma**: `transcribir.py toma.mp4 --palabras "<nombres, marcas, juegos>"`. Antes, pregunta al usuario por los nombres raros: con la pista, Whisper acierta más.
2. **Tramos de voz**: `analizar.py silencios toma.mp4`.
3. **Tomas repetidas**: si dos frases, seguidas o de tomas distintas, dicen casi lo mismo (un 70 % o más de palabras iguales), quédate con la última que esté completa, que suele ser la buena. Si la última está cortada, quédate con la anterior. Quita las frases a medias y las de "espera, otra vez".
4. **Orden y gancho**: respeta el orden de grabación. La primera frase tiene que enganchar en 1–2 s. Si la mejor frase está más adelante, **propón** al usuario ponerla al principio, pero no lo hagas sin preguntar.
5. **Clips**: un clip por cada tramo de voz que se queda, con los márgenes del estilo. Si dos tramos están separados por menos de 0,15 s, únelos para evitar microcortes.
6. **Subtítulos**: sácalos de las palabras de los clips que se quedan, pasadas a tiempo de la línea de tiempo:

   `t_línea = inicio_del_clip_en_la_línea + (t_palabra − inicio_del_clip_en_la_toma) / velocidad`

   Haz los bloques según el estilo, cumpliendo las reglas de subtítulos de [estilos.md](estilos.md): mínimo 1 s, sin huecos, longitud y zona segura. Avisa al usuario de las palabras con `prob` < 0,5 y de los nombres propios para que los revise.
7. **Zoom** según el estilo.
8. **Duración**: la que pida el usuario. Por defecto, quita todo lo que sobra sin recortar contenido.

## Ejemplo de plan (fragmento, estilo A)

```json
{
  "nombre": "2026-10-20-ana · A dinámico",
  "lienzo": [1080, 1920],
  "clips": [
    {"video": "C:/Users/maxlu/Documents/editar-videos/videos/2026-10-20-ana/toma2.mp4", "inicio": 0.42, "fin": 2.9},
    {"video": "C:/Users/maxlu/Documents/editar-videos/videos/2026-10-20-ana/toma2.mp4", "inicio": 3.6, "fin": 6.1, "zoom": 1.18}
  ],
  "textos": [
    {"texto": "HOY OS ENSEÑO", "inicio": 0.0, "fin": 1.1, "tam": 11, "y": -0.2},
    {"texto": "MI TRUCO", "inicio": 1.1, "fin": 2.2, "tam": 11, "y": -0.2}
  ]
}
```
