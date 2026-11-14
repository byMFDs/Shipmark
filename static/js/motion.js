// Анімації: пауза циклів поза екраном і у фоні, поява при прокрутці, лічба чисел.
// Ambient motion helpers (styles in css/motion.css).
// - [data-loop]: loops inside run only while the block is on screen (.is-inview).
// - [data-reveal]: children fade in once when the block scrolls into view (.is-revealed).
// - html.is-paused while the tab is hidden, so nothing animates in the background.
// Without this script nothing loops and nothing is hidden.

const root = document.documentElement;
const loops = document.querySelectorAll("[data-loop]");
const reveals = document.querySelectorAll("[data-reveal]");

document.addEventListener("visibilitychange", () => {
  root.classList.toggle("is-paused", document.hidden);
});

if (!("IntersectionObserver" in window)) {
  loops.forEach((el) => el.classList.add("is-inview"));
  reveals.forEach((el) => el.classList.add("is-revealed"));
} else {
  const loopObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => entry.target.classList.toggle("is-inview", entry.isIntersecting));
  }, { threshold: 0.1 });
  loops.forEach((el) => loopObserver.observe(el));

  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-revealed");
      observer.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -10% 0px" });
  reveals.forEach((el) => revealObserver.observe(el));
}

// Count-up: [data-count] numbers (profile stats) count from 0 to the number already in the HTML, once, when
// they come into view. Skipped with reduced motion and for numbers that are not plain integers ("1,204").
const counters = document.querySelectorAll("[data-count]");
const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function countUp(el) {
  const target = Number.parseInt(el.textContent.trim(), 10);
  if (!Number.isInteger(target) || target <= 0 || String(target) !== el.textContent.trim()) return;
  const start = performance.now();
  const duration = Math.min(900, 400 + target * 40);
  const step = (now) => {
    const t = Math.min(1, (now - start) / duration);
    const eased = 1 - (1 - t) ** 3;
    // A script elsewhere (follow button) may have changed the number meanwhile: then stop and leave it.
    if (el.dataset.countAt !== undefined && el.textContent !== el.dataset.countAt) return;
    el.textContent = el.dataset.countAt = String(Math.round(target * eased));
    if (t < 1) requestAnimationFrame(step);
    else delete el.dataset.countAt;
  };
  requestAnimationFrame(step);
}

if (!calm && counters.length && "IntersectionObserver" in window) {
  const countObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      observer.unobserve(entry.target);
      countUp(entry.target);
    });
  }, { threshold: 0.6 });
  counters.forEach((el) => countObserver.observe(el));
}
