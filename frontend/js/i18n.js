// Digital Temirzhol — Bilingual i18n System (Қазақша / Русский)
// Clean enterprise texts without casual emojis

const DICTIONARY = {
  kz: {
    // Brand & Header
    "brand_title": "Digital Temirzhol",
    "brand_sub": "ҚТЖ Өндірістік цифрлық басқару жүйесі",
    "brand_checkin_sub": "Өткізу бекеті • Фото-фиксация",
    "nav_home": "Басты бет",
    "nav_checkin": "Фото-чекин",
    "nav_kiosk": "Киоск QR",
    "nav_login": "Кіру",
    "nav_register": "Тіркелу",
    "nav_logout": "Шығу",

    // Checkin page
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
    "default_worker": "Жұмысшы",

    // Roles & Index
    "hero_tag": "ҚТЖ ӨНДІРІСТІК ПЛАТФОРМАСЫ",
    "hero_title": "Қазақстан Темір Жолы: Қағазбастылықты жою және жедел цифрландыру",
    "hero_desc": "Бастықтың жұмысын жеңілдету, жұмысшыларды фото-фиксация арқылы тіркеу, Smart Наряд-допуск №451 бланкін 2 минутта рәсімдеу және больничныйларды скриншотпен бекіту.",
    "btn_open_checkin": "Проходнаядан өту (Фото-чекин)",
    "btn_open_kiosk": "Проходная экран-киоскі",
    "stat_saved": "100%",
    "stat_saved_label": "Фото-фиксация сақталуы",
    "stat_speed": "2 мин",
    "stat_speed_label": "Наряд-допуск рәсімдеу",
    "roles_heading": "Жүйеге кіру жолдары мен жеке кабинеттер",
    "role_checkin_title": "Өткізу бекеті (Фото)",
    "role_checkin_desc": "Камерадан суретке түсіріп, тікелей дерекқорға сақтау: [Келдім] немесе [Кеттім].",
    "role_boss_title": "ПЧ Бастығы (Директор)",
    "role_boss_desc": "Табельді бақылау, больничный бекіту, нарядқа цифрлық қол қою, Excel жүктеу.",
    "role_disp_title": "Поезд Диспетчері (ДНЦ)",
    "role_disp_desc": "Қозғалыс қауіпсіздігі, нарядтарға «Технологиялық терезе / Окно» рұқсатын беру.",
    "role_master_title": "Жол шебері / Бригадир",
    "role_master_desc": "№451 Наряд-допуск толтыру, ТК таңдау, бригада жинау және жұмысты жабу.",
    "btn_enter_cabinet": "Кабинетке өту ➔",

    // Password Reset
    "forgot_password": "Құпиясөзді ұмыттыңыз ба?",
    "reset_title": "Құпиясөзді қалпына келтіру",
    "reset_sub": "Тіркелген телефон нөміріңізді немесе электрондық поштаңызды енгізіңіз",
    "reset_identifier_label": "Телефон нөмірі немесе Email:",
    "reset_btn_send": "Растау кодын алу ➔",
    "reset_code_label": "6-таңбалы растау коды:",
    "reset_new_password": "Жаңа құпиясөз:",
    "reset_confirm_password": "Жаңа құпиясөзді растаңыз:",
    "reset_btn_submit": "Құпиясөзді жаңарту және кіру ➔",
    "reset_back": "Кіру бетіне қайту",

    // Common
    "lang_toggle": "ҚАЗ",
    "status_loading": "Жүктелуде...",
    "btn_save": "Сақтау",
    "btn_cancel": "Болдырмау",
    "btn_approve": "Бекіту",
    "btn_reject": "Қайтару"
  },

  ru: {
    // Brand & Header
    "brand_title": "Digital Temirzhol",
    "brand_sub": "КТЖ • Цифровая система производственного контроля",
    "brand_checkin_sub": "Проходной пункт • Фотофиксация",
    "nav_home": "Главная",
    "nav_checkin": "Фото-чекин",
    "nav_kiosk": "Экран QR",
    "nav_login": "Войти",
    "nav_register": "Регистрация",
    "nav_logout": "Выйти",

    // Checkin page
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
    "default_worker": "Работник",

    // Roles & Index
    "hero_tag": "ПРОИЗВОДСТВЕННАЯ ЦИФРОВАЯ СИСТЕМА КТЖ",
    "hero_title": "Казахстан Темир Жолы: Исключение бумажной волокиты и цифровизация",
    "hero_desc": "Облегчение работы руководства, моментальный проход по фотофиксации, оформление Smart Наряда-допуска №451 за 2 минуты и утверждение больничных по скриншотам.",
    "btn_open_checkin": "Пройти через КПП (Фото-чекин)",
    "btn_open_kiosk": "Экран-киоск КПП",
    "stat_saved": "100%",
    "stat_saved_label": "Сохранение снимков",
    "stat_speed": "2 мин",
    "stat_speed_label": "Оформление наряда",
    "roles_heading": "Точки входа и личные кабинеты",
    "role_checkin_title": "Проходной пункт (Фото)",
    "role_checkin_desc": "Снимок с камеры и прямая запись в базу: [Пришел] или [Ушел].",
    "role_boss_title": "Начальник ПЧ (Директор)",
    "role_boss_desc": "Контроль табеля, утверждение больничных, цифровая подпись нарядов, выгрузка Excel.",
    "role_disp_title": "Поездной диспетчер (ДНЦ)",
    "role_disp_desc": "Безопасность движения, предоставление «Технологического окна» для нарядов.",
    "role_master_title": "Дорожный мастер / Бригадир",
    "role_master_desc": "Оформление Наряда №451, автовыбор ТК, сбор бригады и закрытие работ.",
    "btn_enter_cabinet": "В кабинет ➔",

    // Password Reset
    "forgot_password": "Забыли пароль?",
    "reset_title": "Сброс пароля",
    "reset_sub": "Введите номер телефона или электронную почту, указанные при регистрации",
    "reset_identifier_label": "Номер телефона или Email:",
    "reset_btn_send": "Получить проверочный код ➔",
    "reset_code_label": "6-значный код подтверждения:",
    "reset_new_password": "Новый пароль:",
    "reset_confirm_password": "Подтвердите новый пароль:",
    "reset_btn_submit": "Обновить пароль и войти ➔",
    "reset_back": "Вернуться ко входу",

    // Common
    "lang_toggle": "РУС",
    "status_loading": "Загрузка...",
    "btn_save": "Сохранить",
    "btn_cancel": "Отмена",
    "btn_approve": "Утвердить",
    "btn_reject": "Отклонить"
  }
};

