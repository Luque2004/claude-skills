# InfoJobs

Guía para usar la skill en InfoJobs (observado en octubre de 2026). Las reglas fijas, `busqueda.json` y `solicitudes.csv` son los de SKILL.md. Para los perfiles junior de Barcelona, InfoJobs tiene más ofertas de pymes y agencias que LinkedIn, y casi todas indican experiencia y estudios mínimos en campos fijos, así que se criban rápido.

**Ve despacio.** El 01/10/2026, tras ~40 páginas automatizadas en una tarde (búsquedas + completar todo el CV), InfoJobs mostró "¿Eres humano o un robot? Hemos detectado una actividad poco habitual". Limita cada pase a unas 15–20 páginas y deja que el usuario haga a mano lo que sobre.

## Sesión

- El usuario se registra él (no se pueden crear cuentas por él) e inicia sesión en el panel. Comprueba la cabecera: con sesión aparece "Empleos · Mis ofertas · CV · Quién me ve"; sin sesión, "ACCESO CANDIDATOS".
- **Sin sesión, cada búsqueda enseña solo 5 resultados** aunque el título diga "15 ofertas". No cribes sin sesión.
- Banner de cookies: "Rechazar y cerrar".

## Buscar

```
https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=<kw>&provinceIds=9&sortBy=PUBLICATION_DATE&sinceDate=_7_DAYS
```

- `provinceIds=9` = provincia de Barcelona. `sinceDate`: `_24_HOURS`, `_7_DAYS`, `_15_DAYS`; quítalo para "cualquier fecha".
- El buscador es difuso: "frontend", "programador php" y "react" devuelven casi las mismas ofertas. Palabras clave que funcionaron: "programador web junior", "desarrollador web", "wordpress", "programador php", "frontend", "react", "programador junior".
- La página tiene dos bloques: los resultados de la búsqueda y, debajo de "Ofertas que quizá te interesen", coincidencias flojas que incluyen otras provincias. El bloque de abajo se carga al hacer **scroll con la rueda** (`computer` → `scroll`), no con `window.scrollBy`.
- **Popup "Buscamos ofertas para ti — Te hemos creado una alerta…"**: InfoJobs intenta crear una alerta por email en cada búsqueda nueva. Pulsa "NO, GRACIAS" salvo que el usuario haya pedido esa alerta (es configuración persistente de su cuenta).

### extraer-lista-infojobs

Después del scroll con rueda. Marca `[rel]` lo que va detrás de "Ofertas que quizá te interesen".

```js
const stop = [...document.querySelectorAll('h2,h3')].find(h => /Ofertas que quizá te interesen/.test(h.innerText));
const seen = new Map();
for (const a of document.querySelectorAll('a[href*="/of-i"]')) {
  const id = a.getAttribute('href').match(/of-i([0-9a-f]+)/)?.[1]; if (!id || seen.has(id) || !a.innerText.trim()) continue;
  let c = a; for (let j = 0; j < 8 && c && !/Contrato|Jornada|Hace|Salario/.test(c.innerText); j++) c = c.parentElement;
  const lines = (c?.innerText || '').split('\n').map(s => s.trim()).filter(Boolean).filter(l => l.length < 90);
  const sal = lines.find(l => /€/.test(l));
  const rel = stop && (stop.compareDocumentPosition(a) & Node.DOCUMENT_POSITION_FOLLOWING);
  seen.set(id, lines.slice(0, 4).join(' | ') + (sal ? ' | ' + sal : '') + (rel ? ' | [rel]' : '') + ' | ' + id);
}
({ h1: document.querySelector('h1')?.innerText, popup: /Buscamos ofertas para ti/.test(document.body.innerText), jobs: [...seen.values()] })
```

## Cribar

Cualquier oferta se abre solo con su ID: `https://www.infojobs.net/x/x/of-i<id>` (el slug da igual). La ficha tiene campos fijos: **Estudios mínimos**, **Experiencia mínima** ("No Requerida", "Al menos 1 año"…), salario, modalidad, nº de inscritos, y "Conocimientos necesarios que no tienes" (compara la oferta con el CV del portal: si ahí salen cosas que el usuario sí sabe, su CV de InfoJobs está incompleto).

### leer-oferta-infojobs

