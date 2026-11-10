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
