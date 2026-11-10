// Toasts: short results of an action ("Published"). Django messages render as toasts too.
// Info toasts hide after 6 seconds (paused while hovered or focused). Errors stay until closed.
// Other modules can call showToast("Liked") after a fetch() request.

const HIDE_AFTER_MS = 6000;
const region = document.querySelector("[data-toasts]");
const template = document.querySelector("template[data-toast-template]");

function dismiss(toast) {
  toast.classList.add("is-leaving");
  toast.addEventListener("transitionend", () => toast.remove(), { once: true });
  setTimeout(() => toast.remove(), 400); // no transition with reduced motion
}

function arm(toast) {
  toast.querySelector("[data-toast-close]")?.addEventListener("click", () => dismiss(toast));
  if (toast.classList.contains("toast--error")) return;

  let timer = setTimeout(() => dismiss(toast), HIDE_AFTER_MS);
  const pause = () => clearTimeout(timer);
  const resume = () => {
    clearTimeout(timer);
    timer = setTimeout(() => dismiss(toast), HIDE_AFTER_MS);
  };
  toast.addEventListener("mouseenter", pause);
  toast.addEventListener("mouseleave", resume);
  toast.addEventListener("focusin", pause);
  toast.addEventListener("focusout", resume);
}

export function showToast(text, { kind = "info" } = {}) {
  if (!region || !template) return;
  const toast = template.content.firstElementChild.cloneNode(true);
  toast.querySelector(".toast__text").textContent = text;
  if (kind === "error") {
    toast.classList.add("toast--error");
    toast.setAttribute("role", "alert");
  }
  region.append(toast);
  arm(toast);
}

region?.querySelectorAll("[data-toast]").forEach(arm);
