// Composer: images by drag and drop or the "Add images" button, previews with a remove button, and the sticker picker.
// Without this file the form still works: a plain file input and a <select> of stickers.
// Previews are blob: URLs (the page's own memory, nothing is uploaded until the form is sent); the CSP allows blob:
// images only on pages with a composer. The server checks every file again (type, size, pixels, count).

const TYPES = ["image/png", "image/jpeg", "image/webp"];
const MAX_BYTES = 5 * 1024 * 1024;
const RECENT_KEY = "community.recentStickers";
const RECENT_MAX = 8;

function setFiles(input, files) {
  const transfer = new DataTransfer();
  files.forEach((file) => transfer.items.add(file));
  input.files = transfer.files;
}

function armComposer(composer) {
  const input = composer.querySelector("[data-file-input]");
  const box = composer.querySelector("[data-drop]");
  const list = composer.querySelector("[data-previews]");
  const max = Number(composer.dataset.max);
  const canEdit = typeof DataTransfer === "function";
  let files = [];
  let urls = [];

  function problem(file) {
    if (!TYPES.includes(file.type)) return composer.dataset.badType;
    if (file.size > MAX_BYTES) return composer.dataset.tooBig;
    return "";
  }

  function render() {
    urls.forEach((url) => URL.revokeObjectURL(url));
    urls = [];
    list.replaceChildren();
    files.forEach((file, index) => {
      const item = document.createElement("li");
      item.className = "composer__preview";
      const error = problem(file) || (index >= max ? composer.dataset.tooMany : "");
      if (error) {
        item.classList.add("is-invalid");
        item.title = `${file.name}: ${error}`;
      }
      if (!problem(file)) {
        const img = document.createElement("img");
        const url = URL.createObjectURL(file);
        urls.push(url);
        img.src = url;
        img.alt = file.name;
        item.append(img);
      } else {
        const text = document.createElement("span");
        text.className = "visually-hidden";
        text.textContent = item.title;
        item.append(text);
      }
      if (canEdit) {
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "btn btn--quiet btn--icon";
        remove.setAttribute("aria-label", `${list.dataset.remove || "Remove"}: ${file.name}`);
        const icon = composer.querySelector("template[data-close-icon]")?.content.firstElementChild;
        if (icon) remove.append(icon.cloneNode(true));
        remove.addEventListener("click", () => {
          files.splice(index, 1);
          setFiles(input, files);
          render();
          input.focus();
        });
        item.append(remove);
      }
      list.append(item);
    });
  }

  function add(newFiles) {
    files = canEdit ? [...files, ...newFiles] : [...newFiles];
    if (canEdit) setFiles(input, files);
    render();
  }

  input.addEventListener("change", () => {
    const chosen = [...input.files];
    if (canEdit) {
      // The browser replaced the selection; keep what was chosen before and add the new files.
      files = [...files, ...chosen.filter((file) => !files.includes(file))];
      setFiles(input, files);
    } else {
      files = chosen;
    }
    render();
  });

  if (canEdit) {
    let depth = 0;
    box.addEventListener("dragenter", (event) => {
      if (![...event.dataTransfer.types].includes("Files")) return;
      event.preventDefault();
      depth += 1;
      box.classList.add("is-dragging");
    });
    box.addEventListener("dragover", (event) => {
      if ([...event.dataTransfer.types].includes("Files")) event.preventDefault();
    });
    box.addEventListener("dragleave", () => {
      depth = Math.max(0, depth - 1);
      if (!depth) box.classList.remove("is-dragging");
    });
    box.addEventListener("drop", (event) => {
      event.preventDefault();
      depth = 0;
      box.classList.remove("is-dragging");
      add([...event.dataTransfer.files]);
    });
    // Pasting an image from the clipboard adds it too.
    box.addEventListener("paste", (event) => {
      const pasted = [...(event.clipboardData?.files || [])].filter((file) => file.type.startsWith("image/"));
      if (pasted.length) add(pasted);
    });
  }

  composer.closest("form")?.addEventListener("reset", () => { files = []; render(); });
  armPicker(composer);
}

// ---------- Sticker picker ----------

function readRecent() {
  try {
    const value = JSON.parse(localStorage.getItem(RECENT_KEY) || "[]");
    return Array.isArray(value) ? value.filter((key) => typeof key === "string") : [];
  } catch {
    return [];
  }
}

