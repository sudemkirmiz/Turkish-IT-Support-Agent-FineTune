// ========================================
// CONFIGURATION
// ========================================
const API_CANDIDATE_URLS = ["http://127.0.0.1:8000", "http://127.0.0.1:8001"];
let apiBaseUrl = localStorage.getItem("itSupportApiBaseUrl") || API_CANDIDATE_URLS[0];
const REQUEST_TIMEOUT_MS = 300000; // 5 min - model loading takes time on first run
const CHAT_HISTORY_KEY = "itSupportChatHistory";
const ACTIVE_SESSION_KEY = "itSupportSessionId";
const CHAT_SESSIONS_KEY = "itSupportLocalSessions";
const CHAT_OS_STORAGE_KEY = "itSupportChatOS";
const MAX_CHAT_MESSAGES = 50;

// Test cases for evaluation
const testCases = [
  { message: "Wi-Fi bağlı ama internete giremiyorum.", os: "Windows", expectedCategory: "network_issue", expectedPriority: "medium", expectedRisk: "safe" },
  { message: "Bilgisayarım çok yavaşladı.", os: "Windows", expectedCategory: "performance_issue", expectedPriority: "medium", expectedRisk: "safe" },
  { message: "Laptop çok ısınıyor, fan çok sesli çalışıyor ve cihaz kendi kendine kapanıyor.", os: "Windows", expectedCategory: "hardware_issue", expectedPriority: "high", expectedRisk: "warning" },
  { message: "Chrome sürekli çöküyor.", os: "Windows", expectedCategory: "software_issue", expectedPriority: "medium", expectedRisk: "safe" },
  { message: "Windows güncellemesinden sonra ses gelmiyor.", os: "Windows", expectedCategory: "os_error", expectedPriority: "medium", expectedRisk: "warning" },
  { message: "Diskim dolu görünüyor ama neyi sileceğimi bilmiyorum.", os: "Windows", expectedCategory: "storage_issue", expectedPriority: "medium", expectedRisk: "warning" },
  { message: "Ekran kartı driver güncellemesinden sonra oyun açılmıyor.", os: "Windows", expectedCategory: "driver_issue", expectedPriority: "medium", expectedRisk: "warning" },
  { message: "Bilgisayarımda virüs olabilir.", os: "Windows", expectedCategory: "security_issue", expectedPriority: "high", expectedRisk: "warning" },
  { message: "Bluetooth kulaklığım bağlanıyor ama ses gelmiyor.", os: "Windows", expectedCategory: "peripheral_issue", expectedPriority: "medium", expectedRisk: "safe" },
  { message: "Ne olduğunu bilmiyorum ama bilgisayar garip davranıyor.", os: "Unknown", expectedCategory: "unknown_issue", expectedPriority: "low", expectedRisk: "safe" },
  { message: "Program kurarken hata alıyorum.", os: "Windows", expectedCategory: "software_issue", expectedPriority: "medium", expectedRisk: "safe" },
  { message: "Yazıcım bilgisayarda görünmüyor.", os: "Windows", expectedCategory: "peripheral_issue", expectedPriority: "medium", expectedRisk: "safe" },
  { message: "Harici diskim görünmüyor.", os: "Windows", expectedCategory: "storage_issue", expectedPriority: "medium", expectedRisk: "warning" },
  { message: "Bilgisayarım açılıyor ama ekran siyah kalıyor.", os: "Windows", expectedCategory: "hardware_issue", expectedPriority: "high", expectedRisk: "warning" },
  { message: "DNS hatası alıyorum.", os: "Windows", expectedCategory: "network_issue", expectedPriority: "medium", expectedRisk: "safe" },
];

const quickExamples = [
  { label: "Wi-Fi", message: "Wi-Fi bağlı ama internete giremiyorum." },
  { label: "Performans", message: "Bilgisayarım çok yavaşladı." },
  { label: "Tarayıcı", message: "Chrome sürekli çöküyor." },
  { label: "Web Hatası", message: "Bazı sitelerde 409 hata kodu alıyorum." },
];

// ========================================
// STATE MANAGEMENT
// ========================================
let chatMessages = [];
let currentSessionId = localStorage.getItem(ACTIVE_SESSION_KEY) || "";
let evaluationResults = [];
let currentPage = "assistantPage";
let isAnalyzing = false;
let isEvaluating = false;
let isAssistantThinking = false;
let currentAnalysisAbortController = null;
let modelReady = false; // Track if model has been loaded once
let speechRecognition = null;
let isListening = false;
let analysisStartedAt = 0;
let analysisTimerId = null;