```js
const t = document.body.innerText.replace(/\n+/g, ' · '); const g = (re) => (t.match(re) || [])[1];
const i = t.search(/Descripción ·/);
({
  h1: document.querySelector('h1')?.innerText,
  est: g(/Estudios mínimos · ([^·]+)/), exp: g(/Experiencia mínima · ([^·]+)/),
  sal: g(/(\d[\d.]* ?€[^·]{0,40})/), mod: g(/(Presencial|Híbrido|Solo teletrabajo)/),
  falta: g(/Conocimientos necesarios que no tienes · ([\s\S]{0,200}?) · Sector/),
  inscritos: g(/(\d+ inscritos)/), desc: t.slice(i, i + 1000)
})
```

Si `h1` es "¿Eres humano o un robot?", para (reglas fijas). La experiencia mínima declarada a veces contradice el texto (p. ej. campo "3 años" y descripción "2 años"): usa la mayor.

## Completar el CV del portal

Las empresas filtran por los campos del CV de InfoJobs, no por el PDF. Con el perfil vacío, el usuario aparece como "sin estudios" y sin conocimientos. Hazlo solo con permiso y con datos que el usuario confirme (niveles, fechas). Cada sección se edita en:

```
https://www.infojobs.net/candidate/cv/cv-edit/edit.xhtml?fragment=<sección>&codiCv=<id del CV>
```

`<sección>`: `languages-data`, `skills`, `studies-data`, `experience`, `employment-status`, `job-preferences`, `text-cv-data`, `other-data`, `letter-data`. El `codiCv` sale de cualquier enlace "Añadir" de `/candidate/cv/view/index.xhtml`. Al guardar, la URL pasa a `…?fragment-saved=<sección>`: es la confirmación.

Trampas de los formularios:

- **Desplegables propios** (no `<select>`): clic en el campo, luego clic en la opción (con captura previa para ver su posición, o `find` con el texto de la opción y clic por `ref`).
- **Habilidades**: el nombre tiene autocompletado; elige la sugerencia exacta (p. ej. "ReactJS", que es la etiqueta que InfoJobs compara con las ofertas). Con 2 caracteres ("C#") no sugiere nada pero acepta texto libre. Niveles: Bajo / Medio / Alto. Una habilidad por formulario.
- **Idiomas**: niveles Nulo / Básico / Intermedio / Avanzado / Nativo.
- **Estudios**: fecha de inicio **y** de fin (MM/AAAA) son obligatorias. Un curso privado va en "Otros cursos y formación no reglada" (pide nombre del título y centro). InfoJobs calcula la duración restando fechas, así que 3 meses = inicio 3 meses antes del fin (12→02 sale como "2 meses").
- **Experiencia**: no existe casilla de "sin experiencia"; el enlace "No tengo experiencia" solo abre el formulario. Déjala vacía.
- **Situación laboral**: "¿Estás trabajando?" Sí/No; "cambio de residencia": Buena / Depende / Mala.
- **Preferencias**: asistente de 5 pasos (puestos, modalidad y ubicación, contratos, jornada, salario). El salario es un deslizador de 6K a 240K en saltos de 1.000: arrástralo con `left_click_drag` y comprueba `aria-valuenow` del `[role=slider]`. Activa "Ver ofertas sin salario especificado"; si no, InfoJobs oculta la mayoría de ofertas.
- **CV en texto**: el cuadro crece al escribir y empuja el botón Guardar hacia abajo. Pulsa Guardar por `ref` (`find` "Guardar"), no por coordenadas.

## Alertas

En la página de resultados, el interruptor "Activar alerta" (columna izquierda) crea una alerta por email con esa búsqueda. Créala **sin `sinceDate`** (la alerta ya filtra lo nuevo) y solo las que pida el usuario. Comprueba que el texto cambia a "Alerta activa".

## Inscribirse

Por ahora, la inscripción la hace el usuario: abre la oferta, pulsa "Inscribirme en esta oferta" y, si se pide, pega la carta de presentación. Tu parte es preparar la carta (adaptada a la oferta, sin afirmar nada que el usuario no haya confirmado, p. ej. disponibilidad para viajar) y responderle las preguntas de cribado con `respuestas`. Cuando diga "inscrito", añade la fila a `solicitudes.csv` con la URL `https://www.infojobs.net/x/x/of-i<id>` y "InfoJobs" en `estado`. El seguimiento está en "Mis ofertas".
