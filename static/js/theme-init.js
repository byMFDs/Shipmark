// Runs before the first paint: applies the saved theme (no flash) and marks that JS works.
// A separate file (not inline) so the Content-Security-Policy can forbid inline scripts.
(function () {
  var root = document.documentElement;
  root.classList.add("js");
  try {
    var theme = localStorage.getItem("theme");
    if (theme === "light" || theme === "dark") root.setAttribute("data-theme", theme);
  } catch (e) {}
})();
