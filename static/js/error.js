// Error pages: "Go back" returns to the previous page in this tab. Without JS the link (when there is a
// same-site referrer) still works; the button version is hidden by .needs-js, and here when there is no history.
for (const el of document.querySelectorAll("[data-back]")) {
  if (window.history.length <= 1) {
    if (el.tagName === "BUTTON") el.hidden = true;
    continue;
  }
  el.addEventListener("click", (event) => {
    event.preventDefault();
    window.history.back();
  });
}
