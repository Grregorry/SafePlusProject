# SafePlus Frontend

React + TypeScript single-page application for the SafePlus assessment
platform. See the [root README](../README.md) for full project setup — this
file covers the frontend only.

## Running

```bash
npm install
npm run dev
```

Serves on http://localhost:5173. **The backend must be running** at
`http://127.0.0.1:8000` or nothing beyond the landing page will work.

To use a different port (if 5173 is taken):

```bash
set PORT=5174 && npm run dev
```

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Development server with hot reload |
| `npm run build` | Type-check then production build to `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | ESLint across the project |

## Configuration

One optional variable, in `frontend/.env` — see `.env.example`:

- `VITE_API_BASE_URL` — backend base URL. Defaults to
  `http://127.0.0.1:8000` when unset.

## Source layout

```
src/
├── api/          Typed clients per backend area; config.ts holds the base URL
├── assets/       Images
├── components/   Shared UI; maturity.ts defines the maturity scale and colours
├── features/
│   ├── assessment/   Setup, questions, responses, results, reports
│   ├── auth/         Register, login, account, email verification
│   ├── marketing/    Public landing page
│   └── survey/       Anonymous respondent survey flow
├── layouts/      App shell
└── App.tsx       Route definitions
```

## Notes

- Maturity thresholds in `components/maturity.ts` **mirror the backend** in
  `backend/app/services/scoring.py`. Change both together or results will
  disagree.
- Maturity levels deliberately use one hue at three strengths rather than
  red/amber/green, and always show the level name as text, so they remain
  legible to colour-blind users.