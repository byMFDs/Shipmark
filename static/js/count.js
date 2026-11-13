// "<n> people joined" in the header: the number counts up from 0 once, on load (about 800 ms), and ends on the
// exact text the server wrote. Reduced motion, a compact number ("128K") or no JS: the final number at once.
// The sentence for screen readers is a separate hidden text with the full number, so nothing is read twice.

const numbers = document.querySelectorAll("[data-count-to]");
const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (!calm && numbers.length) {
  const format = new Intl.NumberFormat(document.documentElement.lang || undefined);
  numbers.forEach((el) => {
    const target = Number.parseInt(el.dataset.countTo, 10);
    const final = el.textContent;
    if (!Number.isInteger(target) || target <= 0) return;
    const start = performance.now();
    const duration = 800;
    const step = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - (1 - t) ** 3;
      el.textContent = t < 1 ? format.format(Math.round(target * eased)) : final;
      if (t < 1) requestAnimationFrame(step);
    };
    el.textContent = format.format(0);
    requestAnimationFrame(step);
  });
}
