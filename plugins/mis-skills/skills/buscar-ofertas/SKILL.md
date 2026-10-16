---
name: buscar-ofertas
description: Busca ofertas de empleo en LinkedIn (y en InfoJobs) con la sesión del usuario, las criba leyendo la descripción (años de experiencia, nivel, estudios, stack) y presenta solicitudes con "Solicitud sencilla" (Easy Apply) o inscripción en InfoJobs confirmando cada envío. Usa esta skill cuando el usuario pida buscar trabajo, ofertas, prácticas o vacantes en LinkedIn o InfoJobs, aplicar/enviar su CV, revisar sus alertas de empleo, completar su perfil de InfoJobs, o diga cosas como "busca ofertas", "envía mi currículum", "aplica a ofertas junior", "qué ofertas hay hoy", aunque no mencione el portal. No la uses para redactar o convertir el CV en PDF/DOCX (eso es aparte) ni para portales distintos de LinkedIn e InfoJobs.
---

# Buscar ofertas y solicitar en LinkedIn e InfoJobs

Flujo en cuatro fases: **configurar → buscar → cribar → solicitar**. El usuario está presente y confirma cada envío; el ritmo es humano (pausas de 2–3 s, máximo ~10 solicitudes por sesión). LinkedIn e InfoJobs prohíben bots y pueden restringir cuentas: nunca lo hagas en bucle desatendido.

Las secciones 1-5 describen LinkedIn. InfoJobs tiene su propia guía en [references/infojobs.md](references/infojobs.md) (búsqueda por URL, cribado por los campos fijos de la ficha, completar el CV del portal, alertas, inscripción con cuestionario y carta hasta el botón de confirmar); los criterios de `busqueda.json`, el registro `solicitudes.csv` y las reglas fijas son los mismos.

Las fases 1-3 (buscar y cribar) son de solo lectura y pueden ir en segundo plano con un subagente mientras el usuario hace otra cosa; la fase 4 (solicitar) no, porque necesita al usuario delante.

## 0. Reglas fijas

- Trabaja sobre la sesión de LinkedIn del usuario en el navegador del panel (`mcp__Claude_Browser__*`). Si no está logueado, pídele que inicie sesión él en el panel; nunca introduzcas su contraseña ni resuelvas CAPTCHAs. Si su sesión está en otro navegador, el panel sale sin sesión: compruébalo antes de lanzar las búsquedas. **El panel no conserva la sesión de un día para otro**: cuenta con pedir el login al empezar cada pase. En el aviso de cookies, pulsa "Rechazar" (opción que menos datos cede).
- **Si aparece un CAPTCHA o "actividad poco habitual"**, para: no lo resuelvas, pídele al usuario que lo haga él y no sigas automatizando ese portal en esa sesión (lo que quede, que lo haga él a mano). Es la señal previa a una restricción de cuenta.
- No abras en el panel enlaces que descargan archivos (PDF de certificados, CV): lanzan un diálogo de guardado en la pantalla del usuario. Para leerlos usa `WebFetch` (guarda el binario y luego `Read` del PDF).
- **Un "sí" por pase, un clic final por oferta.** Presenta la tabla numerada del cribado y deja que el usuario elija en un solo mensaje ("sí a todas", "sí a 1, 3 y 5"). Ese "sí" cubre preparar esas solicitudes concretas (abrir, rellenar, responder con datos confirmados, pegar la carta), no otras que salgan después ni pases futuros. El envío final (**Enviar solicitud** en LinkedIn, **CONFIRMA TU INSCRIPCIÓN** en InfoJobs) lo pulsa el usuario en cada una.
- Preguntas de cribado (años de experiencia, salario, disponibilidad, idiomas, niveles, preguntas abiertas): pregúntalas al usuario, no las inventes, y **espera a que confirme cada respuesta de forma explícita** antes de escribirla (un "a" a otra pregunta no vale como confirmación). Responder falso a un filtro solo sirve para quemar la candidatura en entrevista. Las que ya estén en `respuestas` se reutilizan sin volver a preguntar.
- **Reparto de clics que funciona**: tú abres la oferta, rellenas contacto, CV y las respuestas confirmadas; el usuario pulsa **Revisar → Enviar solicitud** en el panel. El sistema de permisos bloquea `Enviar solicitud` siempre y a veces también `Revisar` (08/10/2026), aunque el usuario haya dicho "aplica a todas": no intentes rodearlo; deja el formulario en la última página que puedas y pídeselo a él.
- **El panel del navegador puede cerrarse solo** (pasó el 08/10/2026 con el usuario fuera): los formularios a medio rellenar se pierden. Si el usuario se va, haz búsqueda y cribado, y deja la preparación de formularios para cuando vuelva.
- Cambios en la cuenta (preferencias de empleo, aptitudes del perfil) solo con permiso explícito.

