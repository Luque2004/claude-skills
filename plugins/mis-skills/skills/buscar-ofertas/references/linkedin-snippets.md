# Snippets JavaScript para LinkedIn

Se ejecutan con `mcp__Claude_Browser__javascript_tool` (`action: javascript_exec`) en la pestaña de LinkedIn. LinkedIn ofusca las clases CSS (`._709c7bd9`…), así que ninguno depende de nombres de clase: se apoyan en atributos `data-*`, en el texto de los encabezados y en los botones.

## extraer-lista

Página de resultados de búsqueda. Hace scroll en la lista para que se rendericen todas las tarjetas (LinkedIn solo pinta las visibles) y devuelve `id | título | empresa | lugar` sin duplicados.

```js
const list = document.querySelector('li[data-occludable-job-id]')?.closest('ul');
const scroller = (() => { let el = list; while (el && el !== document.body) { const s = getComputedStyle(el); if (/(auto|scroll)/.test(s.overflowY) && el.scrollHeight > el.clientHeight) return el; el = el.parentElement; } return document.scrollingElement; })();
for (let i = 0; i < 12; i++) { scroller.scrollTop += 500; await new Promise(r => setTimeout(r, 300)); }
const seen = new Map();
for (const li of document.querySelectorAll('li[data-occludable-job-id]')) {
  const id = li.getAttribute('data-occludable-job-id');
  const lines = li.innerText.split('\n').map(s => s.trim()).filter(Boolean).filter(s => !/with verification/.test(s));
  if (lines.length && !seen.has(id)) seen.set(id, id + ' | ' + lines.slice(0, 3).join(' | '));
}
({ total: document.querySelector('main')?.innerText.match(/[\d.]+ resultados?/)?.[0], jobs: [...seen.values()] })
```

Si `total` es `undefined`, la búsqueda no tuvo resultados y la lista son sugerencias de LinkedIn: ignórala.

## leer-oferta

Página `jobs/view/<id>/`. Localiza el bloque "Acerca del empleo" y devuelve los fragmentos con años de experiencia y palabras de nivel.

```js
const h = [...document.querySelectorAll('h2,h3')].find(e => /Acerca del empleo|About the job/i.test(e.innerText));
const d = (h?.parentElement?.parentElement?.innerText || '').replace(/\s+/g, ' ').trim();
({
  t: document.querySelector('h1')?.innerText.trim(),
  yrs: [...d.matchAll(/[^.;•]{0,80}\b\d+\s*\+?\s*(años|years|yrs)\b[^.;•]{0,60}/gi)].map(m => m[0].trim()).slice(0, 4),
  lvl: [...d.matchAll(/[^.;•]{0,60}\b(junior|senior|intern|prácticas|becari\w*|graduate|entry|freelance)\b[^.;•]{0,60}/gi)].map(m => m[0].trim()).slice(0, 4),
  snip: d.slice(0, 300)
})
```

## leer-requisitos

Misma página; devuelve ~900 caracteres a partir del bloque de requisitos.

```js
const h = [...document.querySelectorAll('h2,h3')].find(e => /Acerca del empleo|About the job/i.test(e.innerText));
const d = (h?.parentElement?.parentElement?.innerText || '').replace(/\s+/g, ' ').trim();
const m = d.search(/Requisitos|Requirements|Qué buscamos|Perfil|Buscamos|What you|Qualifications|Must have|Imprescindible|Se requiere/i);
({ t: document.querySelector('h1')?.innerText.trim(), req: d.slice(m < 0 ? 0 : m, (m < 0 ? 0 : m) + 900) })
```

## abrir-easy-apply

```js
const b = [...document.querySelectorAll('button')].find(b => /Solicitud sencilla|Easy Apply/.test(b.innerText));
b ? (b.click(), 'ok') : 'no'
```

Espera 3 s después.

## leer-formulario