const I18n = {
  currentLang: localStorage.getItem("smartrail_lang") || "kz",

  getLang() {
    return this.currentLang;
  },

  setLang(lang) {
    if (lang !== "kz" && lang !== "ru") lang = "kz";
    this.currentLang = lang;
    localStorage.setItem("smartrail_lang", lang);
    document.documentElement.lang = lang;
    this.applyTranslations();
    this.updateToggleButton();
    window.dispatchEvent(new CustomEvent("languageChanged", { detail: { lang } }));
  },

  toggleLang() {
    const next = this.currentLang === "kz" ? "ru" : "kz";
    this.setLang(next);
  },

  t(key, fallback = "") {
    const dict = DICTIONARY[this.currentLang] || DICTIONARY.kz;
    return dict[key] || fallback || key;
  },

  applyTranslations() {
    // 1. Text elements
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      const val = this.t(key);
      if (val) {
        el.textContent = val;
      }
    });

    // 2. HTML elements
    document.querySelectorAll("[data-i18n-html]").forEach(el => {
      const key = el.getAttribute("data-i18n-html");
      const val = this.t(key);
      if (val) {
        el.innerHTML = val;
      }
    });

    // 3. Placeholders
    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
      const key = el.getAttribute("data-i18n-placeholder");
      const val = this.t(key);
      if (val) {
        el.placeholder = val;
      }
    });
  },

  updateToggleButton() {
    const btn = document.getElementById("btnLangToggle");
    if (btn) {
      if (this.currentLang === "kz") {
        btn.innerHTML = `<strong>ҚАЗ</strong> | <span style="opacity:0.55;">РУС</span>`;
      } else {
        btn.innerHTML = `<span style="opacity:0.55;">ҚАЗ</span> | <strong>РУС</strong>`;
      }
    }
  },

  init() {
    document.documentElement.lang = this.currentLang;
    this.applyTranslations();
    this.updateToggleButton();

    // Auto-bind toggle button if present
    const btn = document.getElementById("btnLangToggle");
    if (btn) {
      btn.addEventListener("click", () => this.toggleLang());
    }
  }
};

// Initialize on DOM ready
if (typeof window !== "undefined") {
  window.addEventListener("DOMContentLoaded", () => {
    I18n.init();
  });
}
