// Theme switch: System / Light / Dark.
// The saved choice is applied before the first paint by a short inline script in base.html.
// This module handles the buttons and keeps every open tab in sync.

const KEY = "theme";
const root = document.documentElement;
const themeMetas = [...document.querySelectorAll('meta[name="theme-color"]')];
themeMetas.forEach((meta) => { meta.dataset.original = meta.content; });

function savedChoice() {
  try {
    const value = localStorage.getItem(KEY);
    return value === "light" || value === "dark" ? value : "system";
  } catch {
    return "system"; // storage blocked (private mode, strict settings)
  }
}

function save(choice) {
  try {
    if (choice === "system") localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, choice);
  } catch {
    // Storage blocked: the choice still applies until the page reloads.
  }
}

function apply(choice) {
  if (choice === "system") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", choice);

  // Browser toolbar color on phones follows the page background.
  const paper = getComputedStyle(root).getPropertyValue("--paper").trim();
  themeMetas.forEach((meta) => {
    meta.content = choice === "system" ? meta.dataset.original : paper;
  });

  document.querySelectorAll("[data-theme-choice]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.themeChoice === choice));
  });
}

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-theme-choice]");
  if (!button) return;
  const choice = button.dataset.themeChoice;
  save(choice);
  apply(choice);
});

// Another tab changed the theme.
window.addEventListener("storage", (event) => {
  if (event.key === KEY) apply(savedChoice());
});

apply(savedChoice());
