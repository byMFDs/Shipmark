// Кнопки «Копіювати» для коду вставки.
// Copy buttons: <button data-copy="element-id" data-copied="Copied">. Hidden without JS (needs-js).
// The code text stays selectable, so copying by hand always works too.
import { showToast } from "./toast.js";

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  // Old browsers and non-HTTPS pages: a hidden textarea and execCommand.
  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.append(area);
  area.select();
  const ok = document.execCommand("copy");
  area.remove();
  if (!ok) throw new Error("copy failed");
}

export function initCopyButtons(root = document) {
  root.querySelectorAll("[data-copy]").forEach((button) => {
    if (button.dataset.copyReady) return;
    button.dataset.copyReady = "1";
    button.addEventListener("click", async () => {
      const source = document.getElementById(button.dataset.copy);
      if (!source) return;
      try {
        await copyText(source.textContent.trim());
        showToast(button.dataset.copied || "Copied");
      } catch {
        // Select the text so the person can press Ctrl+C / Cmd+C.
        const range = document.createRange();
        range.selectNodeContents(source);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
      }
    });
  });
}

initCopyButtons();
