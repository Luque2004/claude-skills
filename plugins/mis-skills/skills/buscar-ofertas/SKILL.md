---
name: buscar-ofertas
description: Busca ofertas de empleo en LinkedIn con la sesión del usuario, las criba leyendo la descripción (años de experiencia, nivel, stack) y presenta solicitudes con "Solicitud sencilla" (Easy Apply) confirmando cada envío. Usa esta skill cuando el usuario pida buscar trabajo, ofertas, prácticas o vacantes en LinkedIn, aplicar/enviar su CV, o diga cosas como "busca ofertas", "envía mi currículum", "aplica a ofertas junior", "qué ofertas hay hoy", aunque no mencione LinkedIn. No la uses para redactar o convertir el CV (eso es aparte) ni para otros portales de empleo.
---

# Buscar ofertas y solicitar en LinkedIn

Flujo en cuatro fases: **configurar → buscar → cribar → solicitar**. El usuario está presente y confirma cada envío; el ritmo es humano (pausas de 2–3 s, máximo ~10 solicitudes por sesión). LinkedIn prohíbe bots y puede restringir cuentas: nunca lo hagas en bucle desatendido.

## 0. Reglas fijas

- Trabaja sobre la sesión de LinkedIn del usuario en el navegador del panel (`mcp__Claude_Browser__*`). Si no está logueado, pídele que inicie sesión él en el panel; nunca introduzcas su contraseña ni resuelvas CAPTCHAs.
- **Cada "Enviar solicitud" requiere un "sí" del usuario** tras mostrarle el resumen (empresa, puesto, CV, respuestas). Excepción: si el usuario autoriza explícitamente un lote de formularios *sin preguntas* (solo contacto + CV), envíalos con la comprobación automática de la sección 4 y reporta al final.
- Preguntas de cribado (años de experiencia, salario, disponibilidad): pregúntalas al usuario, no las inventes. Responder falso a un filtro solo sirve para quemar la candidatura en entrevista.
- Cambios en la cuenta (preferencias de empleo, aptitudes del perfil) solo con permiso explícito.

## 1. Configuración del usuario

Lee `busqueda.json` en la carpeta que indique el usuario (por defecto `~/Documents/BusquedaEmpleo/`). Si no existe, créalo preguntando lo mínimo:

```json
{
  "cv": "CV_ATS.pdf",
  "puestos": ["desarrollador web junior", "frontend junior", "prácticas desarrollador web"],
  "ubicacion": "Barcelona, Cataluña, España",
  "distancia_km": 40,
  "remoto_en": "España",
  "max_anos_experiencia": 1,
  "descartar": ["senior", "lead", "angular", "java ", ".net", "sap", "rust", "golang"],
  "respuestas": { "salario_bruto_anual": "21000", "experiencia_profesional_anos": "0" }
}
```

El registro de solicitudes vive en `solicitudes.csv` (misma carpeta), columnas `fecha,empresa,puesto,modalidad,url,estado`. Créalo si no existe y **no repitas una URL ya registrada**.

## 2. Buscar

Construye las búsquedas por URL, no pulsando menús:

```
https://www.linkedin.com/jobs/search/?keywords=<puesto>&location=<ubicacion>&distance=<km>&f_AL=true&f_TPR=r604800
https://www.linkedin.com/jobs/search/?keywords=<puesto>&location=<remoto_en>&f_WT=2&f_AL=true&f_TPR=r604800
```

- `f_AL=true` = solo Solicitud sencilla · `f_WT=2` = remoto · `f_TPR=r604800` = última semana (`r2592000` = último mes) · `start=25` = página 2.
- **No uses `f_E` (nivel de experiencia)**: muchas empresas no lo rellenan y vacía los resultados. Filtra tú leyendo.
- Lanza una búsqueda por puesto en local y otra en remoto. Si "0 resultados", amplía la fecha antes de cambiar palabras clave.
- Extrae las tarjetas con el snippet **`extraer-lista`** de [references/linkedin-snippets.md](references/linkedin-snippets.md) (hace scroll para que LinkedIn pinte todas y deduplica por `data-occludable-job-id`). Acumula `id | título | empresa | lugar` en memoria; el ID sirve para abrir `https://www.linkedin.com/jobs/view/<id>/`.

