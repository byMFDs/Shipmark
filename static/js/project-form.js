import { showToast } from "./toast.js";

// Markdown preview in the project editor. Without JS the button is hidden and the form still works.
// The server renders and sanitizes the markdown (same code as the project page); we only show its answer.

const form = document.querySelector("[data-project-form]");
const toggle = form?.querySelector("[data-preview-toggle]");
const panel = form?.querySelector("[data-preview]");
const textarea = form?.querySelector("textarea");

if (form && toggle && panel && textarea) {
  const csrf = form.querySelector("input[name=csrfmiddlewaretoken]").value;
  let timer;
  let request = 0;

  async function render() {
    const current = ++request;
    try {
      const response = await fetch(form.dataset.previewUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrf },
        body: new URLSearchParams({ text: textarea.value }),
        credentials: "same-origin",
      });
      if (current !== request) return; // a newer request is in flight
      if (!response.ok) throw new Error(String(response.status));
      panel.innerHTML = (await response.json()).html || "";
    } catch {
      panel.textContent = toggle.dataset.error || "Preview is not available right now.";
    }
  }

  toggle.addEventListener("click", () => {
    const open = panel.hidden;
    panel.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
    if (open) render();
  });

  textarea.addEventListener("input", () => {
    if (panel.hidden) return;
    clearTimeout(timer);
    timer = setTimeout(render, 400);
  });
}

// Screenshots: chosen files upload with the main form's Save (or Publish, which belongs to it).
// Here we only say how many are chosen, and warn once when another form on the page would
// navigate away and drop them. The server checks everything again.
const shotInput = form?.querySelector("[data-shot-input]");
const shotStatus = form?.querySelector("[data-shot-status]");

if (form && shotInput && shotStatus) {
  const max = Number(shotStatus.dataset.max) - Number(shotStatus.dataset.existing);
  let warned = false;

  shotInput.addEventListener("change", () => {
    const count = shotInput.files.length;
    warned = false;
    shotStatus.hidden = count === 0;
    shotStatus.classList.toggle("field__error", count > max);
    shotStatus.textContent = count > max
      ? shotStatus.dataset.over
      : shotStatus.dataset.chosen.replace("%(count)s", String(count));
  });

  document.addEventListener("submit", (event) => {
    if (event.target === form || event.defaultPrevented || !shotInput.files.length || warned) return;
    event.preventDefault(); // once: the second press goes through
    warned = true;
    showToast(form.dataset.unsaved, { kind: "error" });
  });
}
