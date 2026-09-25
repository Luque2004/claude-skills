# Snippets JavaScript para LinkedIn

Se ejecutan con `mcp__Claude_Browser__javascript_tool` (`action: javascript_exec`) en la pestaña de LinkedIn. LinkedIn ofusca las clases CSS (`._709c7bd9`…), así que ninguno depende de nombres de clase: se apoyan en atributos `data-*` y `aria-*`, en el texto de los encabezados y en los botones.

Pega el snippet entero en cada llamada: la CSP de LinkedIn prohíbe `eval`/`new Function` (guardarlo en `sessionStorage` y ejecutarlo da `EvalError`), y las variables `window.__x` se pierden con cada `navigate`.

## extraer-lista

Página de resultados `/jobs/search-results/` (interfaz de sept. 2026). Espera a que cargue, hace scroll para que se pinten las 25 tarjetas y devuelve `id | título | empresa | lugar`.

Las tarjetas son `div[role=button]` dentro de `[data-testid=lazy-column]` y **no llevan el ID en el HTML**: está en las props de React, como `JobCardFrameworkImplDismissedState_<id>`. Para serializarlas hay que quitar las claves circulares de React; si no, `JSON.stringify` falla, el `catch` se lo traga y todos los ID salen `undefined`. La regex es `State_(\d+)` y no `\b\d+\b`, porque `_` cuenta como carácter de palabra.

```js
await new Promise(r => setTimeout(r, 2500));
const jid = (c) => { const pk = Object.keys(c).find(k => k.startsWith('__reactProps')); if (!pk) return; try { return JSON.stringify(c[pk], (kk, v) => (kk === 'return' || kk === '_owner' || kk === 'stateNode' || kk === 'child' || kk === 'sibling' || kk === 'alternate' || kk === '_debugOwner' || v instanceof Node) ? undefined : v).match(/State_(\d{8,12})/)?.[1]; } catch (e) { return } };
const lz = document.querySelector('[data-testid=lazy-column]');
let out;
if (!lz) out = { total: document.body.innerText.match(/[\d.]+ resultados?/)?.[0], jobs: [] }; else {
  let sc = lz; while (sc && sc !== document.body) { const s = getComputedStyle(sc); if (/(auto|scroll)/.test(s.overflowY) && sc.scrollHeight > sc.clientHeight) break; sc = sc.parentElement; }
  if (!sc || sc === document.body) sc = document.scrollingElement;
  const seen = new Map();
  for (let i = 0; i < 20; i++) {
    const div = [...lz.querySelectorAll('*')].find(e => e.children.length === 0 && /Hemos encontrado más resultados relacionados/.test(e.textContent));
    for (const c of lz.querySelectorAll('div[role=button]')) {
      const id = jid(c); if (!id || seen.has(id)) continue;
      const lines = c.innerText.split('\n').map(s => s.trim()).filter(Boolean).filter(s => !/^Seleccionado|verificado\)$|^·$/.test(s)).filter((s, j, a) => s !== a[j - 1]);
      const rel = div ? !!(div.compareDocumentPosition(c) & Node.DOCUMENT_POSITION_FOLLOWING) : false;
      seen.set(id, id + ' | ' + lines.slice(0, 3).join(' | ') + (rel ? ' | [rel]' : '') + (/Solicitud sencilla/.test(c.innerText) ? '' : ' | [noEA]'));
    }
    sc.scrollTop += 500; await new Promise(r => setTimeout(r, 300));
  }
  out = { total: document.body.innerText.match(/[\d.]+ resultados?/)?.[0], remoto: !!document.querySelector('input[aria-label="Filtrar por En remoto"]:checked'), jobs: [...seen.values()] };
}
out
```

- Con 0 resultados no existe `lazy-column` (de ahí el `if`). En remoto, `total` a veces no aparece.
- `[rel]`: va detrás del aviso "Hemos encontrado más resultados relacionados…", son resultados flojos. `[noEA]`: la tarjeta no tiene Solicitud sencilla.
- Usa `document.body`, no `main`: justo tras cargar, `main` puede ser `null`.

## leer-oferta

Página `jobs/view/<id>/`. Ejecútalo **después** de `wait` 3 s y una captura `scale: 0.1` (ver SKILL.md, sección 3). Busca el bloque "Acerca del empleo" (haciendo scroll hasta que cargue) y devuelve cabecera, modalidad, años, nivel, idiomas, salario, tecnologías y 400 caracteres del bloque de requisitos.

