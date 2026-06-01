(() => {
  const root = document.documentElement;
  const themeIcon = document.getElementById("theme-toggle-icon");
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const SIDEBAR_KEY = "law-sidebar-collapsed";

  root.setAttribute("data-theme", "dark");
  try {
    localStorage.setItem("obsidian-theme", "dark");
  } catch (_err) {}
  if (themeIcon) themeIcon.textContent = "🌙";

  const applySidebarState = (collapsed) => {
    document.body.classList.toggle("sidebar-collapsed", Boolean(collapsed));
    try {
      localStorage.setItem(SIDEBAR_KEY, collapsed ? "1" : "0");
    } catch (_err) {}
  };

  try {
    const saved = localStorage.getItem(SIDEBAR_KEY);
    applySidebarState(saved === "1");
  } catch (_err) {}

  sidebarToggle?.addEventListener("click", () => {
    const collapsed = document.body.classList.contains("sidebar-collapsed");
    applySidebarState(!collapsed);
    hideSidebarFlytip();
  });

  const flytip = document.createElement("div");
  flytip.id = "sidebar-flytip";
  flytip.className = "sidebar-flytip";
  flytip.setAttribute("role", "tooltip");
  flytip.setAttribute("aria-hidden", "true");
  document.body.appendChild(flytip);

  const hideSidebarFlytip = () => {
    flytip.classList.remove("visible");
    flytip.setAttribute("aria-hidden", "true");
  };

  const showSidebarFlytip = (el) => {
    if (!document.body.classList.contains("sidebar-collapsed")) return;
    const label =
      el.getAttribute("data-tooltip") ||
      el.querySelector(".sidebar-label")?.textContent?.trim() ||
      el.querySelector(".sidebar-brand-title")?.textContent?.trim();
    if (!label) return;
    flytip.textContent = label;
    flytip.classList.add("visible");
    flytip.setAttribute("aria-hidden", "false");
    const rect = el.getBoundingClientRect();
    flytip.style.visibility = "hidden";
    flytip.style.left = "0";
    flytip.style.top = "0";
    const tipW = flytip.offsetWidth;
    const tipH = flytip.offsetHeight;
    const gap = 14;
    let left = rect.left - tipW - gap;
    let top = rect.top + rect.height / 2 - tipH / 2;
    left = Math.max(12, left);
    top = Math.max(12, Math.min(top, window.innerHeight - tipH - 12));
    flytip.style.left = `${left}px`;
    flytip.style.top = `${top}px`;
    flytip.style.right = "auto";
    flytip.style.visibility = "visible";
  };

  document.querySelectorAll(".sidebar-item-modern, .sidebar-brand[data-tooltip]").forEach((el) => {
    el.addEventListener("mouseenter", () => showSidebarFlytip(el));
    el.addEventListener("mouseleave", hideSidebarFlytip);
    el.addEventListener("focus", () => showSidebarFlytip(el));
    el.addEventListener("blur", hideSidebarFlytip);
  });

  const quickPanel = document.getElementById("quick-actions-panel");
  const openQuick = () => {
    if (!quickPanel) return;
    quickPanel.classList.remove("hidden");
    quickPanel.classList.add("flex");
  };
  const closeQuick = () => {
    if (!quickPanel) return;
    quickPanel.classList.add("hidden");
    quickPanel.classList.remove("flex");
  };

  document.getElementById("floating-quick-actions")?.addEventListener("click", openQuick);
  document.getElementById("close-quick-actions")?.addEventListener("click", closeQuick);
  quickPanel?.addEventListener("click", (event) => event.target === quickPanel && closeQuick());

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeQuick();
  });

  document.querySelectorAll("[data-counter]").forEach((node) => {
    const end = Number(node.getAttribute("data-counter")) || 0;
    if (!end) {
      node.textContent = "0";
      return;
    }
    const duration = 650;
    const start = performance.now();
    const step = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      node.textContent = new Intl.NumberFormat("ar-EG").format(Math.floor(end * progress));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  });

  document.querySelectorAll(".table-premium tbody tr").forEach((row) => {
    row.addEventListener("click", () => row.classList.toggle("selected"));
  });

  const toastStack = document.getElementById("smart-toast-stack");
  const showToast = (message, category = "success") => {
    if (!toastStack || !message) return;
    const el = document.createElement("div");
    el.className = `smart-toast smart-toast-${category}`;
    el.textContent = message;
    toastStack.appendChild(el);
    requestAnimationFrame(() => el.classList.add("visible"));
    setTimeout(() => {
      el.classList.remove("visible");
      setTimeout(() => el.remove(), 300);
    }, 5200);
  };
  try {
    const payload = document.getElementById("flash-payload");
    if (payload?.textContent) {
      const msgs = JSON.parse(payload.textContent);
      msgs.forEach(([cat, msg]) => showToast(msg, cat === "danger" ? "danger" : cat === "warning" ? "warning" : "success"));
    }
  } catch (_err) {}

  document.querySelectorAll("[data-status]").forEach((node) => {
    const value = (node.textContent || "").trim();
    if (!node.classList.contains("status-pill")) node.classList.add("status-pill");
    if (value.includes("متصل")) node.classList.add("status-online");
    else if (value.includes("غير متصل")) node.classList.add("status-offline");
    else if (value.includes("مفتوحة")) node.classList.add("status-open");
    else if (value.includes("نشطة")) node.classList.add("status-active");
    else if (value.includes("مؤجلة")) node.classList.add("status-pending");
    else if (value.includes("مقفولة") || value.includes("مغلقة")) node.classList.add("status-closed");
    else if (value.includes("منتهية")) node.classList.add("status-finished");
  });
})();
