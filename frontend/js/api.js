// Digital Temirzhol — Client API Service & Utilities
// Deploy-aware base URL resolution (Vercel + Render friendly):
//   1) window.DT_API_BASE from js/config.js (set to Render backend URL on Vercel)
//   2) localStorage "dt_api_base" manual override
//   3) same-origin "" when backend serves frontend (Render monolith / port 8000)
//   4) local dev fallback http://127.0.0.1:8000
function resolveApiBase() {
  // 1) Explicit deploy config (Vercel -> Render backend URL)
  if (typeof window !== "undefined" && window.DT_API_BASE) {
    return String(window.DT_API_BASE).replace(/\/$/, "");
  }
  // 2) Manual browser override: localStorage.setItem("dt_api_base", "https://xxx.onrender.com")
  try {
    const stored = localStorage.getItem("dt_api_base");
    if (stored) return stored.replace(/\/$/, "");
  } catch (e) { /* ignore */ }
  if (typeof window !== "undefined") {
    const host = window.location.hostname || "";
    // 3) Local development (Live Server / file://)
    if (host === "127.0.0.1" || host === "localhost" || window.location.protocol === "file:") {
      return window.location.port === "8000" ? "" : "http://127.0.0.1:8000";
    }
    // 4) Any hosted origin (Render monolith or Vercel with DT_API_BASE=""):
    //    try same-origin first — works when FastAPI serves /frontend itself.
    return "";
  }
  return "http://127.0.0.1:8000";
}
const API_BASE = resolveApiBase();

