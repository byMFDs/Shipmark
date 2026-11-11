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
