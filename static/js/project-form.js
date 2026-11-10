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