// ========================================
// DOM ELEMENTS
// ========================================
function getElements() {
  return {
    navItems: document.querySelectorAll(".nav-item"),
    statusDot: document.querySelector("#sidebarStatus .status-dot"),
    statusText: document.querySelector("#sidebarStatus .status-text"),
    assistantPage: document.querySelector("#assistantPage"),
    evaluationPage: document.querySelector("#evaluationPage"),
    statusPage: document.querySelector("#statusPage"),
    analyzeForm: document.querySelector("#analyzeForm"),
    messageInput: document.querySelector("#message"),
    osInput: document.querySelector("#os"),
    submitButton: document.querySelector("#submitButton"),
    chatMessages: document.querySelector("#chatMessages"),
    chatEmptyState: document.querySelector("#chatEmptyState"),
    examples: document.querySelector("#examples"),
    clearChatButton: document.querySelector("#clearChatButton"),
    deleteChatButton: document.querySelector("#deleteChatButton"),
    clearAllChatsButton: document.querySelector("#clearAllChatsButton"),
    newChatButton: document.querySelector("#newChatButton"),
    voiceButton: document.querySelector("#voiceButton"),
    sessionList: document.querySelector("#sessionList"),
    toast: document.querySelector("#toast"),
    runQuickTestsButton: document.querySelector("#runQuickTestsButton"),
    runAllTestsButton: document.querySelector("#runAllTestsButton"),
    clearTestsButton: document.querySelector("#clearTestsButton"),
    testStatus: document.querySelector("#testStatus"),
    testResultsBody: document.querySelector("#testResultsBody"),
    testCases: document.querySelector("#testCases"),
    totalTestsMetric: document.querySelector("#totalTestsMetric"),
    passedTestsMetric: document.querySelector("#passedTestsMetric"),
    partialTestsMetric: document.querySelector("#partialTestsMetric"),
    failedTestsMetric: document.querySelector("#failedTestsMetric"),
    categoryAccuracyMetric: document.querySelector("#categoryAccuracyMetric"),
    priorityAccuracyMetric: document.querySelector("#priorityAccuracyMetric"),
    riskAccuracyMetric: document.querySelector("#riskAccuracyMetric"),
    backendStatusDot: document.querySelector("#backendStatusDot"),
    backendStatusText: document.querySelector("#backendStatusText"),
    apiUrl: document.querySelector("#apiUrl"),
    modelName: document.querySelector("#modelName"),
  };
}

// ========================================
// PAGE NAVIGATION
// ========================================
function switchPage(pageId) {
  const els = getElements();
  els.assistantPage.classList.remove("active");
  els.evaluationPage.classList.remove("active");
  els.statusPage.classList.remove("active");
  els.navItems.forEach((item) => item.classList.remove("active"));

  if (pageId === "assistantPage") {
    els.assistantPage.classList.add("active");
    scrollChatToBottom();
  } else if (pageId === "evaluationPage") {
    els.evaluationPage.classList.add("active");
  } else if (pageId === "statusPage") {
    els.statusPage.classList.add("active");
    checkHealth();
  }

  const activeNav = document.querySelector(`[data-page="${pageId}"]`);
  if (activeNav) activeNav.classList.add("active");
  currentPage = pageId;
}

function initializeNavigation() {
  const els = getElements();
  els.navItems.forEach((item) => {
    item.addEventListener("click", () => switchPage(item.getAttribute("data-page")));
  });
}

// ========================================
// HEALTH & API
// ========================================
function updateHealthStatus(online) {
  const els = getElements();
  document.querySelectorAll(".status-dot").forEach((dot) => {
    dot.classList.toggle("online", online);
    dot.classList.toggle("offline", !online);
  });

  document.querySelectorAll(".status-text").forEach((text) => {
    text.textContent = online ? "Backend çalışıyor" : "Backend kapalı";
  });

  if (els.backendStatusDot) {
    els.backendStatusDot.classList.toggle("online", online);
    els.backendStatusDot.classList.toggle("offline", !online);
  }
  if (els.backendStatusText) {
    els.backendStatusText.textContent = online ? "✓ Çalışıyor" : "✗ Kapalı";
  }
}

async function checkHealth() {
  const candidates = [apiBaseUrl, ...API_CANDIDATE_URLS].filter((url, index, list) => list.indexOf(url) === index);

  for (const candidateUrl of candidates) {
    try {
      const response = await fetch(`${candidateUrl}/health`, {
        signal: AbortSignal.timeout(2500),
      });
      if (!response.ok) throw new Error("Backend unreachable");

      apiBaseUrl = candidateUrl;
      localStorage.setItem("itSupportApiBaseUrl", apiBaseUrl);
      const els = getElements();
      if (els.apiUrl) els.apiUrl.textContent = apiBaseUrl;
      updateHealthStatus(true);
      return true;
    } catch (error) {
      // Try the next known backend port.
    }
  }

  updateHealthStatus(false);
  return false;
}

