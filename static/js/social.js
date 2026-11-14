// Кнопки «Подобається» і «Стежити» без перезавантаження.
// Follow and like buttons. The forms work as plain POSTs without this file.
// With it: the button changes at once (optimistic), the request runs in the background,
// and on any error the button goes back to how it was and a toast says why.
// One listener on the document, so rows added by "Load more" work too.
import { showToast } from "./toast.js";

const GENERIC_ERROR = "Could not save. Try again.";

function counterOf(form) {
  if (form.dataset.countTarget) return document.getElementById(form.dataset.countTarget);
  return form.querySelector("[data-count]");
}

// Puts the form into the "pressed" (liked / following) or normal state.
function render(form, pressed, count) {
  const button = form.querySelector("button");
  const label = form.querySelector("[data-label]");
  button.setAttribute("aria-pressed", String(pressed));
  label.textContent = pressed ? label.dataset.labelOn : label.dataset.labelOff;
  // Follow: filled button to start, quiet once following.
  if (form.hasAttribute("data-follow-style")) {
    button.classList.toggle("btn--primary", !pressed);
    button.classList.toggle("btn--secondary", pressed);
  }
  // If the user leaves without JS finishing, the form still posts to the right URL.
  form.action = pressed ? form.dataset.urlOff : form.dataset.urlOn;
  const counter = counterOf(form);
  if (counter && count !== null && count !== undefined) {
    counter.textContent = String(count);
    // Like counts hide a zero ("0 likes" reads as "nobody cares"); follower stats always show their number.
    if (counter.hasAttribute("data-hide-zero")) counter.hidden = count === 0;
  }
}

document.addEventListener("submit", async (event) => {
  const form = event.target.closest?.("[data-social-form]");
  if (!form) return;
  event.preventDefault();

  const button = form.querySelector("button");
  if (button.disabled) return;

  const wasPressed = button.getAttribute("aria-pressed") === "true";
  const nowPressed = !wasPressed;
  const counter = counterOf(form);
  const before = counter ? Number(counter.textContent) : null;

  render(form, nowPressed, before === null ? null : Math.max(0, before + (nowPressed ? 1 : -1)));
  button.disabled = true;
  button.setAttribute("aria-busy", "true");

  try {
    const response = await fetch(nowPressed ? form.dataset.urlOn : form.dataset.urlOff, {
      method: "POST",
      headers: {
        "X-CSRFToken": form.querySelector("input[name=csrfmiddlewaretoken]").value,
        Accept: "application/json",
      },
      credentials: "same-origin",
    });
    const data = await response.json().catch(() => null);
    if (!response.ok || !data?.ok) throw new Error(data?.message || form.dataset.error || GENERIC_ERROR);
    render(form, data.pressed, data.count); // the server's count wins
  } catch (error) {
    render(form, wasPressed, before); // roll back
    // A failed fetch() says "Failed to fetch": show our own text instead.
    showToast(error instanceof TypeError ? form.dataset.error || GENERIC_ERROR : error.message, { kind: "error" });
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }
});
