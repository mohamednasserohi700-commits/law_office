(() => {
  const debounce = (fn, ms = 280) => {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  };

  const escapeHtml = (s) =>
    String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");

  const initEntityPicker = (root, config) => {
    const hidden = root.querySelector(`input[name="${config.field}"]`);
    const search = root.querySelector(".smart-picker-search");
    const dropdown = root.querySelector(".smart-picker-dropdown");
    const selectedWrap = root.querySelector(".smart-picker-selected");
    const chipName = root.querySelector(".smart-picker-chip-name");
    const chipMeta = root.querySelector(".smart-picker-chip-meta");
    const clearBtn = root.querySelector(".smart-picker-clear");
    if (!hidden || !search || !dropdown) return;

    const setSelected = (item) => {
      if (!item || !item.id) {
        hidden.value = "";
        selectedWrap?.classList.add("hidden");
        search.classList.remove("hidden");
        search.value = "";
        return;
      }
      hidden.value = String(item.id);
      if (chipName) chipName.textContent = config.chipTitle(item);
      if (chipMeta) chipMeta.textContent = config.chipMeta(item);
      selectedWrap?.classList.remove("hidden");
      search.classList.add("hidden");
      dropdown.classList.add("hidden");
    };

    const renderList = (items) => {
      if (!items.length) {
        dropdown.innerHTML = `<div class="smart-picker-empty">${config.emptyHtml}</div>`;
        dropdown.classList.remove("hidden");
        return;
      }
      dropdown.innerHTML = "";
      items.forEach((item) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "smart-picker-option";
        btn.innerHTML = `<span class="smart-picker-option-name">${escapeHtml(config.optionTitle(item))}</span><span class="smart-picker-option-meta">${escapeHtml(config.optionMeta(item))}</span>`;
        btn.addEventListener("click", () => setSelected(item));
        dropdown.appendChild(btn);
      });
      dropdown.classList.remove("hidden");
    };

    const fetchItems = async (q) => {
      const res = await fetch(`${config.apiUrl}?q=${encodeURIComponent(q || "")}`);
      const data = await res.json();
      renderList(Array.isArray(data[config.dataKey]) ? data[config.dataKey] : []);
    };

    const loadInitial = () => {
      const id = root.dataset.initialId;
      if (!id) return;
      setSelected(config.initialFromDataset(root));
    };

    clearBtn?.addEventListener("click", () => {
      setSelected(null);
      search.focus();
    });
    search.addEventListener("input", debounce(() => fetchItems(search.value.trim())));
    search.addEventListener("focus", () => fetchItems(search.value.trim()));
    document.addEventListener("click", (e) => {
      if (!root.contains(e.target)) dropdown.classList.add("hidden");
    });
    loadInitial();
  };

  document.querySelectorAll("[data-client-picker]").forEach((root) => {
    initEntityPicker(root, {
      field: "client_id",
      apiUrl: "/api/clients/picker",
      dataKey: "clients",
      emptyHtml: 'لا يوجد عملاء. <a href="/table/clients/new" class="smart-link">أضف عميلاً</a>',
      chipTitle: (c) => c.name,
      chipMeta: (c) => [c.phone, c.type].filter(Boolean).join(" · ") || "—",
      optionTitle: (c) => c.name,
      optionMeta: (c) => `${c.phone || "بدون هاتف"}${c.type ? " · " + c.type : ""}`,
      initialFromDataset: (r) => ({
        id: r.dataset.initialId,
        name: r.dataset.initialName,
        phone: r.dataset.initialPhone,
        type: r.dataset.initialType,
      }),
    });
  });

  document.querySelectorAll("[data-case-picker]").forEach((root) => {
    initEntityPicker(root, {
      field: "case_id",
      apiUrl: "/api/cases/picker",
      dataKey: "cases",
      emptyHtml: 'لا توجد قضايا. <a href="/table/cases/new" class="smart-link">أضف قضية</a>',
      chipTitle: (c) => c.case_num,
      chipMeta: (c) => [c.subject, c.status].filter(Boolean).join(" · ") || "—",
      optionTitle: (c) => c.case_num,
      optionMeta: (c) => `${c.subject || "بدون موضوع"}${c.court ? " · " + c.court : ""}`,
      initialFromDataset: (r) => ({
        id: r.dataset.initialId,
        case_num: r.dataset.initialNum,
        subject: r.dataset.initialSubject,
        status: r.dataset.initialStatus,
      }),
    });
  });

  const requireHidden = (form, name, msg) => {
    const hid = form.querySelector(`input[name="${name}"]`);
    if (hid?.value?.trim()) return true;
    const picker = form.querySelector(`[data-${name.replace("_id", "")}-picker], [data-client-picker], [data-case-picker]`);
    const search = form.querySelector(".smart-picker-search");
    search?.classList.remove("hidden");
    search?.focus();
    alert(msg);
    return false;
  };

  document.querySelectorAll("form[data-smart-form='case']").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!requireHidden(form, "client_id", "يرجى اختيار عميل من النظام.")) e.preventDefault();
    });
  });
  document.querySelectorAll("form[data-smart-form='session']").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!requireHidden(form, "case_id", "يرجى اختيار قضية من النظام.")) e.preventDefault();
    });
  });
  document.querySelectorAll("form[data-smart-form='payment']").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!requireHidden(form, "client_id", "يرجى اختيار عميل.")) e.preventDefault();
    });
  });
  document.querySelectorAll("form[data-smart-form='contract']").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!requireHidden(form, "client_id", "يرجى اختيار عميل.")) e.preventDefault();
    });
  });
})();
