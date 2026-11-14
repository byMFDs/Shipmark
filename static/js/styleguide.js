// Styleguide: повтор удару марок і приклади тостів.
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

// Demo of the "pop" answer: the icon pops once when the state turns on.
document.querySelectorAll("[data-pop]").forEach((button) => {
  button.addEventListener("click", () => {
    const icon = button.querySelector(".icon");
    icon.classList.remove("pop");
    void icon.offsetWidth; // restart the animation
    icon.classList.add("pop");
  });
});
