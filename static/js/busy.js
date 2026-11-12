// Loading state for buttons (styles: .btn[data-busy-ring] in components.css). When a form really submits (no
// script stopped it), the button that sent it shows a ring and ignores further clicks, so nothing is sent twice.
// Scripts that send a form themselves (likes, domain check) set aria-busy on their own and keep their text.
// Coming back with the Back button (page restored from the cache) clears it.

document.addEventListener("submit", (event) => {
  const button = event.submitter;
  if (!button || !button.classList.contains("btn") || button.classList.contains("social-btn")) return;
  // A download (data export) does not leave the page, so its button must stay usable.
  if (event.target.closest("[data-no-busy]")) return;
  // Wait until every other submit listener has run (and the browser has read the button's name and value):
  // a script may still cancel this submit, e.g. the "images not uploaded yet" warning on the project form.
  setTimeout(() => {
    if (event.defaultPrevented) return;
    button.setAttribute("aria-busy", "true");
    button.setAttribute("data-busy-ring", "");
  }, 0);
});

window.addEventListener("pageshow", (event) => {
  if (!event.persisted) return;
  document.querySelectorAll(".btn[data-busy-ring]").forEach((el) => {
    el.removeAttribute("aria-busy");
    el.removeAttribute("data-busy-ring");
  });
});
