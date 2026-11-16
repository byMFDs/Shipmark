// Стовпчики аптайму: поява при прокрутці й керування стрілками.
// Uptime bars: [data-uptime-bars] rise once when they scroll into view (.is-in, see motion.css), and the 30 bars
// become ONE tab stop with the arrow keys moving between them (without JS each bar is focusable by itself).
// Never fetches anything: every number is already in the HTML.

const blocks = document.querySelectorAll("[data-uptime-bars]");

blocks.forEach((block) => {
  const bars = [...block.querySelectorAll(".uptime-bars__days > .uptime-bar")];
  if (!bars.length) return;

  bars.forEach((bar, i) => { bar.tabIndex = i === 0 ? 0 : -1; });
  const move = (to) => {
    const next = bars[Math.max(0, Math.min(bars.length - 1, to))];
    bars.forEach((bar) => { bar.tabIndex = bar === next ? 0 : -1; });
    next.focus();
  };
  block.addEventListener("keydown", (event) => {
    const at = bars.indexOf(event.target);
    if (at < 0) return;
    const to = { ArrowRight: at + 1, ArrowLeft: at - 1, Home: 0, End: bars.length - 1 }[event.key];
    if (to === undefined) return;
    event.preventDefault();
    move(to);
  });
  // A click or tap on a bar makes it the current one, so a later Tab starts there.
  block.addEventListener("focusin", (event) => {
    if (!bars.includes(event.target)) return;
    bars.forEach((bar) => { bar.tabIndex = bar === event.target ? 0 : -1; });
  });
});

if (blocks.length) {
  if (!("IntersectionObserver" in window)) {
    blocks.forEach((block) => block.classList.add("is-in"));
  } else {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in");
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.4 });
    blocks.forEach((block) => observer.observe(block));
  }
}
