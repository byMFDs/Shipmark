// Build log on the project page (owner only).
// - "Post update" sends the form with fetch() and puts the new entry at the top of the list.
// - "Delete entry" removes the entry in place.
// Without JS, or if fetch fails, the same forms do a normal POST and the page reloads.
import { showToast } from "./toast.js";

const section = document.querySelector("[data-build-log]");
const form = section?.querySelector("[data-log-form]");

if (section && form) {
  const list = section.querySelector("[data-log-list]");
  const empty = section.querySelector("[data-log-empty]");
  const launchField = section.querySelector("[data-launch-field]");
  const launched = document.querySelector("[data-launched]");
  const heading = section.querySelector("#build-log-title");

  async function send(target) {
    const response = await fetch(target.action, {
      method: "POST",
      headers: {
        "X-CSRFToken": target.querySelector("input[name=csrfmiddlewaretoken]").value,
        Accept: "application/json",
      },
      body: new FormData(target),
      credentials: "same-origin",
    });
    return response.json(); // the views always answer JSON here, also on 400 and 429
  }

  function setCanLaunch(canLaunch) {
    if (!launchField) return;
    launchField.hidden = !canLaunch;
    if (!canLaunch) launchField.querySelector("input[type=checkbox]").checked = false;
  }

  function syncEmpty() {
    const hasEntries = list.children.length > 0;
    list.hidden = !hasEntries;
    if (empty) empty.hidden = hasEntries;
  }

  // Disables the button while a request runs; returns a function that restores it.
  function busy(button) {
    const label = button.innerHTML;
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    if (button.dataset.busyLabel) button.textContent = button.dataset.busyLabel;
    return () => {
      button.disabled = false;
      button.removeAttribute("aria-busy");
      button.innerHTML = label;
    };
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button[type=submit]");
    if (button.disabled) return;
    const restore = busy(button);
    let data;
    try {
      data = await send(form);
    } catch {
      form.submit(); // network or parsing problem: fall back to the plain POST
      return;
    } finally {
      restore();
    }
    if (data.ok) {
      list.insertAdjacentHTML("afterbegin", data.html);
      form.reset();
      setCanLaunch(data.can_launch);
      if (launched && data.launched_html !== undefined) launched.innerHTML = data.launched_html;
      syncEmpty();
    }
    showToast(data.message, { kind: data.ok ? "info" : "error" });
  });

  // One listener for all delete forms, also for entries added after the page loaded.
  list.addEventListener("submit", async (event) => {
    const target = event.target.closest("[data-log-delete]");
    if (!target) return;
    event.preventDefault();
    const button = target.querySelector("button[type=submit]");
    if (button.disabled) return;
    const restore = busy(button);
    let data;
    try {
      data = await send(target);
    } catch {
      target.submit();
      return;
    } finally {
      restore();
    }
    if (data.ok) {
      target.closest("[data-log-entry]").remove();
      heading.focus(); // the focused button is gone; keep keyboard users in the section
      setCanLaunch(data.can_launch);
      syncEmpty();
    }
    showToast(data.message, { kind: data.ok ? "info" : "error" });
  });
}
