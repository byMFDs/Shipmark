// Footer language select: choosing a language sends the form at once. Without this file the "Change" button
// next to the select does the same (the button is hidden only when JS runs, see components.css).
document.addEventListener("change", (event) => {
  const select = event.target.closest?.("[data-autosubmit]");
  if (!select || !select.form) return;
  select.form.requestSubmit ? select.form.requestSubmit() : select.form.submit();
});
