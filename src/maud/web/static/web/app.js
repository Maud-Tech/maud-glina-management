// Casca das telas: troca de tema e prévia da cor da gestora. Sem dependências.
(function () {
  "use strict";
  const root = document.documentElement;
  // Grupos independentes; o grupo da rota atual fica aberto ao navegar.
  document.querySelectorAll("[data-navigation-group]").forEach(function (group) {
    const user = group.closest("[data-navigation-user]").dataset.navigationUser;
    const key = "glina.navigation." + user + "." + group.dataset.navigationGroup;
    try {
      const saved = localStorage.getItem(key);
      if (!group.hasAttribute("data-navigation-active") && saved !== null) {
        group.open = saved === "true";
      }
    } catch (_) { /* O menu nativo continua funcionando sem armazenamento. */ }
    group.addEventListener("toggle", function () {
      try { localStorage.setItem(key, String(group.open)); }
      catch (_) { /* Preferência indisponível neste navegador. */ }
    });
  });
  document.addEventListener("click", function (event) {
    const button = event.target.closest("[data-formset-add]");
    if (!button) return;
    const group = button.closest("[data-registration-formset]");
    const total = group.querySelector('input[name$="-TOTAL_FORMS"]');
    const maximum = group.querySelector('input[name$="-MAX_NUM_FORMS"]');
    const index = Number(total.value);
    if (index >= Number(maximum.value || 100)) return;
    const template = group.querySelector("[data-formset-template]");
    group.querySelector("[data-formset-items]").insertAdjacentHTML(
      "beforeend", template.innerHTML.replaceAll("__prefix__", String(index))
    );
    total.value = index + 1;
  });

  // Confirmação: botão com data-dialog="id" abre o <dialog id="id">; data-dialog-close fecha.
  document.addEventListener("click", function (event) {
    const opener = event.target.closest("[data-dialog]");
    if (opener) {
      const dialog = document.getElementById(opener.dataset.dialog);
      if (dialog && typeof dialog.showModal === "function") { event.preventDefault(); dialog.showModal(); }
      return;
    }
    const closer = event.target.closest("[data-dialog-close]");
    if (closer) { event.preventDefault(); closer.closest("dialog").close(); }
  });

  // Linhas repetidas (ex.: limites): data-row-add copia o <template data-row-template>; data-row-remove apaga.
  document.addEventListener("click", function (event) {
    const add = event.target.closest("[data-row-add]");
    if (add) {
      const group = add.closest("[data-rows-group]");
      const template = group.querySelector("template[data-row-template]");
      group.querySelector("[data-rows]").appendChild(template.content.cloneNode(true));
      group.querySelectorAll("[data-limit-dimension]").forEach(filterTargets);
      return;
    }
    const remove = event.target.closest("[data-row-remove]");
    if (remove) remove.closest("[data-row]").remove();
  });

  // Alvo do limite: só mostra as opções da dimensão escolhida (o servidor confere de novo).
  function filterTargets(dimension) {
    const select = dimension.closest("[data-row]").querySelector("[data-limit-target]");
    if (!select) return;
    let keep = false;
    select.querySelectorAll("optgroup").forEach(function (group) {
      const match = group.dataset.dimension === dimension.value;
      group.hidden = !match;
      group.disabled = !match;
      if (match && Array.prototype.some.call(group.querySelectorAll("option"), function (o) { return o.selected; })) keep = true;
    });
    if (!keep) {
      const first = select.querySelector('optgroup:not([hidden]) option');
      select.value = first ? first.value : "";
    }
  }
  document.querySelectorAll("[data-limit-dimension]").forEach(filterTargets);
  document.addEventListener("change", function (event) {
    if (event.target.matches("[data-limit-dimension]")) filterTargets(event.target);
  });

  // Tema: cada pessoa escolhe; fica num cookie para o servidor já mandar a página certa.
  document.addEventListener("click", function (event) {
    const button = event.target.closest("[data-theme-toggle]");
    if (!button) return;
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    document.cookie = "theme=" + next + "; path=/; max-age=31536000; SameSite=Lax";
  });

  // Prévia da cor: mesma regra do domain/brand.py (texto escuro ou branco, o de maior contraste).
  const DARK = "#031011", LIGHT = "#FFFFFF";
  function luminance(hex) {
    const c = [1, 3, 5].map(function (i) { return parseInt(hex.slice(i, i + 2), 16) / 255; })
      .map(function (v) { return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }
  function contrast(a, b) {
    const x = luminance(a), y = luminance(b);
    return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
  }
  function normalize(raw) {
    let v = (raw || "").trim().replace(/^#/, "");
    if (/^[0-9a-f]{3}$/i.test(v)) v = v.split("").map(function (d) { return d + d; }).join("");
    return /^[0-9a-f]{6}$/i.test(v) ? "#" + v.toUpperCase() : null;
  }
  function preview(raw, source) {
    const color = normalize(raw);
    if (!color) return;
    root.style.setProperty("--brand", color);
    root.style.setProperty("--on-brand", contrast(color, DARK) >= contrast(color, LIGHT) ? DARK : LIGHT);
    document.querySelectorAll("[data-brand-input]").forEach(function (input) {
      if (input === source) return;
      if (input.type === "radio") input.checked = input.value.toUpperCase() === color;
      else input.value = color;
    });
  }
  document.addEventListener("input", function (event) {
    if (event.target.matches("[data-brand-input]")) preview(event.target.value, event.target);
  });
  document.addEventListener("change", function (event) {
    if (event.target.matches("[data-brand-input]")) preview(event.target.value, event.target);
    if (event.target.matches(".drop input[type=file]")) {
      const label = event.target.closest(".drop").querySelector(".chosen");
      if (label) label.textContent = event.target.files.length ? event.target.files[0].name : "";
    }
  });
})();
