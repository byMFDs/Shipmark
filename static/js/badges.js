// Official and moderator badges (one component: templates/includes/user_marks.html + badge_popover.html).
// Hover or focus shows a short tooltip (CSS). A click or tap opens one shared panel filled from the badge's
// <template>: a popover next to the badge, a bottom sheet on small screens. Escape, the close button and a click
// outside close it, and focus goes back to the badge. Without this file the badge is a labelled button with the
// same tooltip.

const panel = document.querySelector("[data-badge-pop]");

if (panel) {
  const body = panel.querySelector("[data-badge-pop-body]");
  const closeButton = panel.querySelector("[data-badge-pop-close]");
  const sheet = window.matchMedia("(max-width: 47.99em)");
  let opener = null;

  function place(button) {
    panel.classList.toggle("is-sheet", sheet.matches);
    if (sheet.matches) {
      panel.style.removeProperty("--pop-x");
      panel.style.removeProperty("--pop-y");
      return;
    }
    const rect = button.getBoundingClientRect();
    const width = panel.offsetWidth;
    const height = panel.offsetHeight;
    const rtl = getComputedStyle(button).direction === "rtl";
    let x = rtl ? rect.right - width : rect.left - 12;
    x = Math.max(8, Math.min(x, window.innerWidth - width - 8));
    let y = rect.bottom + 8;
    if (y + height > window.innerHeight - 8 && rect.top - height - 8 > 8) y = rect.top - height - 8;
    panel.style.setProperty("--pop-x", `${Math.round(x)}px`);
    panel.style.setProperty("--pop-y", `${Math.round(y)}px`);
  }

  function open(button) {
    const source = document.getElementById(`badge-tpl-${button.dataset.badge}`);
    if (!source) return;
    if (opener && opener !== button) close(false);
    body.replaceChildren(source.content.cloneNode(true));
    const since = body.querySelector("[data-badge-since]");
    if (since) {
      since.textContent = button.dataset.since || "";
      since.closest("[data-badge-since-row]").hidden = !button.dataset.since;
    }
    opener = button;
    button.setAttribute("aria-expanded", "true");
    panel.hidden = false;
    place(button);
    panel.classList.remove("is-open");
    void panel.offsetWidth; // restart the open animation
    panel.classList.add("is-open");
    panel.focus();
  }

  function close(returnFocus = true) {
    if (panel.hidden) return;
    panel.hidden = true;
    panel.classList.remove("is-open");
    if (opener) {
      opener.setAttribute("aria-expanded", "false");
      if (returnFocus) opener.focus();
    }
    opener = null;
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest?.("[data-badge]");
    if (button) {
      event.preventDefault();
      event.stopPropagation();
      if (opener === button) close();
      else open(button);
      return;
    }
    if (!panel.hidden && !panel.contains(event.target)) close(false);
  });

  closeButton.addEventListener("click", () => close());

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !panel.hidden) {
      event.preventDefault();
      close();
    }
  });

  // Keep the panel next to its badge; a scroll that moves the badge away closes it.
  window.addEventListener("resize", () => { if (opener) place(opener); });
  window.addEventListener("scroll", () => {
    if (!opener || sheet.matches) return;
    const rect = opener.getBoundingClientRect();
    if (rect.bottom < 0 || rect.top > window.innerHeight) close(false);
    else place(opener);
  }, { passive: true });
}
