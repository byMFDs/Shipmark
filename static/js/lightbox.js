// Image viewer for community posts, on the native <dialog>: Escape closes (the browser does it), arrow keys and
// swipes move between the images of the same post, focus goes back to the tile that opened it.
// Without this file every tile is a plain link to the image.

const dialog = document.querySelector("[data-lightbox]");

if (dialog && typeof dialog.showModal === "function") {
  const img = dialog.querySelector("[data-lightbox-img]");
  const count = dialog.querySelector("[data-lightbox-count]");
  const altText = dialog.querySelector("[data-lightbox-alt]");
  const prev = dialog.querySelector("[data-lightbox-prev]");
  const next = dialog.querySelector("[data-lightbox-next]");
  let tiles = [];
  let index = 0;
  let opener = null;

  function show(at) {
    index = (at + tiles.length) % tiles.length;
    const tile = tiles[index];
    const thumb = tile.querySelector("img");
    img.removeAttribute("src"); // no stale picture while the next one loads
    img.width = Number(tile.dataset.width) || thumb.naturalWidth;
    img.height = Number(tile.dataset.height) || thumb.naturalHeight;
    img.alt = thumb.alt;
    img.src = tile.dataset.full;
    altText.textContent = thumb.alt;
    count.textContent = tiles.length > 1 ? `${index + 1} / ${tiles.length}` : "";
    prev.hidden = next.hidden = tiles.length < 2;
  }

  document.addEventListener("click", (event) => {
    const tile = event.target.closest?.("[data-gallery] [data-full]");
    if (!tile || event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return;
    event.preventDefault();
    tiles = [...tile.closest("[data-gallery]").querySelectorAll("[data-full]")];
    opener = tile;
    show(tiles.indexOf(tile));
    dialog.showModal();
    dialog.querySelector("[data-lightbox-close]").focus();
  });

  prev.addEventListener("click", () => show(index - 1));
  next.addEventListener("click", () => show(index + 1));
  dialog.querySelector("[data-lightbox-close]").addEventListener("click", () => dialog.close());

  // A click on the dark area around the picture closes it, like Escape.
  let swiped = false;
  dialog.addEventListener("click", (event) => {
    if (swiped) { swiped = false; return; } // the click that ends a swipe is not a "close"
    if (event.target === dialog || event.target.classList.contains("lightbox__figure")) dialog.close();
  });

  dialog.addEventListener("keydown", (event) => {
    if (tiles.length < 2) return;
    if (event.key === "ArrowLeft") { event.preventDefault(); show(index - 1); }
    if (event.key === "ArrowRight") { event.preventDefault(); show(index + 1); }
  });

  let startX = null;
  let startY = null;
  dialog.addEventListener("pointerdown", (event) => { swiped = false; startX = event.clientX; startY = event.clientY; });
  dialog.addEventListener("pointerup", (event) => {
    if (startX === null || tiles.length < 2) return;
    const dx = event.clientX - startX;
    const dy = event.clientY - startY;
    startX = startY = null;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
      swiped = true;
      show(index + (dx < 0 ? 1 : -1));
    }
  });

  dialog.addEventListener("close", () => {
    img.removeAttribute("src");
    opener?.focus();
    opener = null;
  });
}