function saveRecent(key) {
  try {
    const recent = [key, ...readRecent().filter((item) => item !== key)].slice(0, RECENT_MAX);
    localStorage.setItem(RECENT_KEY, JSON.stringify(recent));
  } catch {
    // private window or storage blocked: recent stickers are a convenience only
  }
}

function armPicker(composer) {
  const select = composer.querySelector("select[name=sticker]");
  const open = composer.querySelector("[data-picker-open]");
  const picker = composer.querySelector("[data-picker]");
  if (!select || !open || !picker) return;

  const search = picker.querySelector("[data-picker-search]");
  const grid = picker.querySelector("[data-picker-grid]");
  const recentGrid = picker.querySelector("[data-picker-recent]");
  const recentTitle = picker.querySelector("[data-picker-recent-title]");
  const none = picker.querySelector("[data-picker-none]");
  const chosen = composer.querySelector("[data-sticker-chosen]");
  const chosenImg = chosen.querySelector("[data-sticker-img]");
  const items = [...grid.querySelectorAll("[data-sticker]")];
  open.hidden = false;

  function visibleItems() {
    return [...picker.querySelectorAll("[data-sticker]")].filter((item) => !item.hidden && item.offsetParent !== null);
  }

  function renderRecent() {
    const keys = readRecent().filter((key) => items.some((item) => item.dataset.sticker === key));
    recentGrid.replaceChildren(...keys.map((key) => {
      const copy = items.find((item) => item.dataset.sticker === key).cloneNode(true);
      copy.querySelector("img").loading = "eager";
      return copy;
    }));
    recentTitle.hidden = !keys.length || Boolean(search.value);
    recentGrid.hidden = !keys.length || Boolean(search.value);
  }

  function show() {
    renderRecent();
    picker.hidden = false;
    open.setAttribute("aria-expanded", "true");
    search.value = "";
    filter();
    search.focus();
  }

  function hide(returnFocus = true) {
    if (picker.hidden) return;
    picker.hidden = true;
    open.setAttribute("aria-expanded", "false");
    if (returnFocus) open.focus();
  }

  function filter() {
    const words = search.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    let shown = 0;
    items.forEach((item) => {
      item.hidden = !words.every((word) => item.dataset.label.includes(word));
      if (!item.hidden) shown += 1;
    });
    none.hidden = shown > 0;
    recentTitle.hidden = recentGrid.hidden = Boolean(words.length) || !recentGrid.children.length;
  }

  function choose(key) {
    select.value = key;
    const item = items.find((element) => element.dataset.sticker === key);
    if (key && item) {
      chosenImg.src = item.querySelector("img").src;
      chosenImg.alt = item.getAttribute("aria-label");
      chosen.hidden = false;
      chosen.classList.remove("is-popping");
      void chosen.offsetWidth;
      chosen.classList.add("is-popping");
      saveRecent(key);
    } else {
      chosen.hidden = true;
    }
  }

  open.addEventListener("click", () => (picker.hidden ? show() : hide()));
  search.addEventListener("input", filter);
  chosen.querySelector("[data-sticker-clear]").addEventListener("click", () => { choose(""); open.focus(); });

  picker.addEventListener("click", (event) => {
    if (event.target.closest("[data-picker-close]")) return hide();
    const item = event.target.closest("[data-sticker]");
    if (!item) return;
    choose(item.dataset.sticker);
    hide();
  });

  // Keyboard: arrows move between stickers, Down from the search goes into the grid, Escape closes.
  picker.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      hide();
      return;
    }
    const current = event.target.closest?.("[data-sticker]");
    const list = visibleItems();
    if (event.target === search && event.key === "ArrowDown" && list.length) {
      event.preventDefault();
      list[0].focus();
      return;
    }
    if (!current) return;
    const index = list.indexOf(current);
    const columns = Math.max(1, Math.round(grid.clientWidth / current.offsetWidth));
    const step = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: columns, ArrowUp: -columns }[event.key];
    if (step === undefined) {
      if (event.key === "Home") list[0]?.focus();
      if (event.key === "End") list[list.length - 1]?.focus();
      return;
    }
    event.preventDefault();
    const next = index + step;
    if (next < 0) search.focus();
    else list[Math.min(next, list.length - 1)]?.focus();
  });

  document.addEventListener("click", (event) => {
    if (!picker.hidden && !picker.contains(event.target) && !open.contains(event.target)) hide(false);
  });

  if (select.value) choose(select.value); // a form shown again after an error keeps its sticker
}

document.querySelectorAll("[data-composer]").forEach(armComposer);