const Api = {
  BASE_URL: API_BASE,
  getFileUrl(path) {
    if (!path) return "";
    if (path.startsWith("http://") || path.startsWith("https://") || path.startsWith("data:")) {
      return path;
    }
    const cleanPath = path.startsWith("/") ? path : `/${path}`;
    return `${API_BASE}${encodeURI(decodeURI(cleanPath))}`;
  },
  getToken() {
    return localStorage.getItem("smartrail_token");
  },
  getUser() {
    const u = localStorage.getItem("smartrail_user");
    return u ? JSON.parse(u) : null;
  },
  setUser(user, token) {
    localStorage.setItem("smartrail_user", JSON.stringify(user));
    if (token) localStorage.setItem("smartrail_token", token);
  },
  logout() {
    localStorage.removeItem("smartrail_user");
    localStorage.removeItem("smartrail_token");
    window.location.href = "login.html";
  },

  async request(endpoint, options = {}) {
    const headers = options.headers || {};
    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Қате орын алды");
      }
      return data;
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  },

  // Auth
  login(username, password) {
    return this.request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
  },
  register(userData) {
    return this.request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(userData)
    });
  },
  getPendingUsers() {
    return this.request("/api/auth/pending-users");
  },
  approveUser(userId, action = "APPROVE") {
    return this.request("/api/auth/approve-user", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, action })
    });
  },
  requestPasswordReset(identifier) {
    return this.request("/api/auth/reset-password/request", {
      method: "POST",
      body: JSON.stringify({ identifier })
    });
  },
  confirmPasswordReset(identifier, code, newPassword) {
    return this.request("/api/auth/reset-password/confirm", {
      method: "POST",
      body: JSON.stringify({ identifier, code, new_password: newPassword })
    });
  },
  getUsers(role) {
    const query = role ? `?role=${role}` : "";
    return this.request(`/api/auth/users${query}`);
  },

  // Attendance
  checkIn(payload) {
    return this.request("/api/attendance/check-in", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  getRecentAttendance(limit = 20) {
    const q = limit ? `?limit=${encodeURIComponent(limit)}` : "";
    return this.request(`/api/attendance/recent${q}`);
  },
  getTimesheet(dateStr) {
    const query = dateStr ? `?target_date=${dateStr}` : "";
    return this.request(`/api/attendance/timesheet${query}`);
  },
  getJournal(dateStr, checkpointId = null) {
    const q = new URLSearchParams();
    if (dateStr) q.append("target_date", dateStr);
    if (checkpointId) q.append("checkpoint_id", checkpointId);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return this.request(`/api/attendance/journal${qs}`);
  },
  downloadTimesheetCsv(dateStr) {
    const q = dateStr ? `?target_date=${encodeURIComponent(dateStr)}` : "";
    window.open(`${API_BASE}/api/attendance/export-csv${q}`, "_blank");
  },

  // Naryad
  getNaryadRef() {
    return this.request("/api/naryad/reference");
  },
  createNaryad(payload) {
    return this.request("/api/naryad/create", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  getNaryads(status) {
    const query = status ? `?status=${status}` : "";
    return this.request(`/api/naryad/list${query}`);
  },
  approveBossNaryad(naryadId) {
    return this.request("/api/naryad/approve-boss", {
      method: "POST",
      body: JSON.stringify({ naryad_id: naryadId })
    });
  },
  permitDispatcherNaryad(naryadId) {
    return this.request("/api/naryad/permit-dispatcher", {
      method: "POST",
      body: JSON.stringify({ naryad_id: naryadId })
    });
  },
  completeNaryad(naryadId, actualTime) {
    return this.request("/api/naryad/complete", {
      method: "POST",
      body: JSON.stringify({ naryad_id: naryadId, actual_end_time: actualTime })
    });
  },

  // Leaves
  createLeave(payload) {
    return this.request("/api/leaves/create", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  getLeaves(userId) {
    const query = userId ? `?user_id=${userId}` : "";
    return this.request(`/api/leaves/list${query}`);
  },
  approveLeave(leaveId, status = "APPROVED") {
    return this.request("/api/leaves/approve", {
      method: "POST",
      body: JSON.stringify({ leave_id: leaveId, status })
    });
  },

  // Kiosk & Notifications
  getKioskToken(checkpointId = null) {
    const q = checkpointId ? `?checkpoint_id=${encodeURIComponent(checkpointId)}` : "";
    return this.request(`/api/kiosk/token${q}`);
  },
  getNotifications(role) {
    return this.request(`/api/kiosk/notifications?role=${role || "BOSS"}`);
  },

  // Audit journal (BOSS)
  getAuditActions() {
    return this.request("/api/audit/actions");
  },
  getAudit(action = "", limit = 100) {
    const q = new URLSearchParams();
    if (action) q.append("action", action);
    if (limit) q.append("limit", limit);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return this.request(`/api/audit/list${qs}`);
  },

  // Work points (dispatcher-managed checkpoints & sections)
  getWorkPoints(kind = "", activeOnly = false) {
    const q = new URLSearchParams();
    if (kind) q.append("kind", kind);
    if (activeOnly) q.append("active_only", "true");
    const qs = q.toString() ? `?${q.toString()}` : "";
    return this.request(`/api/workpoints${qs}`);
  },
  createWorkPoint(payload) {
    return this.request("/api/workpoints", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  updateWorkPoint(id, payload) {
    return this.request(`/api/workpoints/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
  },
  deleteWorkPoint(id) {
    return this.request(`/api/workpoints/${id}`, { method: "DELETE" });
  },
  // Roster (Live presence: who is present, who is absent)
  getRoster(params = {}) {
    const q = new URLSearchParams();
    if (params.role) q.append("role", params.role);
    if (params.master_id) q.append("master_id", params.master_id);
    if (params.query) q.append("query", params.query);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return this.request(`/api/attendance/roster${qs}`);
  },

  // Chat & Direct Messages (Cleaned after 1 hour)
  sendChatMessage(senderId, receiverId, text) {
    return this.request("/api/chat/send", {
      method: "POST",
      body: JSON.stringify({ sender_id: senderId, receiver_id: receiverId, text })
    });
  },
  getChatMessages(user1Id, user2Id) {
    return this.request(`/api/chat/messages?user1_id=${user1Id}&user2_id=${user2Id}`);
  },
  getChatUsers(query = "", role = "") {
    const q = new URLSearchParams();
    if (query) q.append("query", query);
    if (role) q.append("role", role);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return this.request(`/api/chat/users${qs}`);
  }
};

// UI Notification Toast
function showToast(message, type = "success") {
  let toastContainer = document.getElementById("toast-container");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toast-container";
    toastContainer.style.cssText = "position:fixed; bottom:24px; right:24px; z-index:9999; display:flex; flex-direction:column; gap:10px;";
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement("div");
  const bg = type === "success" ? "#065f46" : (type === "danger" ? "#991b1b" : "#1e3a8a");
  const border = type === "success" ? "#10b981" : (type === "danger" ? "#ef4444" : "#38bdf8");
  
  toast.style.cssText = `background:${bg}; border:1px solid ${border}; color:#fff; padding:12px 20px; border-radius:8px; box-shadow:0 8px 24px rgba(0,0,0,0.4); font-size:14px; font-weight:600; display:flex; align-items:center; gap:8px; animation:fadeIn 0.3s ease;`;
  toast.innerHTML = message;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.4s ease";
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}