## 1. Configuración del usuario

Lee `busqueda.json` en la carpeta que indique el usuario (por defecto `~/Documents/BusquedaEmpleo/`). Si no existe, créalo preguntando lo mínimo:

```json
{
  "cv": "CV_ATS.pdf",
  "puestos": ["desarrollador web junior", "frontend junior", "prácticas programación"],
  "ubicacion": "Barcelona, Cataluña, España",
  "distancia_km": 40,
  "remoto_en": "España",
  "max_anos_experiencia": 1,
  "descartar": ["senior", "lead", "angular", "java ", ".net", "sap", "rust", "golang"],
  "respuestas": {
    "salario_bruto_anual": "21000", "experiencia_profesional_anos": "0", "disponibilidad_dias": "0",
    "telefono": "600000000", "estudios_oficiales": "ESO", "formacion": "Curso X, 700 h (no reglado)",
    "matriculado": "no", "carne_conducir": "no", "hibrido": "sí",
    "grado_universitario": "no", "nivel_programacion": "...", "nivel_python": "...",
    "git": "...", "ia": "..."
  },
  "respuestas_abiertas": {
    "formacion": "...", "tecnologias_y_proyectos": "...", "tecnologia_desconocida": "..."
  },
  "ultimo_pase": "2026-01-01"
}
```

`telefono` evita buscarlo cada vez (LinkedIn no lo recuerda entre solicitudes). `estudios_oficiales`, `formacion` y `matriculado` sirven para el cribado de la sección 3: si no están, pregúntalos la primera vez que una oferta pida estudios mínimos o sea de prácticas. Los niveles (`nivel_programacion`, `nivel_python`, `git`, `ia`) y `respuestas_abiertas` salen de los cuestionarios de InfoJobs: guárdalos solo cuando el usuario los confirme, con su texto literal, y reutilízalos (adaptando la longitud) en los siguientes.

En la misma carpeta:

- `solicitudes.csv`: registro, columnas `fecha,empresa,puesto,modalidad,url,estado`. Créalo si no existe y **no repitas una URL ya registrada**.
- `cartas.md`: carta base del usuario y las variantes ya usadas. Para una oferta nueva, parte de la base y cambia solo el primer párrafo (por qué esa oferta) y lo que encaje del stack; no afirmes nada que el usuario no haya confirmado (Node.js, Power BI, disponibilidad para viajar…).
- `ofertas-<fecha>.md`: cribados anteriores. **Antes de buscar**, saca los IDs ya vistos para no releerlos: `grep -ohE '[0-9]{10}' ofertas-*.md` (LinkedIn) y `grep -ohE 'of-i[0-9a-f]{30}' ofertas-*.md` (InfoJobs).

Al terminar el pase, actualiza `ultimo_pase`.

### Seguimiento al empezar cada pase

