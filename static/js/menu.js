// Меню на details: Escape і дотик поза меню закривають; «/» відкриває пошук.
// The phone menu is a <details> element, so it already opens and closes without JS.
// This adds two expected behaviors: Escape closes it, and so does a tap outside.

const menus = [...document.querySelectorAll("details[data-menu]")];

function close(menu, returnFocus) {
  if (!menu.open) return;
  menu.open = false;
  if (returnFocus) menu.querySelector("summary").focus();
}

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  menus.forEach((menu) => close(menu, menu.contains(document.activeElement)));
});

document.addEventListener("click", (event) => {
  menus.forEach((menu) => {
    if (!menu.contains(event.target)) close(menu, false);
  });
});

// "/" jumps to search (Polish-3 3b), unless the person is typing somewhere or holds a modifier key.
// On Discover it focuses the page's own search field; elsewhere it opens "Find people" in the header
// (the icon from 80em, the field inside the menu below that). Without JS nothing changes.
function isVisible(element) {
  return Boolean(element && element.getClientRects().length);
}

document.addEventListener("keydown", (event) => {
  if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey || event.defaultPrevented) return;
  const target = event.target;
  if (target.closest?.("input, textarea, select, [contenteditable]:not([contenteditable='false'])")) return;

  let field = [document.getElementById("people-q"), document.getElementById("explore-q")].find(isVisible);
  if (!field) {
    const bar = document.querySelector("details.site-search");
    if (isVisible(bar?.querySelector("summary"))) {
      bar.open = true;
      field = bar.querySelector("input[type=search]");
    } else {
      const menu = document.querySelector("details.site-menu");
      if (menu) {
        menu.open = true;
        field = menu.querySelector(".site-search input[type=search]");
      }
    }
  }
  if (!field) return;
  event.preventDefault();
  field.focus();
});
