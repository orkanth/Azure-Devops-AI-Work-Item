# Angular web application

## Responsibilities

- `app.component.*` is the root router host only.
- `app.routes.ts` owns feature routes, lazy loading, titles and page-title metadata.
- `layout/components/app-shell` owns the shared application frame.
- `features/*` owns page workflows and feature-specific components.
- `features/work-items/data-access` defines the work-item persistence contract and a demo-only in-memory adapter.
- `core` contains cross-cutting API, navigation, feedback and HTTP interception concerns.
- `shared` contains reusable UI and domain models.

## Commands

Run these from the monorepo root:

```bash
npm ci
npm run start:web
npx nx test web
npx nx build web
```

The Angular UI is still a prototype: CRUD writes currently mutate in-memory sample data. Use `docs/architecture/ENTERPRISE-FRONTEND-ARCHITECTURE.md` for the production integration boundary and remaining work.
