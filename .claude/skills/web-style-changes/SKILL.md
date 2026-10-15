---
name: web-style-changes
description: Frontend styling workflow for the La Gran Sala web application. Use when making visual changes to the FastAPI/Jinja2 web interface including layout adjustments, color changes, spacing, typography, or responsive design. Triggered by requests to update styling, change the look, adjust layout, style templates, or modify the web application appearance.
---

# Web Style Changes

## Quick Start

1. Locate the template file in `src/lagransala/applications/web/templates/`
2. Edit Tailwind utility classes directly in the HTML/Jinja template
3. Run the development server: `uv run lagransala web --watch`
4. Preview changes at the local URL (default: http://127.0.0.1:8000)

## Template Location

All web templates are in `src/lagransala/applications/web/templates/`:

- `index.html` - Main event listing page
- Other templates as needed

## Making Style Changes

### Tailwind CSS (Primary Styling)

The application uses Tailwind CSS via CDN. Edit utility classes directly in HTML elements.

**Common patterns:**
- Layout: `flex`, `grid`, `container`, `mx-auto` (center), `p-4` (padding)
- Spacing: `m-4` (margin), `gap-4` (flex/grid gap), `space-y-4` (vertical spacing)
- Colors: `bg-blue-500`, `text-gray-700`, `border-gray-300`
- Typography: `text-xl`, `font-bold`, `text-center`
- Responsive: `md:flex`, `lg:w-1/2` (breakpoint modifiers)

**No build step required** - changes are reflected immediately on browser refresh.

### htmx (Dynamic Behavior)

The application uses htmx for dynamic HTML updates. htmx attributes add interactivity without JavaScript:

- `hx-get="/path"` - Make GET request
- `hx-swap="innerHTML"` - Replace content
- `hx-target="#id"` - Target element

**No build step required** for htmx changes.

### Backend Changes (When Needed)

Most style changes only require template edits. However, structural changes may require backend modifications:

- **Data structure**: If layout needs different data organization
- **New endpoints**: For new pages or dynamic interactions
- **Context variables**: Pass different data to templates

Backend code is in `src/lagransala/applications/web/`.

## Development Workflow

### Start the Server

```bash
uv run lagransala web --watch
```

The `--watch` flag enables hot-reload for template changes. Server output shows the local URL (typically http://127.0.0.1:8000).

### Iteration Cycle

1. Edit template file
2. Save changes
3. Refresh browser (hot-reload picks up changes automatically)
4. Repeat until satisfied

### Troubleshooting

- **Changes not visible**: Hard refresh browser (Ctrl+Shift+R / Cmd+Shift+R)
- **Server not starting**: Check if port 8000 is already in use
- **htmx not working**: Ensure htmx CDN script is loaded in `<head>`

## References

- [Tailwind CSS documentation](https://tailwindcss.com/docs) for complete utility reference
- [htmx documentation](https://htmx.org/docs/) for dynamic behavior patterns
