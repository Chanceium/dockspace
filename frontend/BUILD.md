# Vue Build Instructions

## Quick Commands

### Development
```bash
npm run dev          # Start dev server with hot-reload (port 5173)
```

### Production Build
```bash
npm run build        # Builds to ../dockspace/static/dist/
```

### Preview Production Build
```bash
npm run preview      # Preview production build (port 5050)
```

## Output Location

Vue builds to: `../dockspace/static/dist/`

This is configured in `vite.config.ts`:
```typescript
build: {
  outDir: '../dockspace/static/dist',
  base: '/static/dist/',
}
```

## Build Process

1. Vite compiles TypeScript → JavaScript
2. Bundles all Vue components
3. Optimizes and minifies CSS/JS
4. Outputs to `dockspace/static/dist/`
5. Django serves these files via WhiteNoise

## File Hashing

Vite automatically adds content hashes to filenames for cache busting:
- `index-lgf7La5i.js` 
- `index-Bpbo5y4W.css`

The `index.html` file references these hashed files automatically.

## Docker Build

The Dockerfile builds Vue automatically in a multi-stage build:
```dockerfile
# Stage 1: Build Vue
FROM node:20-alpine AS frontend-builder
COPY frontend/ ./
RUN npm ci && npm run build

# Stage 2: Copy to Django
COPY --from=frontend-builder /frontend/dist ./dockspace/static/dist
```

No manual build needed for Docker deployments!