Antes de buscar nada nuevo, mira si hay respuestas: LinkedIn → Empleos → Mis empleos → Solicitados (probablemente `https://www.linkedin.com/my-items/saved-jobs/?cardType=APPLIED`; sin verificar, compruébalo la primera vez y corrige esta línea), con el estado de cada solicitud e InfoJobs → "Mis ofertas" (estado del proceso, "CV leído"). Enséñale al usuario lo que haya cambiado desde el último pase y anótalo en la columna `estado` del CSV. Recuérdale también las **fechas límite** pendientes que quedaron en el último `ofertas-<fecha>.md` (candidaturas por email).

## 2. Buscar

LinkedIn cambió la búsqueda en septiembre de 2026: ahora es `/jobs/search-results/` (la antigua `/jobs/search/` redirige). Construye las búsquedas por URL:

```
Local:  https://www.linkedin.com/jobs/search-results/?keywords=<puesto>&f_TPR=r604800&f_AL=true
Remoto: https://www.linkedin.com/jobs/search-results/?keywords=<puesto>&geoId=105646813&f_TPR=r604800&f_AL=true&f_SAL=f_SA_id_225001%3A272001
```

- **Parámetros que respeta**: `keywords`, `f_AL=true` (solo Solicitud sencilla), `f_TPR` (`r604800` = 1 semana, `r1209600` = 2 semanas, `r2592000` = 1 mes; ajústalo a los días desde `ultimo_pase`), `start=25` (página 2) y `geoId` (`105646813` = España).
- **Parámetros que ignora**: `location` y `distance` (usa la ubicación y el radio del perfil del usuario, p. ej. "Hospitalet de Llobregat (80 km)") y `f_WT=2`. Filtra tú la distancia leyendo el lugar de cada tarjeta.
- **Remoto**: el filtro "En remoto" de la página genera `f_SAL=f_SA_id_225001%3A272001` (el nombre despista, pero es remoto). Comprueba que se aplicó con `document.querySelector('input[aria-label="Filtrar por En remoto"]:checked')`. Si deja de funcionar, carga la búsqueda con `geoId`, localiza con `find` "En remoto" y haz clic por `ref` en el **label** (no en el checkbox). Trampa: la página 2 en remoto mezcla ofertas presenciales; quédate con las que ponen "(En remoto)" en el lugar.
- **No uses `f_E` (nivel de experiencia)**: muchas empresas no lo rellenan y vacía los resultados. Filtra tú leyendo.
- Lanza una búsqueda por puesto en local y otra en remoto. Si "0 resultados", amplía la fecha antes de cambiar palabras clave ("prácticas desarrollador web" da 0 con `f_AL=true`; "prácticas programación" sí da).
- Extrae las tarjetas con el snippet **`extraer-lista`** de [references/linkedin-snippets.md](references/linkedin-snippets.md): hace scroll, saca el ID de las props de React y marca `[rel]` (resultados "relacionados", flojos) y `[noEA]` (sin Solicitud sencilla). Acumula `id | título | empresa | lugar` y deduplica por ID **y** por empresa+título (el mismo anuncio sale a veces con dos IDs). El ID sirve para abrir `https://www.linkedin.com/jobs/view/<id>/`.

## 3. Cribar

1. **Primer corte por título**: descarta lo que contenga términos de `descartar` (Senior, Lead, stacks ajenos). Mantén lo ambiguo ("Full Stack Developer", "Programador web").
2. **Segundo corte leyendo la descripción**: abre cada candidata en lotes de 5 con `browser_batch`, con esta secuencia por oferta: `navigate` → `wait` 3 s → `screenshot` con `scale: 0.1` → snippet **`leer-oferta`**. La captura no es opcional: con el panel oculto, la descripción no se carga hasta que algo obliga a pintar la página (sin ella, 4 de cada 5 salen vacías). Si la captura da *timeout*, ejecuta el snippet igualmente: suele haber disparado ya la carga.
   `leer-oferta` devuelve modalidad, años, nivel, idiomas, salario, tecnologías y el bloque de requisitos. Descarta si piden más de `max_anos_experiencia`, idioma fluido que el usuario no tiene, o stack que no aparece en su CV. Ojo: los "Requisitos añadidos por el anunciante" (p. ej. "Más de 2 años en X") son los filtros automáticos del formulario, y las ofertas en catalán dicen "anys".
