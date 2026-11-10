// Styleguide helpers (development only): replay the hallmark strike, show sample toasts.
import { showToast } from "./toast.js";

document.querySelectorAll("[data-replay]").forEach((button) => {
  button.addEventListener("click", () => {
    const target = document.getElementById(button.dataset.replay);
    // A fresh copy of the element restarts its CSS animations.
    target.replaceWith(target.cloneNode(true));
  });
});

document.querySelectorAll("[data-demo-toast]").forEach((button) => {
  button.addEventListener("click", () => {
    showToast(button.dataset.demoToast, { kind: button.dataset.kind || "info" });
  });
});
