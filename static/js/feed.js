// «Показати ще» у стрічці: дописує наступну сторінку з JSON.
// "Load more" on /feed/. Without JS the same link opens the next page.
// Asks the feed view for JSON ({html, next_url}) and appends the rows.
import { showToast } from "./toast.js";

const list = document.querySelector("[data-feed-list]");
const pager = document.querySelector("[data-feed-pager]");
const more = pager?.querySelector("[data-load-more]");

if (list && more) {
  more.addEventListener("click", async (event) => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return; // let "open in new tab" work
    event.preventDefault();
    if (more.disabled || more.getAttribute("aria-busy") === "true") return;

    more.setAttribute("aria-busy", "true");
    try {
      const response = await fetch(more.href, {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error();
      const data = await response.json();

      const before = list.children.length;
      list.insertAdjacentHTML("beforeend", data.html); // html is rendered (and escaped) by Django templates
      list.children[before]?.focus({ preventScroll: false }); // keyboard users continue where the new rows start

      pager.querySelector("[data-prev]")?.remove(); // "Newer" makes no sense after appending
      if (data.next_url) {
        more.href = data.next_url;
      } else {
        more.remove();
        pager.remove();
      }
    } catch {
      showToast(more.dataset.error, { kind: "error" });
    } finally {
      more.removeAttribute("aria-busy");
    }
  });
}