3. **Señales de baja calidad**: varias ofertas con la misma plantilla ("We are hiring for one of our clients… Work from Anywhere") sin nombre de empresa ni requisitos son agregadores (Hire Feed, Hired, Quik Hire, Jobgether…). Márcalas como *dudosas*; se puede aplicar, pero con expectativas bajas.
4. **Programas formativos** ("programa de talento", "bootcamp", "30 semanas", sin salario) no son empleo: avísalo explícitamente.
5. **Prácticas que exigen matrícula**: "Intern", "becario/a", "university internship", "Pursuing a Bachelor's/Master's", "estudiante de últimos cursos", "convenio", "remuneración según convenio universitario": solo valen si `matriculado` es "sí" (hace falta un centro que firme el convenio). Si no lo está, descarta las becas genéricas, pero las que encajen bien de stack ponlas en un bloque aparte **"Prácticas con convenio: preguntar al centro"** (el centro donde estudió puede firmar convenios); si no sabes si está matriculado, pregúntalo.
6. **Estudios mínimos** (en InfoJobs es un campo fijo; en LinkedIn va en el texto): compáralos con `estudios_oficiales`. Un curso o bootcamp privado no equivale a un CFGS ni a un certificado de profesionalidad: si piden CFGS y el usuario no lo tiene, marca la oferta como *dudosa* (muchas empresas lo pasan por alto si el stack encaja), no la descartes.
7. **Candidatura fuera del portal**: si la descripción dice "envía tu CV a <email>", "send a short note to…", "no se tendrán en cuenta candidaturas que no se envíen al correo indicado", la Solicitud sencilla no cuenta. Anota el email, el asunto que pidan y la **fecha límite**, y prepara el correo en el `ofertas-<fecha>.md` para que lo envíe el usuario desde su cuenta (tú no envías correos).
8. Guarda el cribado en `ofertas-<fecha>.md` con estos bloques: recomendadas (con el porqué), dudosas, prácticas con convenio, por email (con fecha límite) y descartadas (con motivo en una línea). Preséntaselo al usuario en una **tabla numerada** y pídele que elija en un solo mensaje ("sí a 1, 3 y 5"). Si una recomendada exige algo que no sabes si el usuario cumple (un idioma "imprescindible"), pregúntaselo en ese mismo mensaje.

## 4. Solicitar

### 4.0 Primero, todas las preguntas de golpe

Antes de rellenar nada, recorre los formularios de **todas** las ofertas aprobadas y apunta sus preguntas:

- LinkedIn: abre la Solicitud sencilla, escribe el teléfono (dato confirmado) para poder pasar de página y avanza con `Siguiente` leyendo cada página con `leer-formulario`, hasta llegar a `Revisar`. Cierra el diálogo sin enviar.
- InfoJobs: el cuestionario completo aparece de una vez en la página de inscripción (ver [references/infojobs.md](references/infojobs.md)).

Quita las que ya tienen respuesta en `respuestas` / `respuestas_abiertas` y hazle al usuario **todas las nuevas en un solo mensaje**, numeradas por oferta, con tu propuesta al lado sacada de su CV (él confirma o corrige). Guarda las confirmadas en `busqueda.json` antes de seguir. Así el usuario contesta una vez y el resto del pase no depende de él hasta los clics finales.

### 4.1 Rellenar cada oferta aprobada

