// Domain verification on the project editor.
// - Shows only the instructions of the chosen method (without JS both are visible).
// - "Verify now" sends the form with fetch() and updates the status in place.
//   Without JS, or if fetch fails, the same form does a normal POST and the page reloads.
import "./copy.js";
import { showToast } from "./toast.js";

const form = document.querySelector("[data-domain-form]");
const status = document.querySelector("[data-domain-status]");

if (form && status) {
  const radios = form.querySelectorAll("input[name=method]");
  const panels = form.querySelectorAll("[data-method-panel]");
  const button = form.querySelector("button[type=submit]");
  const csrf = form.querySelector("input[name=csrfmiddlewaretoken]").value;

  function showChosen() {
    const chosen = form.querySelector("input[name=method]:checked")?.value;
    panels.forEach((panel) => { panel.hidden = panel.dataset.methodPanel !== chosen; });
  }
  radios.forEach((radio) => radio.addEventListener("change", showChosen));
  showChosen();

  let busy = false;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (busy) return;
    busy = true;
    const label = button.textContent;
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    button.textContent = button.dataset.busyLabel || label;
    try {
      const response = await fetch(form.action, {
        method: "POST",
        headers: { "X-CSRFToken": csrf, Accept: "application/json" },
        body: new FormData(form),
        credentials: "same-origin",
      });
      const data = await response.json(); // the view always answers JSON here, also on 429
      if (data.html) status.innerHTML = data.html;
      showToast(data.message, { kind: data.ok ? "info" : "error" });
    } catch {
      form.submit(); // network or parsing problem: fall back to the plain POST
      return;
    } finally {
      busy = false;
      button.disabled = false;
      button.removeAttribute("aria-busy");
      button.textContent = label;
    }
  });
}
