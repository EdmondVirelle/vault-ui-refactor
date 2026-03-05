# Vault UI Frontend Architecture

## Goals
- Keep UI behavior stable while adding new tools quickly.
- Isolate feature changes so one tab does not break another.
- Centralize Tauri integration and path validation logic.

## Layering

```text
src/
  app/                 # app composition (tabs, page shell, routing-like decisions)
  features/            # business features grouped by domain
    tasks/             # task center
    damage/            # damage calculator
  domain/              # business domain contracts
  ipc/                 # tauri ipc payload/event contracts
  core/                # infrastructure adapters (tauri client, app-wide services)
  shared/              # cross-feature pure utilities
  types.ts             # shared contracts from backend
```

Dependency direction:
- `app -> features -> core/shared -> types`
- `features` cannot import from `app`
- `shared` cannot depend on Tauri runtime

## Contracts
- Domain models live in `src/domain/*`.
- IPC request/response/event models live in `src/ipc/*`.
- [`src/types.ts`](src/types.ts) is a backward-compatible barrel, not the source of truth.
- Backend command names are treated as stable API surface.
- Any command schema change must update `types.ts` and both feature callers.

## Tauri Boundary
- Use [`src/core/tauri.ts`](src/core/tauri.ts) for all `invoke` calls.
- Do not directly call `invoke` in feature code.
- Keep Tauri availability checks and common error text in one place.

## Feature Rules
- Each feature owns:
  - input state
  - validation state
  - log rendering
  - event subscriptions
- Reusable pure logic goes to `shared`.
- Reusable infra logic goes to `core`.

## Backward Compatibility
- [`src/FormBuilder.tsx`](src/FormBuilder.tsx) and [`src/DamageCalculator.tsx`](src/DamageCalculator.tsx) are compatibility shims to new feature modules.
- [`src/App.tsx`](src/App.tsx) points to the new app shell.

## Recommended Extension Pattern
1. Add new tab container in `app/AppShell.tsx`.
2. Create `features/<domain>/<Domain>Panel.tsx`.
3. Add command adapters in `core` only when needed.
4. Reuse types from `types.ts`; do not create duplicate request models.
5. Validate with:
   - `npx tsc --noEmit`
   - `npm run lint`
   - `npm run test:run`
   - `cd src-tauri && cargo check`