```js
const find = () => { const hh = [...document.querySelectorAll('h1,h2,h3')].find(e => /Acerca del empleo|About the job/i.test(e.innerText)); let b = hh; for (let j = 0; j < 6 && b && b.innerText.length < 400; j++) b = b.parentElement; return b && b.innerText.length > 150 ? b : null };
let box; for (let i = 0; i < 24 && !(box = find()); i++) { window.scrollBy(0, 400); await new Promise(r => setTimeout(r, 500)); }
[...(box?.querySelectorAll('button') || [])].find(x => /^…\s*más$/.test(x.innerText.trim()))?.click(); await new Promise(r => setTimeout(r, 1200));
const d = (box?.innerText || '').replace(/\s+/g, ' ').trim();
const top = (document.querySelector('main')?.innerText || '').split('\n').map(s => s.trim()).filter(Boolean);
const m = d.search(/Requisitos|Requirements|Qué buscamos|Perfil|Buscamos|What you|Qualifications|Must have|Imprescindible|Se requiere|Valoramos|Qué necesitas|Requisits/i);
const tech = [...new Set((d.match(/\b(React|Angular|Vue|Svelte|Node(\.js)?|TypeScript|JavaScript|PHP|Laravel|Symfony|Python|Django|FastAPI|Flask|Java|Spring|\.NET|C#|Unity|WordPress|PrestaShop|SQL|MySQL|PostgreSQL|MongoDB|Docker|Kubernetes|AWS|Azure|GCP|Kotlin|Swift|React Native|Next\.js|HTML|CSS|Salesforce|LLM|RAG|PyTorch|TensorFlow)\b/g) || []))];
({
  id: location.pathname.match(/\d+/)?.[0], len: d.length,
  top: top.slice(0, 4).join(' / ').slice(0, 150),
  mod: top.slice(0, 12).filter(s => /^(Híbrido|En remoto|Presencial|Jornada|Prácticas|Media jornada|Contrato|Temporal)/.test(s)).join(', '),
  aplicado: /Solicitado|Has solicitado|Ya has enviado|Solicitud enviada/.test(top.slice(0, 15).join(' ')),
  yrs: [...d.matchAll(/[^.;•]{0,70}\b\d+\s*\+?\s*(años|año|anys|any|years|year|yrs)\b[^.;•]{0,50}/gi)].map(m => m[0].trim()).slice(0, 3),
  lvl: [...d.matchAll(/[^.;•]{0,40}\b(junior|senior|intern|internship|prácticas|pràctiques|becari\w*|graduate|entry|trainee|recién|sin experiencia|convenio)\b[^.;•]{0,40}/gi)].map(m => m[0].trim()).slice(0, 3),
  idioma: [...d.matchAll(/[^.;•]{0,30}\b(ingl[eé]s|english|angl[eè]s|franc[eé]s|alem[aá]n|catal[aà]n)\b[^.;•]{0,40}/gi)].map(m => m[0].trim()).slice(0, 2),
  sal: (d.match(/[^.;•]{0,30}(\d{2}[.,]?\d{3}\s*(€|euros|EUR)|\d{2}\s?k\b)[^.;•]{0,30}/i) || [])[0],
  tech: tech.join(','),
  req: d.slice(m < 0 ? 0 : m, (m < 0 ? 0 : m) + 400)
})
```

Si `len` es 0, la descripción no ha cargado: repite con captura. Algunas ofertas tienen descripciones de menos de 200 caracteres (umbral 150); si ni así aparece, no trae requisitos.

## coordenadas

Para clicar con el ratón en campos del formulario (los inputs y radios ignoran `.click()`). Convierte `getBoundingClientRect` al frame de clics: **`800 / innerWidth`**, no un factor fijo (depende del ancho del panel). No uses la posición visual de la captura: con el panel oculto se pinta reducida y no coincide.

```js
const k = 800 / innerWidth;
const pos = (el, dx) => { const r = el.getBoundingClientRect(); return { x: Math.round((dx != null ? r.x + dx : r.x + r.width / 2) * k), y: Math.round((r.y + r.height / 2) * k) }; };
({
  tel: document.querySelector('input[type=tel]') && pos(document.querySelector('input[type=tel]')),
  textos: [...document.querySelectorAll('input[type=text]')].map(t => ({ id: t.id, ...pos(t) })),
  radios: [...document.querySelectorAll('input[type=radio]')].map(r => ({ id: r.id, ...pos(document.querySelector(`label[for="${r.id}"]`) || r.parentElement, 20) }))
})
```

Los radios van en pares Yes/No en ese orden. Los `id` cambian tras cada clic, así que verifica con `[...document.querySelectorAll('input[type=radio]')].map(r => r.checked)`.

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


Si no te dejan pulsar `Enviar solicitud`, este snippet no sirve: usa el reparto de clics de SKILL.md (el usuario pulsa Revisar → Enviar).

## Notas de comportamiento observadas (sept. 2026)

- El endpoint público `jobs-guest/jobs/api/jobPosting/<id>` devuelve vacío desde una sesión logueada; no sirve de atajo.
- La búsqueda es `/jobs/search-results/`; ignora `location`, `distance` y `f_WT` (ver SKILL.md, sección 2). El filtro "En remoto" se traduce en `f_SAL=f_SA_id_225001%3A272001`.
- Con el panel del navegador oculto, las descripciones de las ofertas no cargan hasta hacer una captura (aunque `document.visibilityState` sea `visible`).
- El teléfono del formulario de contacto no se recuerda entre solicitudes.
- Tras enviar, el modal "Se ha enviado tu solicitud a X" no aparece en `document.body.innerText`, pero al cerrarlo la página muestra "Solicitud enviada" en `main`.
- Con `find` los elementos del diálogo suelen no aparecer, salvo los `select` (`find` "combobox"), que se rellenan con `form_input`.
- La casilla "Seguir a <empresa>" viene marcada; es inofensiva.
- El límite de cargos en "Preferencias de empleo" es 5.
- Con sesión iniciada no sale banner de cookies; sin sesión, sí (no lo aceptes).
