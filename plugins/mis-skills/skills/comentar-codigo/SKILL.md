---
name: comentar-codigo
description: Añade comentarios breves y explicativos al código existente para que cualquiera entienda qué hace cada parte (funciones, clases, bucles, condicionales, llamadas externas), editando los archivos en sitio sin cambiar la lógica. Usa esta skill siempre que el usuario pida comentar, anotar, explicar o documentar código dentro del propio archivo — frases como "comenta el código", "pon comentarios", "añade notas explicando qué hace cada parte", "explica el código con comentarios", "documenta este archivo", "no entiendo este código, coméntamelo" — aunque no diga la palabra "comentario" y aunque no indique qué archivos. No la uses para escribir documentación externa (README, docstrings de API) ni para explicar código solo en el chat.
---

# Comentar código

El objetivo es que alguien que no escribió el código (o el propio autor dentro de seis meses) pueda leerlo de arriba abajo y entender qué hace cada parte sin tener que descifrarla. Los comentarios son notas breves al margen, no un tutorial: acompañan al código, no lo sustituyen.

## 1. Decidir qué archivos tocar

- Si el usuario nombra archivos, carpetas o un módulo, limita el trabajo a eso.
- Si no concreta nada ("comenta el código"), recorre todo el código fuente del proyecto.

Excluye siempre lo que no es código escrito a mano: dependencias (`node_modules`, `venv`, `.venv`, `vendor`), `.git`, salidas de build (`dist`, `build`, `out`, `target`), archivos minificados o generados (`*.min.js`, `*.generated.*`, `*.lock`, migraciones autogeneradas), y datos o configuración sin lógica (JSON, CSV, imágenes). Comentar esos archivos no aporta nada y puede romper herramientas que los regeneran.

Si el alcance resulta grande (más de ~30 archivos), enumera lo que vas a tocar y confirma con el usuario antes de empezar; es fácil que quisiera solo una parte.

## 2. Leer antes de escribir

Lee cada archivo completo antes de comentarlo, y si una función depende de otras (helpers, modelos, config), échales un vistazo. Un comentario escrito sin contexto suele ser vago ("procesa los datos") o directamente erróneo, y un comentario erróneo es peor que ninguno porque el lector se fía de él.

## 3. Qué comentar

Comenta por bloques, no por líneas. Un buen criterio: cada sitio donde un lector se pararía a preguntarse "¿y esto qué hace?". En la práctica:

- **Funciones, métodos y clases**: una línea encima que diga qué hacen y, si no es obvio, para qué se usan.
- **Bucles**: qué recorren y qué producen ("recorre los pedidos y acumula el total por cliente").
- **Condicionales no triviales**: qué caso distinguen y por qué importa.
- **Llamadas externas**: peticiones HTTP, consultas a base de datos, lectura/escritura de archivos, llamadas a APIs de terceros.
- **Trozos densos**: expresiones regulares, cálculos con fórmulas, manipulación de bits, transformaciones encadenadas.
- **Bloques de configuración o constantes** cuyo significado no se deduce del nombre.

No comentes lo que ya se explica solo: imports evidentes, `i += 1`, getters de una línea, un `return` al final. Tampoco repitas literalmente el código ("incrementa i en 1"): el comentario debe aportar la intención, no traducir la sintaxis.

Densidad orientativa: en una función de 20 líneas caben 2-4 comentarios. Si te sale uno por línea, estás explicando de más; si una función de 60 líneas se queda con uno, probablemente de menos.

## 4. Cómo escribir cada comentario

- **Breve**: una línea, dos como máximo. Si necesitas un párrafo, es señal de que ese trozo merece una función con nombre claro, pero eso no es tarea de esta skill: deja el comentario corto y menciónalo en el resumen final.
- **En español**, salvo que el usuario pida otro idioma o el código ya tenga sus comentarios en otro idioma; en ese caso sigue la convención del archivo para no mezclar.
- **Sintaxis nativa del lenguaje**, en la línea justo encima del bloque y con su misma indentación:
  - `#` → Python, Ruby, Shell, YAML, Perl, R
  - `//` → JavaScript, TypeScript, Java, C, C++, C#, Go, Rust, PHP, Kotlin, Swift, Dart
  - `--` → SQL, Lua, Haskell
  - `<!-- -->` → HTML, XML, Vue/Svelte (parte de plantilla)
  - `/* */` → CSS, SCSS
  - Si el lenguaje no está aquí, usa su sintaxis estándar de comentario de línea.
- Tono neutro y directo, sin emojis, sin "aquí", sin "este código". Empieza por el verbo o por el sustantivo que describe el resultado.

## 5. Respetar lo que ya existe

- Si un bloque ya tiene un comentario, no añadas otro encima; con uno basta.
- No borres ni reescribas comentarios existentes, aunque estén mal. Si uno te parece desactualizado o incorrecto, déjalo y señálalo en el resumen para que el usuario decida.
- Docstrings, JSDoc y anotaciones de tipo cuentan como comentarios existentes: una función con docstring no necesita otra línea encima.

## 6. No tocar el código

Solo se añaden líneas de comentario. Nada de reformatear, renombrar, reordenar imports, corregir bugs o "mejorar de paso" aunque veas algo claramente mejorable: el usuario pidió entender su código, no que cambie. Si ves un bug, apúntalo en el resumen final.

Usa ediciones puntuales (insertar líneas) en vez de reescribir el archivo entero: así preservas codificación, finales de línea, indentación con tabs/espacios y evitas errores de transcripción en partes que no ibas a tocar.

## 7. Resumen final

Al terminar, di al usuario:

- Archivos modificados y cuántos comentarios añadiste en cada uno.
- Archivos que saltaste y por qué (generados, sin lógica, ya bien comentados).
- Observaciones que no eran tu tarea pero conviene saber: posibles bugs, comentarios antiguos que parecen incorrectos, funciones demasiado largas.

## Ejemplos

**Python — antes:**

```python
def cargar_pedidos(ruta):
    with open(ruta) as f:
        filas = csv.DictReader(f)
        pedidos = [p for p in filas if p["estado"] != "cancelado"]
    totales = {}
    for p in pedidos:
        totales[p["cliente"]] = totales.get(p["cliente"], 0) + float(p["importe"])
    return totales
```

**Python — después:**

```python
# Lee un CSV de pedidos y devuelve el importe total por cliente, ignorando los cancelados
def cargar_pedidos(ruta):
    with open(ruta) as f:
        filas = csv.DictReader(f)
        # Descarta los pedidos cancelados antes de sumar
        pedidos = [p for p in filas if p["estado"] != "cancelado"]
    totales = {}
    # Acumula el importe de cada pedido en la entrada de su cliente
    for p in pedidos:
        totales[p["cliente"]] = totales.get(p["cliente"], 0) + float(p["importe"])
    return totales
```

**JavaScript — antes:**

```javascript
async function fetchUser(id) {
  const res = await fetch(`${API}/users/${id}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
```

**JavaScript — después:**

```javascript
// Obtiene un usuario de la API por id; devuelve null si no existe
async function fetchUser(id) {
  const res = await fetch(`${API}/users/${id}`);
  // 404 se trata como "no encontrado", cualquier otro error se propaga
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
```

Fíjate en lo que no se comentó: el `return res.json()` y la construcción de la URL se entienden solos.
