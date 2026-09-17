// Digital Temirzhol — deploy-time API config.
// This file is loaded BEFORE js/api.js on every page.
//
// Priority for API base URL:
//   1. window.DT_API_BASE (set here or via Vercel/Render env inject)
//   2. localStorage "dt_api_base" (manual override in browser console)
//   3. Same-origin "" when served by FastAPI itself (port 8000 or /api reachable)
//   4. Local dev fallback http://127.0.0.1:8000
//
// For Vercel: set window.DT_API_BASE to your Render backend URL, e.g.
//   window.DT_API_BASE = "https://digitaltemirzhol-api.onrender.com";
// Or leave empty "" — api.js will auto-detect same-origin.
window.DT_API_BASE = "";
