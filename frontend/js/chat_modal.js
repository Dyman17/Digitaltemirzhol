// Digital Temirzhol — Unified Chat & Print Helper
// Supports 1-hour auto-pruned direct messaging and official print sheet

let currentChatTarget = null;
let chatPollInterval = null;

function getCurrentUserOrPrompt() {
  let user = Api.getUser();
  if (!user) {
    // If not logged in, look for cached guest identity or prompt
    const guest = localStorage.getItem("dt_chat_guest");
    if (guest) {
      try { return JSON.parse(guest); } catch(e){}
    }
  }
  return user;
}

function ensureCurrentUser(callback) {
  let user = getCurrentUserOrPrompt();
  if (user && user.id) {
    callback(user);
    return;
  }

  // Quick clean modal to identify sender if anonymous
  let modal = document.getElementById("chatSenderModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "chatSenderModal";
    modal.className = "modal-overlay";
    modal.innerHTML = `
      <div class="modal-box" style="max-width: 420px;">
        <h3 style="font-size: 16px; margin-bottom: 8px;">Чатқа кіру / Вход в чат</h3>
        <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">
          Хабарлама жіберу үшін атыңызды таңдаңыз немесе жазыңыз:
        </p>
        <div style="margin-bottom: 12px;">
          <input type="text" id="chatGuestName" class="form-control" placeholder="Аты-жөніңіз (ФИО)..." style="width:100%;">
        </div>
        <div style="display:flex; justify-content:flex-end; gap:8px;">
          <button class="btn btn-secondary" onclick="document.getElementById('chatSenderModal').classList.remove('active')">Бас тарту</button>
          <button class="btn btn-primary" id="btnConfirmChatSender">Жалғастыру</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  modal.classList.add("active");
  const btn = document.getElementById("btnConfirmChatSender");
  btn.onclick = async () => {
    const name = document.getElementById("chatGuestName").value.trim() || "Қызметкер";
    // Find or create temporary guest user in DB
    try {
      const users = await Api.getChatUsers(name);
      let guestUser = users.find(u => u.full_name.toLowerCase() === name.toLowerCase());
      if (!guestUser) {
        // Register temporary or use fallback
        guestUser = { id: 9999, full_name: name, role: "WORKER" };
      }
      localStorage.setItem("dt_chat_guest", JSON.stringify(guestUser));
      modal.classList.remove("active");
      callback(guestUser);
    } catch(err) {
      const guestUser = { id: 9999, full_name: name, role: "WORKER" };
      localStorage.setItem("dt_chat_guest", JSON.stringify(guestUser));
      modal.classList.remove("active");
      callback(guestUser);
    }
  };
}

function openChatWith(targetUserId, targetUserName, targetUserRole = "") {
  ensureCurrentUser((currentUser) => {
    currentChatTarget = { id: targetUserId, name: targetUserName, role: targetUserRole };
    renderChatModal(currentUser, currentChatTarget);
    loadChatMessages(currentUser.id, targetUserId);

    if (chatPollInterval) clearInterval(chatPollInterval);
    chatPollInterval = setInterval(() => {
      if (currentChatTarget && document.getElementById("chatDialogModal")?.classList.contains("active")) {
        loadChatMessages(currentUser.id, currentChatTarget.id, false);
      }
    }, 2500);
  });
}

function renderChatModal(currentUser, target) {
  let modal = document.getElementById("chatDialogModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "chatDialogModal";
    modal.className = "modal-overlay";
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div class="modal-box" style="max-width: 520px; display: flex; flex-direction: column; height: 560px; max-height: 90vh;">
      <!-- Header -->
      <div style="display:flex; justify-content:space-between; align-items:flex-start; border-bottom:1px solid var(--border-color); padding-bottom:12px; margin-bottom:12px;">
        <div>
          <div style="font-size: 16px; font-weight: 700; color: var(--text-main);">${escapeHtml(target.name)}</div>
          <div style="font-size: 12px; color: var(--primary);">${escapeHtml(target.role || "Қызметкер")}</div>
          <div style="font-size: 11px; color: #b45309; background:#fffbeb; padding:2px 6px; border-radius:4px; display:inline-block; margin-top:4px;">
            1 сағаттан кейін автоматты тазаланады (БД тазалығы)
          </div>
        </div>
        <button class="btn btn-sm btn-secondary" onclick="closeChatModal()">Жабу</button>
      </div>

      <!-- Messages container -->
      <div id="chatMessagesBody" style="flex:1; overflow-y:auto; padding:8px 4px; display:flex; flex-direction:column; gap:8px;">
        <div style="text-align:center; color:var(--text-muted); font-size:12px; margin-top:20px;">
          Хабарламалар жүктелуде...
        </div>
      </div>

      <!-- Footer input -->
      <form id="chatSendForm" onsubmit="handleSendChatMessage(event)" style="display:flex; gap:8px; border-top:1px solid var(--border-color); padding-top:12px; margin-top:8px;">
        <input type="text" id="chatInputText" class="form-control" placeholder="Хабарлама жазыңыз..." autocomplete="off" style="flex:1;">
        <button type="submit" class="btn btn-primary" style="white-space:nowrap;">Жіберу</button>
      </form>
    </div>
  `;

  modal.classList.add("active");
  setTimeout(() => {
    document.getElementById("chatInputText")?.focus();
  }, 100);
}

function closeChatModal() {
  const modal = document.getElementById("chatDialogModal");
  if (modal) modal.classList.remove("active");
  if (chatPollInterval) clearInterval(chatPollInterval);
  currentChatTarget = null;
}

async function loadChatMessages(currentUserId, targetUserId, autoScroll = true) {
  const body = document.getElementById("chatMessagesBody");
  if (!body) return;

  try {
    const messages = await Api.getChatMessages(currentUserId, targetUserId);
    if (!messages || messages.length === 0) {
      body.innerHTML = `
        <div style="text-align:center; color:var(--text-muted); font-size:12px; margin:auto;">
          Бұл сұхбатта әлі хабарлама жоқ.<br>Бірінші болып жазыңыз.
        </div>
      `;
      return;
    }

    body.innerHTML = messages.map(m => {
      const isMine = (m.sender_id === currentUserId);
      const align = isMine ? "flex-end" : "flex-start";
      const bg = isMine ? "var(--primary)" : "#e5e7eb";
      const textColor = isMine ? "#ffffff" : "var(--text-main)";

      return `
        <div style="display:flex; flex-direction:column; align-items:${align}; max-width:80%; align-self:${align};">
          <div style="font-size:10px; color:var(--text-muted); margin-bottom:2px; padding:0 4px;">
            ${escapeHtml(m.sender_name)} • ${m.created_at}
          </div>
          <div style="background:${bg}; color:${textColor}; padding:8px 12px; border-radius:8px; font-size:13px; line-height:1.4; word-break:break-word;">
            ${escapeHtml(m.text)}
          </div>
        </div>
      `;
    }).join("");

    if (autoScroll) {
      body.scrollTop = body.scrollHeight;
    }
  } catch (err) {
    console.error("Chat load error:", err);
  }
}

async function handleSendChatMessage(e) {
  e.preventDefault();
  const input = document.getElementById("chatInputText");
  const text = input.value.trim();
  if (!text || !currentChatTarget) return;

  const currentUser = getCurrentUserOrPrompt();
  if (!currentUser) return;

  input.value = "";
  try {
    await Api.sendChatMessage(currentUser.id, currentChatTarget.id, text);
    await loadChatMessages(currentUser.id, currentChatTarget.id, true);
  } catch (err) {
    alert("Хабарлама жіберілмеді: " + err.message);
  }
}

// -------------------------------------------------------------
// Official Printable Roster Sheet
// -------------------------------------------------------------
async function openPrintRoster(filterRole = "") {
  let modal = document.getElementById("printRosterModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "printRosterModal";
    modal.className = "modal-overlay";
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div class="modal-box" style="max-width: 900px; width: 95%; max-height: 90vh; overflow-y: auto;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;" class="no-print">
        <h3 style="font-size:16px;">Басып шығару парағы / Печатная ведомость</h3>
        <div style="display:flex; gap:8px;">
          <button class="btn btn-primary" onclick="window.print()">Басып шығару (Печать)</button>
          <button class="btn btn-secondary" onclick="document.getElementById('printRosterModal').classList.remove('active')">Жабу</button>
        </div>
      </div>

      <div id="printableArea" style="background:#ffffff; color:#000000; padding:20px; font-family: 'Times New Roman', Times, serif;">
        <div style="text-align:center; border-bottom:2px solid #000; padding-bottom:8px; margin-bottom:14px;">
          <div style="font-size:13px; font-weight:bold; text-transform:uppercase;">«Қазақстан Темір Жолы» ҰК» АҚ — Алматы дистанциясы (ПЧ-13)</div>
          <div style="font-size:15px; font-weight:bold; margin-top:4px;">КҮНДІЗГІ АУЫСЫМ БОЙЫНША ҚЫЗМЕТКЕРЛЕРДІҢ ҚАТЫСУ ЖӘНЕ КЕЛУ ТАБЕЛІ</div>
          <div style="font-size:12px; margin-top:2px;">Күні: ${new Date().toLocaleDateString('kk-KZ')} | Уақыты: ${new Date().toLocaleTimeString('kk-KZ')}</div>
        </div>

        <div id="printTableContainer">
          <div style="text-align:center; padding:20px; font-size:13px;">Деректер жүктелуде...</div>
        </div>

        <div style="display:flex; justify-content:space-between; margin-top:30px; font-size:12px;">
          <div>Дистанция бастығы / Инженер: __________________</div>
          <div>Ауысым кезекшісі (Диспетчер): __________________</div>
        </div>
      </div>
    </div>
  `;

  modal.classList.add("active");

  try {
    const data = await Api.getRoster({ role: filterRole });
    const container = document.getElementById("printTableContainer");
    if (!data.records || data.records.length === 0) {
      container.innerHTML = `<div style="text-align:center; padding:20px;">Жазбалар табылмады.</div>`;
      return;
    }

    container.innerHTML = `
      <table style="width:100%; border-collapse:collapse; font-size:11px; margin-top:8px;" border="1">
        <thead>
          <tr style="background:#f0f0f0;">
            <th style="padding:5px;">№</th>
            <th style="padding:5px;">Бөлім / Часть</th>
            <th style="padding:5px;">Табельдік №</th>
            <th style="padding:5px;">ЖСН / ИИН</th>
            <th style="padding:5px;">Аты-жөні (ФИО)</th>
            <th style="padding:5px;">Лауазымы</th>
            <th style="padding:5px;">Келгені</th>
            <th style="padding:5px;">Кеткені</th>
            <th style="padding:5px;">Мәртебесі</th>
            <th style="padding:5px;">Қолы</th>
          </tr>
        </thead>
        <tbody>
          ${data.records.map((r, i) => `
            <tr>
              <td style="padding:4px; text-align:center;">${i + 1}</td>
              <td style="padding:4px; font-size:10px;">${escapeHtml(r.organization || 'ПЧ-13')}</td>
              <td style="padding:4px; text-align:center;">${escapeHtml(r.emp_num)}</td>
              <td style="padding:4px; text-align:center; font-family:monospace;">${escapeHtml(r.iin || '—')}</td>
              <td style="padding:4px; font-weight:bold;">${escapeHtml(r.full_name)}</td>
              <td style="padding:4px;">${escapeHtml(r.position)}</td>
              <td style="padding:4px; text-align:center;">${r.check_in_time}</td>
              <td style="padding:4px; text-align:center;">${r.check_out_time}</td>
              <td style="padding:4px; text-align:center; font-weight:bold;">
                ${r.status === 'PRESENT' ? 'КЕЛДІ' : (r.status === 'LEAVE' ? 'ДЕМАЛЫС' : 'КЕЛМЕГЕН')}
              </td>
              <td style="padding:4px; text-align:center; width:60px;"></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
      <div style="margin-top:10px; font-size:11px; font-weight:bold;">
        Барлығы: ${data.total} | Қатысқаны: ${data.present_count} | Келмегені: ${data.absent_count} | Демалыста/Ауруханада: ${data.leave_count}
      </div>
    `;
  } catch(err) {
    document.getElementById("printTableContainer").innerHTML = `<div style="color:red; padding:10px;">Қате: ${err.message}</div>`;
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
