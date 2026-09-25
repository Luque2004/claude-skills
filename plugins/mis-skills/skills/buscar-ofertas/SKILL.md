---
name: buscar-ofertas
description: Busca ofertas de empleo en LinkedIn con la sesión del usuario, las criba leyendo la descripción (años de experiencia, nivel, stack) y presenta solicitudes con "Solicitud sencilla" (Easy Apply) confirmando cada envío. Usa esta skill cuando el usuario pida buscar trabajo, ofertas, prácticas o vacantes en LinkedIn, aplicar/enviar su CV, o diga cosas como "busca ofertas", "envía mi currículum", "aplica a ofertas junior", "qué ofertas hay hoy", aunque no mencione LinkedIn. No la uses para redactar o convertir el CV (eso es aparte) ni para otros portales de empleo.
---

# Buscar ofertas y solicitar en LinkedIn

Flujo en cuatro fases: **configurar → buscar → cribar → solicitar**. El usuario está presente y confirma cada envío; el ritmo es humano (pausas de 2–3 s, máximo ~10 solicitudes por sesión). LinkedIn prohíbe bots y puede restringir cuentas: nunca lo hagas en bucle desatendido.

Las fases 1-3 (buscar y cribar) son de solo lectura y pueden ir en segundo plano con un subagente mientras el usuario hace otra cosa; la fase 4 (solicitar) no, porque necesita al usuario delante.

## 0. Reglas fijas

- Trabaja sobre la sesión de LinkedIn del usuario en el navegador del panel (`mcp__Claude_Browser__*`). Si no está logueado, pídele que inicie sesión él en el panel; nunca introduzcas su contraseña ni resuelvas CAPTCHAs. Si su sesión está en otro navegador, el panel sale sin sesión: compruébalo antes de lanzar las búsquedas.
- **Cada "Enviar solicitud" requiere un "sí" del usuario** tras mostrarle el resumen (empresa, puesto, CV, respuestas). Excepción: si el usuario autoriza explícitamente un lote de formularios *sin preguntas* (solo contacto + CV), envíalos con la comprobación automática de la sección 4 y reporta al final.
- Preguntas de cribado (años de experiencia, salario, disponibilidad, idiomas, freelance): pregúntalas al usuario, no las inventes, y **espera a que confirme cada respuesta de forma explícita** antes de escribirla (un "a" a otra pregunta no vale como confirmación). Responder falso a un filtro solo sirve para quemar la candidatura en entrevista.
- **Reparto de clics que funciona**: tú abres la oferta, rellenas contacto, CV y las respuestas confirmadas; el usuario pulsa **Revisar → Enviar solicitud** en el panel. El sistema de permisos suele bloquear esos dos botones aunque el usuario haya dicho "aplica a todas": no intentes rodearlo, pídeselo a él.
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
  "respuestas": { "salario_bruto_anual": "21000", "experiencia_profesional_anos": "0", "disponibilidad_dias": "0" },
  "ultimo_pase": "2026-01-01"
}
```

El registro de solicitudes vive en `solicitudes.csv` (misma carpeta), columnas `fecha,empresa,puesto,modalidad,url,estado`. Créalo si no existe y **no repitas una URL ya registrada**. Al terminar el pase, actualiza `ultimo_pase`.

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
5. Guarda el cribado en `ofertas-<fecha>.md` con tres bloques: recomendadas (con el porqué), dudosas, descartadas (con motivo en una línea). Preséntaselo al usuario en tabla y pregunta a cuáles aplicar. Si una recomendada exige algo que no sabes si el usuario cumple (un idioma "imprescindible"), pregúntaselo antes.

## 4. Solicitar

Para cada oferta aprobada:

1. Abre `jobs/view/<id>/`, pulsa el botón "Solicitud sencilla" (snippet `abrir-easy-apply`).
2. El formulario tiene de 1 a 4 páginas. Inspecciónalo con el snippet **`leer-formulario`**: devuelve el botón activo (`Siguiente` / `Revisar` / `Enviar solicitud`), la página `n/m`, los campos y sus etiquetas. `Siguiente` se puede pulsar por JS.
3. **Página de contacto**: el email viene relleno; el **teléfono no se guarda entre solicitudes**, así que casi siempre hay que escribirlo. Los clics por JS en campos no funcionan (React ignora eventos sintéticos): haz clic con el ratón y escribe con `type`. Coordenadas con el snippet **`coordenadas`** (multiplica por `800 / innerWidth`, no por un factor fijo). No te fíes de la posición visual en la captura: con el panel oculto se pinta reducida y no coincide con el frame de clics. Comprueba después que `input[type=tel]` tiene el valor.
4. **Página de CV**: el primero de la lista es el más reciente y queda seleccionado; comprueba su fecha. **Subir un CV nuevo** requiere el diálogo nativo: no hay `<input type=file>` hasta pulsar "Cargar currículum" y el diálogo se abre en la pantalla del usuario, así que pídele que pulse él el botón y elija el archivo. Solo hace falta una vez: LinkedIn lo guarda para las siguientes.
5. **Preguntas adicionales**, con las respuestas ya confirmadas por el usuario:
   - Radios Yes/No: la primera opción es "Yes". Haz clic con el ratón en su label (`coordenadas` en modo radios); tras el clic LinkedIn cambia los `id`, así que verifica por posición.
   - Selects (nivel de idioma…): `find` "combobox" y `form_input` con el `ref` y el texto de la opción.
   - Textos: salario y años suelen ser **numéricos puros** (sin guiones ni "€"); "disponibilidad (en días)" también.
   Guarda en `respuestas` cualquier dato nuevo que dé el usuario para la próxima.
6. **Revisar y enviar**: dile al usuario que pulse **Revisar**, compruebe el resumen y pulse **Enviar solicitud** en el panel (ver reglas fijas). Si el entorno sí te deja pulsarlos, muestra antes el resumen y espera su "sí".
7. **Confirmar**: con el diálogo cerrado, la página de la oferta muestra "Solicitud enviada" en `main`. Si sigue abierto en "4/4 páginas Revisa tu solicitud", aún no se ha enviado: avísale.
8. Añade la fila al CSV (en `estado`, anota las respuestas relevantes: salario, años declarados…).

Envío automático de lote (solo si el usuario lo autorizó): el snippet **`enviar-si-simple`** envía únicamente cuando el botón es `Enviar solicitud` en la primera página, no hay campos extra, el CV seleccionado es el configurado y el teléfono está relleno. En cualquier otro caso se detiene y tú retomas a mano.

## 5. Cerrar la sesión de trabajo

Resume en tabla: enviadas, detenidas y por qué, dudosas. Recuerda al usuario dónde está el seguimiento (LinkedIn → Empleos → Mis empleos → Solicitados) y sugiere el siguiente pase en 2–3 días con `f_TPR=r604800`. Si en las preguntas de cribado salió algo que no está en el CV (una tecnología, un idioma), propón añadirlo. Si el usuario dijo algo incorrecto con consecuencias (p. ej. sobre darse de alta como autónomo para una oferta freelance), corrígelo con datos y sugiere consultarlo con una gestoría.