1. Abre `jobs/view/<id>/`, pulsa el botón "Solicitud sencilla" (snippet `abrir-easy-apply`).
2. El formulario tiene de 1 a 4 páginas. Inspecciónalo con el snippet **`leer-formulario`**: devuelve el botón activo (`Siguiente` / `Revisar` / `Enviar solicitud`), la página `n/m`, los campos y sus etiquetas. `Siguiente` se puede pulsar por JS.
3. **Página de contacto**: el email viene relleno; el **teléfono no se guarda entre solicitudes**, así que casi siempre hay que escribirlo. Los clics por JS en campos no funcionan (React ignora eventos sintéticos): haz clic con el ratón y escribe con `type`. Coordenadas con el snippet **`coordenadas`** (multiplica por `800 / innerWidth`, no por un factor fijo). No te fíes de la posición visual en la captura: con el panel oculto se pinta reducida y no coincide con el frame de clics. Comprueba después que `input[type=tel]` tiene el valor.
4. **Página de CV**: el primero de la lista es el más reciente y queda seleccionado; comprueba su fecha. **Subir un CV nuevo** requiere el diálogo nativo: no hay `<input type=file>` hasta pulsar "Cargar currículum" y el diálogo se abre en la pantalla del usuario, así que pídele que pulse él el botón y elija el archivo. Solo hace falta una vez: LinkedIn lo guarda para las siguientes.
5. **Preguntas adicionales**, con las respuestas ya confirmadas por el usuario:
   - Radios Yes/No: la primera opción es "Yes". Haz clic con el ratón en su label (`coordenadas` en modo radios); tras el clic LinkedIn cambia los `id`, así que verifica por posición.
   - Selects (nivel de idioma…): `find` "combobox" y `form_input` con el `ref` y el texto de la opción.
   - Textos: salario y años suelen ser **numéricos puros** (sin guiones ni "€"); "disponibilidad (en días)" también.
   Guarda en `respuestas` cualquier dato nuevo que dé el usuario para la próxima.
6. **Dejarlo listo para el clic final**: lleva el formulario hasta la última página que te deje el sistema de permisos (`Revisar` por JS a veces funciona y a veces se bloquea; `Enviar solicitud` siempre se bloquea). Prepara **cada oferta en su propia pestaña** (`tabs_create`, luego `navigate`/`computer` con su `tabId`; cada pestaña necesita su propia captura antes de clicar por coordenadas) y, al terminar, pon delante la primera con `tabs_select`. Dale al usuario una tabla `pestaña | oferta | qué pulsar` para que haga los clics seguidos.
7. **Comprobar y registrar tú solo**: cuando el usuario diga que ha terminado (o pregunte "¿ya está?"), abre de nuevo cada `jobs/view/<id>/` (con la captura de `scale: 0.1`) y mira en `main` si pone "Solicitud enviada" / "Solicitado" y ya no aparece "Solicitud sencilla". Las pestañas pueden estar cerradas: no lo interpretes como "no enviada", recarga la oferta. Añade al CSV solo las confirmadas (en `estado`, las respuestas relevantes: salario, años, grado…) y dile cuáles faltan.

El snippet **`enviar-si-simple`** (envío de formularios de una página sin preguntas) queda solo para entornos donde el sistema de permisos lo permita y el usuario haya aprobado esas ofertas concretas; en este entorno el clic en `Enviar solicitud` se bloquea siempre, así que no cuentes con él.

## 5. Cerrar la sesión de trabajo

Resume en tabla: enviadas, pendientes del clic del usuario, detenidas y por qué, dudosas, y las **fechas límite** de las candidaturas por email. Actualiza el bloque "Estado" del `CLAUDE.md` de la carpeta si existe. Recuerda al usuario dónde está el seguimiento (LinkedIn → Empleos → Mis empleos → Solicitados; InfoJobs → "Mis ofertas", que además avisa cuando la empresa lee el CV) y sugiere el siguiente pase en 2–3 días con `f_TPR=r604800`. Si en las preguntas de cribado salió algo que no está en el CV (una tecnología, un idioma), propón añadirlo. Si el usuario dijo algo incorrecto con consecuencias (p. ej. sobre darse de alta como autónomo para una oferta freelance), corrígelo con datos y sugiere consultarlo con una gestoría.
