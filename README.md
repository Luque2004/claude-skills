# claude-skills

Marketplace personal de plugins para [Claude Code](https://docs.claude.com/en/docs/claude-code). Contiene el plugin `mis-skills`, con todas mis skills, para instalarlas en cualquier dispositivo con dos comandos.

## Instalar en un dispositivo nuevo

```bash
claude plugin marketplace add Luque2004/claude-skills
claude plugin install mis-skills@claude-skills
```

Abre una sesión nueva de Claude Code y las skills estarán disponibles.

## Skills incluidas

| Skill | Qué hace | Cómo invocarla |
|---|---|---|
| `comentar-codigo` | Añade comentarios breves en español encima de cada bloque (funciones, bucles, condicionales…) sin tocar la lógica. Respeta comentarios existentes y avisa de bugs que vea. | "comenta el código", "coméntame `src/api.js`", "no entiendo este script, explícamelo con comentarios" |
| `buscar-ofertas` | Busca ofertas en LinkedIn con tu sesión, las criba leyendo la descripción (años de experiencia, nivel, stack) y presenta solicitudes con "Solicitud sencilla", pidiendo confirmación antes de cada envío. Lee tus criterios de `busqueda.json` y lleva el registro en `solicitudes.csv` (fuera del repo, en tu carpeta de CV). | "busca ofertas junior de web", "aplica a las que encajen", "qué ofertas nuevas hay esta semana" |

## Actualizar en un dispositivo ya instalado

```bash
claude plugin marketplace update claude-skills
claude plugin update mis-skills@claude-skills
```

## Añadir una skill nueva

1. Crea `plugins/mis-skills/skills/<nombre-de-la-skill>/SKILL.md`.
2. El `SKILL.md` empieza con frontmatter YAML (`name`, `description`) y después las instrucciones en Markdown.
3. Sube la versión en `plugins/mis-skills/.claude-plugin/plugin.json` y en `.claude-plugin/marketplace.json`.
4. `git commit` + `git push`, y actualiza el plugin en cada dispositivo.

## Estructura

```
.claude-plugin/marketplace.json        # catálogo de plugins del repo
plugins/mis-skills/
  .claude-plugin/plugin.json           # manifiesto del plugin
  skills/
    <skill>/SKILL.md                   # una carpeta por skill
```
