// Digital Temirzhol — shared navbar, one for all pages.
// Page config (optional, before this script):
//   window.PAGE = { section: "home|checkin|login|register|cabinet", badge, title, sub }
// Loaded AFTER js/api.js. Re-renders on language change.

const CABINET_BY_ROLE = {
  BOSS: "boss.html",
  DISPATCHER: "dispatcher.html",
  MASTER: "master.html",
  WORKER: "worker.html"
};

const ROLE_BADGE = {
  BOSS: "БАСТЫҚ",
  DISPATCHER: "ДНЦ",
  MASTER: "ШЕБЕР",
  WORKER: "ЖҰМЫСШЫ"
};

const ROLE_NAME = {
  BOSS: "ПЧ Бастығы",
  DISPATCHER: "Поезд Диспетчері",
  MASTER: "Жол шебері",
  WORKER: "Жұмысшы"
};

function layoutInitials(name) {
  const parts = (name || "?").trim().split(/\s+/);
  return ((parts[0] || "?")[0] + (parts[1] ? parts[1][0] : "")).toUpperCase();
}

function renderNavbar() {
  const mount = document.getElementById("appNavbar");
  if (!mount || typeof Api === "undefined") return;

  const page = window.PAGE || {};
  const path = (window.location.pathname.split("/").pop() || "index.html").toLowerCase();
  const section = page.section || (path.includes("checkin") ? "checkin"
    : path.includes("login") ? "login"
    : path.includes("register") ? "register"
    : (path.includes("boss") || path.includes("master") || path.includes("dispatcher") || path.includes("worker")) ? "cabinet"
    : "home");

  const user = Api.getUser();
  const badge = page.badge || (user && section === "cabinet" ? (ROLE_BADGE[user.role] || "ҚТЖ") : "ҚТЖ");
  const title = page.title || "Digital Temirzhol";
  const sub = page.sub || "";

  const link = (href, label, key) => {
    const active = (key === section) ? ` style="color:var(--primary);font-weight:700;"` : "";
    return `<a href="${href}" class="nav-link"${active}>${label}</a>`;
  };

  let right = `<button class="btn-lang" id="btnLangToggle" title="Тілді ауыстыру / Сменить язык"></button>`;
  right += link("index.html", "Басты бет", "home");
  right += link("checkin.html", "Фото-чекин", "checkin");

  if (user) {
    const cabinet = CABINET_BY_ROLE[user.role] || "index.html";
    right += link(cabinet, "Менің кабинетім", "cabinet");
    const avatar = user.photo_url
      ? `<img src="${Api.getFileUrl(user.photo_url)}" alt="" style="width:34px;height:34px;border-radius:50%;object-fit:cover;border:2px solid var(--primary);" onerror="this.style.display='none'">`
      : `<span style="width:34px;height:34px;border-radius:50%;background:var(--primary);color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:13px;font-weight:800;">${layoutInitials(user.full_name)}</span>`;
    right += `
      <span style="display:inline-flex;align-items:center;gap:10px;margin-left:4px;">
        ${avatar}
        <span style="text-align:right;line-height:1.25;">
          <span style="display:block;font-size:13.5px;font-weight:700;color:var(--text-main);">${(user.full_name || "").replace(/</g, "&lt;")}</span>
          <span style="display:block;font-size:11px;color:var(--primary);font-weight:600;">${ROLE_NAME[user.role] || user.role}</span>
        </span>
        <button class="btn btn-secondary btn-sm" onclick="Api.logout()">Шығу</button>
      </span>`;
  } else {
    right += link("login.html", "Кіру", "login");
    right += `<a href="register.html" class="btn btn-primary btn-sm">Тіркелу</a>`;
  }

  mount.innerHTML = `
    <header class="navbar">
      <a href="index.html" class="brand-wrapper">
        <div class="brand-badge">${badge}</div>
        <div class="brand-info">
          <h1>${title}</h1>
          ${sub ? `<p>${sub}</p>` : ""}
        </div>
      </a>
      <div class="nav-actions">${right}</div>
    </header>`;

  // (Re)bind language toggle — I18n.init ran before this navbar existed.
  const btn = document.getElementById("btnLangToggle");
  if (btn && typeof I18n !== "undefined") {
    I18n.updateToggleButton();
    btn.addEventListener("click", () => I18n.toggleLang());
  }
}

if (typeof window !== "undefined") {
  window.addEventListener("DOMContentLoaded", renderNavbar);
  window.addEventListener("languageChanged", renderNavbar);
}