async function requestAnalysis(message, os, controller = new AbortController(), options = {}) {
  const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    await checkHealth();
    const response = await fetch(`${apiBaseUrl}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, os, session_id: options.sessionId || currentSessionId || undefined }),
      signal: controller.signal,
    });

    let data = {};
    try {
      data = await response.json();
    } catch (error) {
      data = {};
    }

    if (!response.ok) {
      const error = new Error(data.detail || "Analiz hatası");
      error.status = response.status;
      error.errorType = data.error_type;
      error.rawPreview = data.raw_preview;
      error.reasons = Array.isArray(data.reasons) ? data.reasons : [];
      throw error;
    }
    if (Array.isArray(data.advisory_warnings) && data.advisory_warnings.length > 0) {
      console.warn("Model advisory warnings", data.advisory_warnings);
    }
    return data;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

// ========================================
// CHAT STATE
// ========================================
function loadChatHistory() {
  try {
    const rawHistory = localStorage.getItem(CHAT_HISTORY_KEY);
    const parsedHistory = rawHistory ? JSON.parse(rawHistory) : [];
    chatMessages = Array.isArray(parsedHistory) ? parsedHistory.filter(isValidChatMessage).slice(-MAX_CHAT_MESSAGES) : [];
  } catch (error) {
    chatMessages = [];
  }
}

function saveChatHistory() {
  chatMessages = chatMessages.slice(-MAX_CHAT_MESSAGES);
  localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(chatMessages));
  saveLocalSession();
  renderSessionList();
}

function isValidChatMessage(message) {
  return Boolean(
    message &&
      typeof message.id === "string" &&
      ["user", "assistant", "system"].includes(message.role) &&
      typeof message.content === "string" &&
      typeof message.createdAt === "string",
  );
}

function createUserMessage(content, os) {
  return {
    id: createMessageId(),
    role: "user",
    content,
    os,
    createdAt: new Date().toISOString(),
  };
}

function createAssistantMessage(result) {
  return {
    id: createMessageId(),
    role: "assistant",
    content: formatAssistantChatResponse(result),
    result,
    createdAt: new Date().toISOString(),
  };
}

function createErrorMessage(content) {
  return {
    id: createMessageId(),
    role: "system",
    content,
    createdAt: new Date().toISOString(),
  };
}

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function addChatMessage(message) {
  chatMessages.push(message);
  saveChatHistory();
  renderChat();
}

function clearChatHistory() {
  if (chatMessages.length > 0) saveLocalSession();
  chatMessages = [];
  currentSessionId = "";
  localStorage.removeItem(CHAT_HISTORY_KEY);
  localStorage.removeItem(ACTIVE_SESSION_KEY);
  renderChat();
  renderSessionList();
}

function deleteCurrentChat() {
  if (!currentSessionId && chatMessages.length === 0) {
    showToast("Silinecek sohbet yok");
    return;
  }
  if (!window.confirm("Bu sohbet silinsin mi?")) return;

  const deletedSessionId = currentSessionId || "unsaved-chat";
  if (currentSessionId) deleteStoredSession(currentSessionId);
  chatMessages = [];
  currentSessionId = "";
  localStorage.removeItem(CHAT_HISTORY_KEY);
  localStorage.removeItem(ACTIVE_SESSION_KEY);
  console.info("deleted session_id", deletedSessionId);
  console.info("cleared localStorage keys", [CHAT_HISTORY_KEY, ACTIVE_SESSION_KEY]);
  renderChat();
  renderSessionList();
  showToast("Sohbet silindi");
}

function deleteStoredSession(sessionId) {
  const sessions = loadLocalSessions();
  delete sessions[sessionId];
  localStorage.setItem(CHAT_SESSIONS_KEY, JSON.stringify(sessions));
}

function deleteSessionFromList(sessionId) {
  if (!window.confirm("Bu sohbet silinsin mi?")) return;

  deleteStoredSession(sessionId);
  console.info("deleted session_id", sessionId);
  if (sessionId === currentSessionId) {
    chatMessages = [];
    currentSessionId = "";
    localStorage.removeItem(CHAT_HISTORY_KEY);
    localStorage.removeItem(ACTIVE_SESSION_KEY);
    console.info("cleared localStorage keys", [CHAT_HISTORY_KEY, ACTIVE_SESSION_KEY]);
    renderChat();
  }
  renderSessionList();
  showToast("Sohbet silindi");
}

function clearAllChats() {
  if (!window.confirm("Tüm sohbet geçmişi silinsin mi?")) return;

  chatMessages = [];
  currentSessionId = "";
  localStorage.removeItem(CHAT_HISTORY_KEY);
  localStorage.removeItem(ACTIVE_SESSION_KEY);
  localStorage.removeItem(CHAT_SESSIONS_KEY);
  console.info("deleted session_id", "all");
  console.info("cleared localStorage keys", [CHAT_HISTORY_KEY, ACTIVE_SESSION_KEY, CHAT_SESSIONS_KEY]);
  renderChat();
  renderSessionList();
  showToast("Tüm sohbet geçmişi temizlendi");
}

function saveLocalSession() {
  if (!currentSessionId || chatMessages.length === 0) return;
  const sessions = loadLocalSessions();
  const firstUser = chatMessages.find((message) => message.role === "user");
  sessions[currentSessionId] = {
    session_id: currentSessionId,
    title: firstUser ? firstUser.content.slice(0, 60) : "Sohbet",
    updatedAt: new Date().toISOString(),
    messages: chatMessages,
  };
  localStorage.setItem(CHAT_SESSIONS_KEY, JSON.stringify(sessions));
}

function loadLocalSessions() {
  try {
    return JSON.parse(localStorage.getItem(CHAT_SESSIONS_KEY) || "{}");
  } catch (error) {
    return {};
  }
}

function renderSessionList() {
  const els = getElements();
  if (!els.sessionList) return;
  const sessions = Object.values(loadLocalSessions()).sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
  els.sessionList.innerHTML = "";

  if (sessions.length === 0) {
    const empty = document.createElement("div");
    empty.className = "session-empty";
    empty.textContent = "Henüz sohbet yok";
    els.sessionList.appendChild(empty);
    return;
  }

  sessions.slice(0, 12).forEach((session) => {
    const row = document.createElement("div");
    row.className = `session-row ${session.session_id === currentSessionId ? "active" : ""}`;
    const lastAssistant = [...(session.messages || [])].reverse().find((message) => message.role === "assistant" && message.result);
    const category = lastAssistant?.result?.category || "sohbet";
    const messageCount = Array.isArray(session.messages) ? session.messages.length : 0;

    const button = document.createElement("button");
    button.type = "button";
    button.className = "session-item";
    button.innerHTML = `<span>${escapeHtml(session.title || "Sohbet")}</span><small>${formatSessionDate(session.updatedAt)} · ${messageCount} mesaj</small><em>${escapeHtml(category)}</em>`;
    button.addEventListener("click", () => loadLocalSession(session.session_id));

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "session-delete";
    deleteButton.textContent = "Sil";
    deleteButton.setAttribute("aria-label", `${session.title || "Sohbet"} sohbetini sil`);
    deleteButton.addEventListener("click", (event) => {
      event.stopPropagation();
      deleteSessionFromList(session.session_id);
    });

    row.append(button, deleteButton);
    els.sessionList.appendChild(row);
  });
}

function loadLocalSession(sessionId) {
  const session = loadLocalSessions()[sessionId];
  if (!session) return;
  currentSessionId = sessionId;
  chatMessages = Array.isArray(session.messages) ? session.messages.filter(isValidChatMessage).slice(-MAX_CHAT_MESSAGES) : [];
  localStorage.setItem(ACTIVE_SESSION_KEY, currentSessionId);
  localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(chatMessages));
  renderChat();
  renderSessionList();
  switchPage("assistantPage");
}

function formatSessionDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString("tr-TR", { day: "2-digit", month: "short" });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[char]));
}

function renderChat() {
  const els = getElements();
  if (!els.chatMessages || !els.chatEmptyState) return;

  els.chatMessages.innerHTML = "";
  els.chatEmptyState.hidden = chatMessages.length > 0 || isAssistantThinking;

  chatMessages.forEach((message) => {
    els.chatMessages.appendChild(createChatMessageElement(message));
  });

  if (isAssistantThinking) {
    els.chatMessages.appendChild(createThinkingMessageElement());
  }

  scrollChatToBottom();
}

function startAnalysisTimer() {
  analysisStartedAt = Date.now();
  window.clearInterval(analysisTimerId);
  analysisTimerId = window.setInterval(() => {
    if (isAssistantThinking) renderChat();
  }, 1000);
}

function stopAnalysisTimer() {
  window.clearInterval(analysisTimerId);
  analysisTimerId = null;
  analysisStartedAt = 0;
}

function createChatMessageElement(message) {
  const wrapper = document.createElement("article");
  wrapper.className = `chat-message ${message.role}`;

  const bubble = document.createElement("div");
  bubble.className = "chat-bubble";

  if (message.role === "assistant" && message.result) {
    bubble.appendChild(createAnalysisResultElement(message.result));
  } else {
    const paragraph = document.createElement("p");
    paragraph.textContent = message.content;
    bubble.appendChild(paragraph);
  }

  const meta = document.createElement("div");
  meta.className = "chat-meta";
  meta.textContent = message.role === "user" ? `${message.os || "Bilinmiyor"} • ${formatMessageTime(message.createdAt)}` : formatMessageTime(message.createdAt);
  bubble.appendChild(meta);
  wrapper.appendChild(bubble);
  return wrapper;
}

function createAnalysisResultElement(result) {
  const container = document.createElement("div");
  container.className = "assistant-response";

  if (result.assistant_message) {
    const message = document.createElement("p");
    message.className = "assistant-intro assistant-message-text";
    message.textContent = result.assistant_message;
    container.appendChild(message);
    container.appendChild(createStructuredResponseSections(result, false));
    container.appendChild(createTechnicalDetailsElement(result));
    return container;
  }

  console.warn("assistant_message missing; rendering structured JSON fields instead", result);

  container.appendChild(createStructuredResponseSections(result, true));
  container.appendChild(createTechnicalDetailsElement(result));

  return container;
}

function createStructuredResponseSections(result, includeSummary) {
  const fallback = document.createElement("div");
  fallback.className = "assistant-fallback-card";

  if (includeSummary && result.summary) {
    const intro = document.createElement("p");
    intro.className = "assistant-intro";
    intro.textContent = result.summary;
    fallback.appendChild(intro);
  }

  fallback.appendChild(createChatSection("Olası nedenler", result.possible_causes, false));
  fallback.appendChild(createChatSection("Denenecek adımlar", result.solution_steps, true));
  fallback.appendChild(createChatSection("Netleştirelim", result.questions, false));
  return fallback;
}

function createTechnicalDetailsElement(result) {
  const details = document.createElement("details");
  details.className = "technical-details";

  const summary = document.createElement("summary");
  summary.appendChild(createTechnicalPills(result));
  details.appendChild(summary);

  const meta = document.createElement("dl");
  meta.className = "technical-meta";
  const items = [
    ["category", result.category],
    ["priority", result.priority],
    ["risk_level", result.risk_level],
    ["summary", result.summary],
    ["possible_causes", Array.isArray(result.possible_causes) ? result.possible_causes.join("; ") : "-"],
    ["questions", Array.isArray(result.questions) ? result.questions.join("; ") : "-"],
    ["solution_steps", Array.isArray(result.solution_steps) ? result.solution_steps.join("; ") : "-"],
    ["mode", result.mode],
    ["model_call_count", Number.isFinite(result.model_call_count) ? String(result.model_call_count) : "-"],
    ["model_inference_ms", Number.isFinite(result.model_inference_ms) ? `${result.model_inference_ms}ms` : "-"],
    ["advisory_warnings", Array.isArray(result.advisory_warnings) ? result.advisory_warnings.join("; ") : "-"],
  ];
  items.forEach(([label, value]) => {
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = value || "-";
    meta.append(term, description);
  });
  details.appendChild(meta);
  return details;
}

function createTechnicalPills(result) {
  const wrapper = document.createElement("span");
  wrapper.className = "technical-summary-pills";
  const pills = [
    result.category,
    result.priority,
    result.risk_level,
    Number.isFinite(result.model_call_count) ? `${result.model_call_count} model çağrısı` : null,
  ].filter(Boolean);
  pills.forEach((pill) => {
    const item = document.createElement("span");
    item.className = "technical-pill";
    item.textContent = pill;
    wrapper.appendChild(item);
  });
  return wrapper;
}

function createChatSection(title, items, ordered) {
  const safeItems = Array.isArray(items) ? items.filter(Boolean) : [];
  if (safeItems.length === 0) return document.createDocumentFragment();

  const section = document.createElement("section");
  section.className = "assistant-section";
  const heading = document.createElement("h4");
  heading.textContent = title;
  const list = document.createElement(ordered ? "ol" : "ul");

  safeItems.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  });

  section.append(heading, list);
  return section;
}

function createThinkingMessageElement() {
  const wrapper = document.createElement("article");
  wrapper.className = "chat-message assistant thinking";

  const bubble = document.createElement("div");
  bubble.className = "chat-bubble thinking-bubble";

  const text = document.createElement("span");
  text.textContent = currentSessionId && chatMessages.length > 1 ? "Bağlamla yanıt hazırlanıyor" : modelReady ? "Analiz ediliyor" : "Model yükleniyor, analiz ediliyor";

  const timer = document.createElement("span");
  timer.className = "thinking-timer";
  timer.textContent = analysisStartedAt ? `${Math.floor((Date.now() - analysisStartedAt) / 1000)} sn` : "0 sn";

  const dots = document.createElement("span");
  dots.className = "typing-dots";
  dots.setAttribute("aria-hidden", "true");
  dots.innerHTML = "<span></span><span></span><span></span>";

  bubble.append(text, timer, dots);
  wrapper.appendChild(bubble);
  return wrapper;
}

function formatAssistantChatResponse(result) {
  const lines = [];
  lines.push(result.summary || "Problemi analiz ettim.");

  if (Array.isArray(result.possible_causes) && result.possible_causes.length > 0) {
    lines.push("", "Olası nedenler:");
    result.possible_causes.forEach((cause) => lines.push(`- ${cause}`));
  }

  if (Array.isArray(result.solution_steps) && result.solution_steps.length > 0) {
    lines.push("", "Şimdi şu adımları deneyin:");
    result.solution_steps.forEach((step, index) => lines.push(`${index + 1}. ${step}`));
  }

  if (Array.isArray(result.questions) && result.questions.length > 0) {
    lines.push("", "Devam edebilmem için şunları da söyleyin:");
    result.questions.forEach((question) => lines.push(`- ${question}`));
  }

  return lines.join("\n");
}

function formatMessageTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
}

function scrollChatToBottom() {
  const els = getElements();
  if (!els.chatMessages) return;
  requestAnimationFrame(() => {
    els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
  });
}

function showToast(message) {
  const els = getElements();
  if (!els.toast) return;
  els.toast.textContent = message;
  els.toast.hidden = false;
  window.clearTimeout(showToast.timeoutId);
  showToast.timeoutId = window.setTimeout(() => {
    els.toast.hidden = true;
  }, 2200);
}

// ========================================
// CHAT ANALYSIS
// ========================================
async function analyze(event) {
  event.preventDefault();
  const els = getElements();
  const message = els.messageInput.value.trim();
  const os = els.osInput.value;

  if (!message || isAnalyzing) return;

  addChatMessage(createUserMessage(message, os));
  els.messageInput.value = "";
  localStorage.setItem(CHAT_OS_STORAGE_KEY, os);
  isAssistantThinking = true;
  startAnalysisTimer();
  setChatSubmitting(true);
  renderChat();

  const controller = new AbortController();
  currentAnalysisAbortController = controller;
  isAnalyzing = true;

  try {
    const data = await requestAnalysis(message, os, controller, { sessionId: currentSessionId });
    if (data.session_id) {
      currentSessionId = data.session_id;
      localStorage.setItem(ACTIVE_SESSION_KEY, currentSessionId);
    }
    modelReady = true;
    isAssistantThinking = false;
    stopAnalysisTimer();
    addChatMessage(createAssistantMessage(data));
  } catch (error) {
    isAssistantThinking = false;
    stopAnalysisTimer();
    if (error.name === "AbortError") {
      addChatMessage(createErrorMessage("İşlem iptal edildi."));
    } else {
      addChatMessage(createErrorMessage(getFriendlyErrorMessage(error)));
    }
  } finally {
    isAnalyzing = false;
    isAssistantThinking = false;
    stopAnalysisTimer();
    setChatSubmitting(false);
    if (currentAnalysisAbortController === controller) {
      currentAnalysisAbortController = null;
    }
    els.messageInput.focus();
  }
}

function setChatSubmitting(submitting) {
  const els = getElements();
  els.submitButton.disabled = submitting;
  els.submitButton.textContent = submitting ? "Yanıt hazırlanıyor..." : "Gönder";
}

function resizeMessageInput() {
  const els = getElements();
  if (!els.messageInput) return;
  els.messageInput.style.height = "auto";
  els.messageInput.style.height = `${Math.min(118, Math.max(46, els.messageInput.scrollHeight))}px`;
}

function getFriendlyErrorMessage(error) {
  if (error.status === 502 && ["invalid_model_json", "invalid_model_semantics"].includes(error.errorType)) {
    if (error.errorType === "invalid_model_semantics") {
      console.warn("Model semantic validation reasons:", error.reasons || []);
      return "Model çıktısı kalite kontrolünden geçemedi. Backend loglarını kontrol edin.";
    }
    return "Model çıktısı doğrulanamadı. Backend loglarını kontrol edin.";
  }
  if (error.status === 502) {
    return "Model cevabı işlenemedi. Lütfen problemi biraz daha açık ifade ederek tekrar deneyin.";
  }
  if (error.name === "TypeError" || error.message === "Failed to fetch") {
    return "Backend'e ulaşılamadı. Lütfen sunucunun çalıştığını kontrol edin.";
  }
  return error.message || "Analiz sırasında beklenmeyen bir hata oluştu.";
}

function restoreChatOS() {
  const els = getElements();
  const savedOS = localStorage.getItem(CHAT_OS_STORAGE_KEY);
  if (savedOS && [...els.osInput.options].some((option) => option.value === savedOS)) {
    els.osInput.value = savedOS;
  }
}

function setupChatEvents() {
  const els = getElements();
  els.analyzeForm.addEventListener("submit", analyze);
  if (els.clearChatButton) els.clearChatButton.addEventListener("click", clearChatHistory);
  if (els.deleteChatButton) els.deleteChatButton.addEventListener("click", deleteCurrentChat);
  if (els.clearAllChatsButton) els.clearAllChatsButton.addEventListener("click", clearAllChats);
  if (els.newChatButton) els.newChatButton.addEventListener("click", clearChatHistory);
  if (els.voiceButton) els.voiceButton.addEventListener("click", toggleVoiceInput);
  els.osInput.addEventListener("change", () => localStorage.setItem(CHAT_OS_STORAGE_KEY, els.osInput.value));
  els.messageInput.addEventListener("input", resizeMessageInput);
  els.messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      els.analyzeForm.requestSubmit();
    }
  });
}

function toggleVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const els = getElements();

  if (!SpeechRecognition) {
    showToast("Tarayıcınız sesli yazdırmayı desteklemiyor.");
    return;
  }

  if (isListening && speechRecognition) {
    speechRecognition.stop();
    return;
  }

  speechRecognition = new SpeechRecognition();
  speechRecognition.lang = "tr-TR";
  speechRecognition.interimResults = false;
  speechRecognition.maxAlternatives = 1;

  speechRecognition.onstart = () => {
    isListening = true;
    if (els.voiceButton) els.voiceButton.classList.add("listening");
  };

  speechRecognition.onresult = (event) => {
    const transcript = event.results?.[0]?.[0]?.transcript?.trim();
    if (transcript) {
      els.messageInput.value = transcript;
      resizeMessageInput();
      els.messageInput.focus();
    }
  };

  speechRecognition.onerror = () => {
    showToast("Sesli yazdırma başlatılamadı.");
  };

  speechRecognition.onend = () => {
    isListening = false;
    if (els.voiceButton) els.voiceButton.classList.remove("listening");
  };

  speechRecognition.start();
}

// ========================================
// KEYBOARD SHORTCUTS
// ========================================
function setupKeyboardShortcuts() {
  const els = getElements();

  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      if (!isAnalyzing && currentPage === "assistantPage") {
        els.analyzeForm.requestSubmit();
      }
    }

    if (event.key === "Escape" && isAnalyzing && currentAnalysisAbortController) {
      currentAnalysisAbortController.abort();
    }
  });
}

// ========================================
// EXAMPLES & TEST CASES UI
// ========================================
function renderExamples() {
  const els = getElements();
  els.examples.innerHTML = "";

  quickExamples.forEach((example) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "example-button";
    button.innerHTML = `<span>${escapeHtml(example.label)}</span><strong>${escapeHtml(example.message)}</strong>`;
    button.addEventListener("click", () => {
      els.messageInput.value = example.message;
      resizeMessageInput();
      els.messageInput.focus();
    });
    els.examples.appendChild(button);
  });
}

function renderTestCases() {
  const els = getElements();
  els.testCases.innerHTML = "";

  testCases.forEach((testCase, index) => {
    const card = document.createElement("div");
    card.className = "test-case-card";

    const title = document.createElement("strong");
    title.textContent = `${index + 1}. ${testCase.expectedCategory}`;

    const message = document.createElement("p");
    message.textContent = testCase.message;

    const meta = document.createElement("div");
    meta.className = "test-case-meta";
    meta.innerHTML = `${testCase.os} • ${testCase.expectedPriority} • ${testCase.expectedRisk}`;

    const runButton = document.createElement("button");
    runButton.type = "button";
    runButton.className = "mini-button";
    runButton.textContent = "Çalıştır";
    runButton.addEventListener("click", () => runSingleTest(testCase, index));

    card.append(title, message, meta, runButton);
    els.testCases.appendChild(card);
  });
}

// ========================================
// EVALUATION LOGIC
// ========================================
function evaluateResponse(testCase, response) {
  const categoryCorrect = response.category === testCase.expectedCategory;
  const priorityCorrect = response.priority === testCase.expectedPriority;
  const riskCorrect = response.risk_level === testCase.expectedRisk;
  const correctCount = [categoryCorrect, priorityCorrect, riskCorrect].filter(Boolean).length;
  const status = correctCount === 3 ? "passed" : correctCount === 2 ? "partial" : "failed";

  return {
    message: testCase.message,
    os: testCase.os,
    expectedCategory: testCase.expectedCategory,
    modelCategory: response.category,
    expectedPriority: testCase.expectedPriority,
    modelPriority: response.priority,
    expectedRisk: testCase.expectedRisk,
    modelRisk: response.risk_level,
    categoryCorrect,
    priorityCorrect,
    riskCorrect,
    correctCount,
    status,
    error: "",
  };
}

function failedEvaluation(testCase, error) {
  return {
    message: testCase.message,
    os: testCase.os,
    expectedCategory: testCase.expectedCategory,
    modelCategory: "error",
    expectedPriority: testCase.expectedPriority,
    modelPriority: "error",
    expectedRisk: testCase.expectedRisk,
    modelRisk: "error",
    categoryCorrect: false,
    priorityCorrect: false,
    riskCorrect: false,
    correctCount: 0,
    status: "failed",
    error: error.message,
  };
}

async function runSingleTest(testCase, index) {
  if (isEvaluating) return;

  const els = getElements();
  isEvaluating = true;
  els.testStatus.textContent = `${index + 1}. test çalıştırılıyor...`;
  setEvaluationButtonsDisabled(true);

  try {
    const response = await requestAnalysis(testCase.message, testCase.os);
    const result = evaluateResponse(testCase, response);
    evaluationResults = evaluationResults.filter((item) => item.message !== testCase.message);
    evaluationResults.push(result);
  } catch (error) {
    if (error.name !== "AbortError") {
      evaluationResults = evaluationResults.filter((item) => item.message !== testCase.message);
      evaluationResults.push(failedEvaluation(testCase, error));
    }
  } finally {
    renderEvaluation();
    els.testStatus.textContent = `${index + 1}. test tamamlandı.`;
    isEvaluating = false;
    setEvaluationButtonsDisabled(false);
  }
}

async function runTests(selectedTests, label) {
  if (isEvaluating) return;

  const els = getElements();
  isEvaluating = true;
  evaluationResults = [];
  renderEvaluation();
  setEvaluationButtonsDisabled(true);

  for (let index = 0; index < selectedTests.length; index += 1) {
    const testCase = selectedTests[index];
    els.testStatus.textContent = `${label}: ${index + 1}/${selectedTests.length} test çalıştırılıyor...`;

    try {
      const response = await requestAnalysis(testCase.message, testCase.os);
      evaluationResults.push(evaluateResponse(testCase, response));
    } catch (error) {
      if (error.name !== "AbortError") {
        evaluationResults.push(failedEvaluation(testCase, error));
      }
    }

    renderEvaluation();
  }

  // Save results after tests complete
  saveEvaluationResults(evaluationResults);
  
  els.testStatus.textContent = `${label} tamamlandı. (Rapor indirmek için aşağıdaki butonu kullanabilirsiniz)`;
  isEvaluating = false;
  setEvaluationButtonsDisabled(false);
}

async function runAllTests() {
  await runTests(testCases, "Tüm testler");
}

async function runQuickTests() {
  await runTests(testCases.slice(0, 3), "Hızlı demo testi");
}

function setEvaluationButtonsDisabled(disabled) {
  const els = getElements();
  els.runAllTestsButton.disabled = disabled;
  els.runQuickTestsButton.disabled = disabled;
  els.clearTestsButton.disabled = disabled;
  document.querySelectorAll(".mini-button").forEach((button) => {
    button.disabled = disabled;
  });
}

function clearEvaluation() {
  evaluationResults = [];
  const els = getElements();
  els.testStatus.textContent = "Henüz test çalıştırılmadı.";
  renderEvaluation();
}

function accuracy(correct, total) {
  if (total === 0) return "0%";
  return `${Math.round((correct / total) * 100)}%`;
}

function renderEvaluation() {
  const els = getElements();
  const total = evaluationResults.length;
  const passed = evaluationResults.filter((result) => result.status === "passed").length;
  const partial = evaluationResults.filter((result) => result.status === "partial").length;
  const failed = evaluationResults.filter((result) => result.status === "failed").length;
  const categoryCorrect = evaluationResults.filter((result) => result.categoryCorrect).length;
  const priorityCorrect = evaluationResults.filter((result) => result.priorityCorrect).length;
  const riskCorrect = evaluationResults.filter((result) => result.riskCorrect).length;

  els.totalTestsMetric.textContent = total;
  els.passedTestsMetric.textContent = passed;
  els.partialTestsMetric.textContent = partial;
  els.failedTestsMetric.textContent = failed;
  els.categoryAccuracyMetric.textContent = accuracy(categoryCorrect, total);
  els.priorityAccuracyMetric.textContent = accuracy(priorityCorrect, total);
  els.riskAccuracyMetric.textContent = accuracy(riskCorrect, total);

  els.testResultsBody.innerHTML = "";
  evaluationResults.forEach((result) => {
    const row = document.createElement("tr");
    row.className = result.status === "passed" ? "passed-row" : result.status === "partial" ? "partial-row" : "failed-row";
    const label = result.status === "passed" ? "✓ Başarılı" : result.status === "partial" ? "⊘ Kısmi" : "✗ Başarısız";
    row.innerHTML = `
      <td><strong>${result.message.substring(0, 30)}</strong><br><small>${result.os}</small></td>
      <td>${result.expectedCategory}<br><small>${result.expectedPriority} • ${result.expectedRisk}</small></td>
      <td>
        <strong>${result.modelCategory}</strong><br>
        <small>${result.modelPriority} • ${result.modelRisk}</small>
        ${result.error ? `<br><span style="color: var(--danger);">${result.error}</span>` : ""}
      </td>
      <td><span class="result-pill ${result.status}">${label}<br>(${result.correctCount}/3)</span></td>
    `;
    els.testResultsBody.appendChild(row);
  });
}

// ========================================
// EVALUATION RESULTS STORAGE & EXPORT
// ========================================
const EVALUATION_RESULTS_STORAGE_KEY = "itSupportTestResults";
const EVALUATION_HISTORY_STORAGE_KEY = "itSupportTestHistory";

function saveEvaluationResults(results) {
  const timestamp = new Date().toISOString();
  const data = {
    timestamp,
    results,
    metrics: calculateMetrics(results),
  };
  
  localStorage.setItem(EVALUATION_RESULTS_STORAGE_KEY, JSON.stringify(data));
  
  // Also save to history
  let history = [];
  try {
    history = JSON.parse(localStorage.getItem(EVALUATION_HISTORY_STORAGE_KEY) || "[]");
  } catch (e) {
    history = [];
  }
  
  history.push(data);
  // Keep last 10 test runs
  if (history.length > 10) {
    history = history.slice(-10);
  }
  
  localStorage.setItem(EVALUATION_HISTORY_STORAGE_KEY, JSON.stringify(history));
}

function loadEvaluationResults() {
  try {
    const data = JSON.parse(localStorage.getItem(EVALUATION_RESULTS_STORAGE_KEY) || "{}");
    return data.results || [];
  } catch (e) {
    return [];
  }
}

function calculateMetrics(results) {
  const total = results.length;
  const passed = results.filter((r) => r.status === "passed").length;
  const partial = results.filter((r) => r.status === "partial").length;
  const failed = results.filter((r) => r.status === "failed").length;
  const categoryCorrect = results.filter((r) => r.categoryCorrect).length;
  const priorityCorrect = results.filter((r) => r.priorityCorrect).length;
  const riskCorrect = results.filter((r) => r.riskCorrect).length;
  
  return {
    timestamp: new Date().toISOString(),
    total,
    passed,
    partial,
    failed,
    categoryAccuracy: total > 0 ? Math.round((categoryCorrect / total) * 100) : 0,
    priorityAccuracy: total > 0 ? Math.round((priorityCorrect / total) * 100) : 0,
    riskAccuracy: total > 0 ? Math.round((riskCorrect / total) * 100) : 0,
    overallAccuracy: total > 0 ? Math.round(((passed / total) * 100)) : 0,
  };
}

function generateTestReport() {
  const metrics = calculateMetrics(evaluationResults);
  const timestamp = new Date().toLocaleString("tr-TR");
  
  const report = {
    metadata: {
      timestamp,
      timestampISO: new Date().toISOString(),
      apiUrl: apiBaseUrl,
      modelName: "oguzinyo/qwen2.5-3b-it-support-lora-v2",
      totalTestCases: testCases.length,
    },
    summary: {
      totalTestsRun: metrics.total,
      passedTests: metrics.passed,
      partialTests: metrics.partial,
      failedTests: metrics.failed,
    },
    accuracy: {
      categoryAccuracy: `${metrics.categoryAccuracy}%`,
      priorityAccuracy: `${metrics.priorityAccuracy}%`,
      riskAccuracy: `${metrics.riskAccuracy}%`,
      overallAccuracy: `${metrics.overallAccuracy}%`,
    },
    detailedResults: evaluationResults,
  };
  
  return report;
}

function downloadTestResults() {
  const report = generateTestReport();
  const dataStr = JSON.stringify(report, null, 2);
  const dataBlob = new Blob([dataStr], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(dataBlob);
  
  const link = document.createElement("a");
  link.href = url;
  link.download = `test_results_${new Date().toISOString().slice(0, 10)}_${new Date().getHours()}-${new Date().getMinutes()}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// ========================================
// INITIALIZATION
// ========================================
function initialize() {
  const els = getElements();
  if (els.apiUrl) els.apiUrl.textContent = apiBaseUrl;
  if (els.modelName) els.modelName.textContent = "oguzinyo/qwen2.5-3b-it-support-lora-v2";

  initializeNavigation();
  setupChatEvents();
  els.runAllTestsButton.addEventListener("click", runAllTests);
  els.runQuickTestsButton.addEventListener("click", runQuickTests);
  els.clearTestsButton.addEventListener("click", clearEvaluation);

  loadChatHistory();
  restoreChatOS();
  setupKeyboardShortcuts();
  renderExamples();
  renderChat();
  renderSessionList();
  renderTestCases();
  renderEvaluation();

  checkHealth();
  setInterval(checkHealth, 30000); // Check every 30 seconds
}

document.addEventListener("DOMContentLoaded", initialize);
