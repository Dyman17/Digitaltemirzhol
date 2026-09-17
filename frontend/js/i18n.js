// Digital Temirzhol — Bilingual i18n System (Қазақша / Русский)
// Only keys actually used by the pages (via data-i18n / I18n.t).

const DICTIONARY = {
  kz: {
    "brand_title": "Digital Temirzhol",
    "brand_checkin_sub": "Өткізу бекеті • Фото-фиксация",
    "nav_home": "Басты бет",
    "nav_checkin": "Фото-чекин",
    "nav_login": "Кіру",
    "nav_register": "Тіркелу",
    "nav_logout": "Шығу",

    "checkin_badge": "ФОТО-ТІРКЕУ БЕКЕТІ",
    "checkin_title": "Жұмыс орнына кіру / кетуді фотоға түсіру",
    "checkin_desc": "Камераға қарап, тиісті батырманы басыңыз. Фото автоматты түрде түсіріліп, дерекқорға сақталады.",
    "camera_active": "Камера белсенді",
    "camera_loading": "Камера қосылуда...",
    "camera_error": "Камера табылмады немесе рұқсат берілмеген",
    "camera_refresh": "Камераны қайта қосу",
    "checkpoint_label": "Бекет: КПП ПЧ-13 (Бас өткізу орны)",
    "worker_name_label": "Жұмыскердің аты-жөні (Ф.И.О.):",
    "worker_name_placeholder": "Мысалы: Бақытов Нұржан (немесе бос қалдырыңыз)",
    "btn_checkin": "ЖҰМЫСҚА КЕЛДІМ (КІРУ)",
    "btn_checkout": "ЖҰМЫСТАН КЕТТІМ (ШЫҒУ)",
    "checkin_success_title": "СӘТТІ ТІРКЕЛДІ",
    "checkin_success_text": "Фото дерекқорға сәтті сақталды.",
    "recent_checkins_title": "Соңғы фото-тіркеулер (Дерекқордан)",
    "recent_refresh": "Жаңарту",
    "col_photo": "Фото",
    "col_worker": "Қызметкер",
    "col_action": "Әрекет",
    "col_time": "Уақыты",
    "no_records": "Әзірге тіркеулер жоқ",
    "action_in": "Келді (Кіру)",
    "action_out": "Кетті (Шығу)",
    "default_worker": "Жұмысшы"
  },

  ru: {
    "brand_title": "Digital Temirzhol",
    "brand_checkin_sub": "Проходной пункт • Фотофиксация",
    "nav_home": "Главная",
    "nav_checkin": "Фото-чекин",
    "nav_login": "Войти",
    "nav_register": "Регистрация",
    "nav_logout": "Выйти",

    "checkin_badge": "ПУНКТ ФОТОФИКСАЦИИ",
    "checkin_title": "Фиксация явки / ухода с работы по фотографии",
    "checkin_desc": "Посмотрите в камеру и нажмите нужную кнопку. Снимок автоматически сохранится в базу данных.",
    "camera_active": "Камера активна",
    "camera_loading": "Подключение камеры...",
    "camera_error": "Камера не найдена или доступ заблокирован",
    "camera_refresh": "Перезапустить камеру",
    "checkpoint_label": "Пункт: КПП ПЧ-13 (Главная проходная)",
    "worker_name_label": "Ф.И.О. сотрудника:",
    "worker_name_placeholder": "Например: Бахытов Нуржан (или оставьте пустым)",
    "btn_checkin": "НА РАБОТУ (ВХОД)",
    "btn_checkout": "С РАБОТЫ (ВЫХОД)",
    "checkin_success_title": "УСПЕШНО ЗАФИКСИРОВАНО",
    "checkin_success_text": "Фотография успешно сохранена в базу данных.",
    "recent_checkins_title": "Последние фотофиксации (Из базы)",
    "recent_refresh": "Обновить",
    "col_photo": "Фото",
    "col_worker": "Сотрудник",
    "col_action": "Действие",
    "col_time": "Время",
    "no_records": "Записей пока нет",
    "action_in": "Пришел (Вход)",
    "action_out": "Ушел (Выход)",
    "default_worker": "Работник"
  }
};

const I18n = {
  currentLang: "kz",

  getLang() {
    return this.currentLang;
  },

  load() {
    try {
      const saved = localStorage.getItem("smartrail_lang");
      if (saved === "kz" || saved === "ru") this.currentLang = saved;
    } catch (e) { /* storage unavailable */ }
  },

  setLang(lang) {
    if (lang !== "kz" && lang !== "ru") lang = "kz";
    this.currentLang = lang;
    try { localStorage.setItem("smartrail_lang", lang); } catch (e) {}
    document.documentElement.lang = lang;
    this.applyTranslations();
    this.updateToggleButton();
    window.dispatchEvent(new CustomEvent("languageChanged", { detail: { lang } }));
  },

  toggleLang() {
    this.setLang(this.currentLang === "kz" ? "ru" : "kz");
  },

  t(key, fallback = "") {
    const dict = DICTIONARY[this.currentLang] || DICTIONARY.kz;
    return dict[key] || fallback || key;
  },

  applyTranslations() {
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const val = this.t(el.getAttribute("data-i18n"));
      if (val) el.textContent = val;
    });
    document.querySelectorAll("[data-i18n-html]").forEach(el => {
      const val = this.t(el.getAttribute("data-i18n-html"));
      if (val) el.innerHTML = val;
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
      const val = this.t(el.getAttribute("data-i18n-placeholder"));
      if (val) el.placeholder = val;
    });
  },

  updateToggleButton() {
    const btn = document.getElementById("btnLangToggle");
    if (btn) {
      btn.innerHTML = this.currentLang === "kz"
        ? `<strong>ҚАЗ</strong> | <span style="opacity:0.55;">РУС</span>`
        : `<span style="opacity:0.55;">ҚАЗ</span> | <strong>РУС</strong>`;
    }
  },

  init() {
    this.load();
    document.documentElement.lang = this.currentLang;
    this.applyTranslations();
    this.updateToggleButton();
    const btn = document.getElementById("btnLangToggle");
    if (btn) btn.addEventListener("click", () => this.toggleLang());
  }
};

if (typeof window !== "undefined") {
  window.addEventListener("DOMContentLoaded", () => {
    I18n.init();
  });
}