## 3. Cribar

1. **Primer corte por título**: descarta lo que contenga términos de `descartar` (Senior, Lead, stacks ajenos). Mantén lo ambiguo ("Full Stack Developer", "Programador web").
2. **Segundo corte leyendo la descripción**: abre cada candidata (lotes de 5 con `browser_batch`, `wait` de 3 s entre ellas) y ejecuta el snippet **`leer-oferta`**. Devuelve los fragmentos con "N años/years" y palabras de nivel (junior, senior, prácticas, intern, graduate). Descarta si piden más de `max_anos_experiencia`, idioma fluido que el usuario no tiene, o stack que no aparece en su CV. Si no dice años, lee el bloque de requisitos (snippet `leer-requisitos`).
3. **Señales de baja calidad**: varias ofertas con la misma plantilla ("We are hiring for one of our clients… Work from Anywhere") sin nombre de empresa ni requisitos son agregadores. Márcalas como *dudosas*; se puede aplicar, pero con expectativas bajas.
4. **Programas formativos** ("programa de talento", "bootcamp", "30 semanas", sin salario) no son empleo: avísalo explícitamente.
5. Guarda el cribado en `ofertas-<fecha>.md` con tres bloques: recomendadas (con el porqué), dudosas, descartadas (con motivo en una línea). Preséntaselo al usuario en tabla y pregunta a cuáles aplicar.

## 4. Solicitar

Para cada oferta aprobada:

1. Abre `jobs/view/<id>/`, pulsa el botón "Solicitud sencilla" (snippet `abrir-easy-apply`).
2. El formulario tiene de 1 a 4 páginas. Inspecciónalo con el snippet **`leer-formulario`**: devuelve el botón activo (`Siguiente` / `Revisar` / `Enviar solicitud`), la página `n/m`, los campos y sus etiquetas.
3. **Página de contacto**: email suele venir; el teléfono a veces está vacío. Los clics por JS no funcionan (React ignora eventos sintéticos): haz clic con el ratón sobre el campo (las coordenadas de `getBoundingClientRect` van ×0.92 respecto al frame de la captura) y escribe con `type`.
4. **Página de CV**: el primero de la lista es el más reciente y queda seleccionado. **Subir un CV nuevo** requiere el diálogo nativo: no hay `<input type=file>` hasta pulsar "Cargar currículum" y el diálogo se abre en la pantalla del usuario, así que pídele que pulse él el botón y elija el archivo. Solo hace falta una vez por sesión: LinkedIn lo guarda.
5. **Preguntas adicionales**: radios Yes/No (haz clic en el texto de la opción), textos, selects. El campo de salario suele ser **numérico puro** (sin guiones ni "€"). Consulta al usuario cualquier dato que no esté en `respuestas` y guárdalo ahí para la próxima.
6. **Página "Revisa tu solicitud"**: extrae el resumen y muéstraselo al usuario. Con su "sí", pulsa `Enviar solicitud`.
7. Confirma con una captura (`scale` 0.4 basta): el modal "Se ha enviado tu solicitud a X" **no aparece en `document.body.innerText`**, así que no lo busques por texto.
8. Añade la fila al CSV.

Envío automático de lote (solo si el usuario lo autorizó): el snippet **`enviar-si-simple`** envía únicamente cuando el botón es `Enviar solicitud` en la primera página, no hay campos extra, el CV seleccionado es el configurado y el teléfono está relleno. En cualquier otro caso se detiene y tú retomas a mano.

## 5. Cerrar la sesión de trabajo

Resume en tabla: enviadas, detenidas y por qué, dudosas. Recuerda al usuario dónde está el seguimiento (LinkedIn → Empleos → Mis empleos → Solicitados) y sugiere el siguiente pase en 2–3 días con `f_TPR=r604800`. Si en las preguntas de cribado salió algo que no está en el CV (una tecnología, un idioma), propón añadirlo.
