// Форма допису: картинки перетягуванням або кнопкою, прев'ю з видаленням.
// Composer: images by drag and drop or the "Add images" button, previews with a remove button.
// Without this file the form still works: a plain file input.
// Previews are blob: URLs (the page's own memory, nothing is uploaded until the form is sent); the CSP allows blob:
// images only on pages with a composer. The server checks every file again (type, size, pixels, count).

const TYPES = ["image/png", "image/jpeg", "image/webp"];
const MAX_BYTES = 5 * 1024 * 1024;

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
}

document.querySelectorAll("[data-composer]").forEach(armComposer);