Devuelve el botón activo, la página `n/m`, el texto del diálogo (sin la lista de países) y los campos con etiqueta y valor.

```js
const btn = [...document.querySelectorAll('button')].find(b => /Enviar solicitud|Siguiente|Revisar/.test(b.innerText.trim()));
let dlg = btn; for (let i = 0; i < 12 && dlg && dlg.innerText.length < 300; i++) dlg = dlg.parentElement;
const fields = [...dlg.querySelectorAll('input:not([type=hidden]),select,textarea')].map(el => ({
  tag: el.tagName, type: el.type, id: el.id,
  label: (el.closest('label')?.innerText || dlg.querySelector(`label[for="${el.id}"]`)?.innerText || el.closest('fieldset')?.querySelector('legend')?.innerText || el.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 150),
  value: el.type === 'radio' || el.type === 'checkbox' ? el.checked : el.value.slice(0, 100)
}));
({
  boton: btn?.innerText.trim(),
  pagina: (dlg.innerText.match(/\d\/\d páginas/) || [])[0],
  texto: dlg.innerText.replace(/\s+/g, ' ').replace(/Código del país\*.*?(Teléfono|Phone)/, '[país] $1').slice(0, 1200),
  fields
})
```

Los radios de LinkedIn tienen ancho 0 y sin etiqueta asociada: para saber a qué opción corresponden, mira `r.parentElement.innerText` ("Yes"/"No") y haz clic con el ratón sobre ese texto, no con `.click()`.

## botón por texto

```js
const b = [...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Siguiente'); // o 'Revisar' / 'Enviar solicitud'
b ? (b.click(), 'ok') : 'no'
```

Los botones sí aceptan `.click()` por JS; los inputs de texto y radios no.

## enviar-si-simple

Envía solo si el formulario es de una página, sin preguntas, con el CV configurado seleccionado y el teléfono relleno. Sustituye `CV_ARCHIVO` y `TELEFONO`.

```js
const btn = [...document.querySelectorAll('button')].find(b => /Enviar solicitud|Siguiente|Revisar/.test(b.innerText.trim()));
let dlg = btn; for (let i = 0; i < 12 && dlg && dlg.innerText.length < 300; i++) dlg = dlg.parentElement;
const extra = [...dlg.querySelectorAll('input:not([type=hidden]):not([type=radio]):not([type=checkbox]),select,textarea')]
  .map(el => (el.closest('label')?.innerText || dlg.querySelector(`label[for="${el.id}"]`)?.innerText || '').replace(/\s+/g, ' ').trim())
  .filter(l => !/^(Email|Email address|Phone|Teléfono móvil|Mobile phone number|Código del país)\*?$/.test(l));
const t = dlg.innerText.replace(/\s+/g, ' ');
const cvOk = /PDF CV_ARCHIVO/.test(t) && [...dlg.querySelectorAll('input[type=radio]')][0]?.checked;
const phone = dlg.querySelector('input[type=tel]')?.value;
const simple = btn?.innerText.trim() === 'Enviar solicitud' && extra.length === 0 && cvOk && phone === 'TELEFONO';
if (simple) btn.click();
({ empresa: document.querySelector('h1')?.innerText.trim(), boton: btn?.innerText.trim(), extra, cvOk, phone, enviado: simple })
```

Después: `wait` 3 s y captura (`scale: 0.4`) para ver el modal "Se ha enviado tu solicitud".

## Notas de comportamiento observadas (sept. 2026)

- El endpoint público `jobs-guest/jobs/api/jobPosting/<id>` devuelve vacío desde una sesión logueada; no sirve de atajo.
- Coordenadas: `getBoundingClientRect()` da píxeles CSS; el frame de la captura es 800×1176 y equivale a ×0.92. Con `find` los elementos del diálogo suelen no aparecer; usa captura + clic.
- La casilla "Seguir a <empresa>" viene marcada; es inofensiva.
- El límite de cargos en "Preferencias de empleo" es 5.
