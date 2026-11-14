// Спільнота: голоси без перезавантаження, згортання гілок, відповідь на конкретну відповідь.
// Community pages: upvotes, collapsing a branch of replies, and "Reply" that moves the composer under a reply.
// Every part works without this file: votes are plain POST forms, branches stay open, "Reply" links to
// ?reply_to=<id>#reply-form. One listener per event on the document, so rows added by "Load more" work too.
import { showToast } from "./toast.js";

const GENERIC_ERROR = "Could not save your vote. Try again.";

// ---------- Upvotes: optimistic, rolled back on any error ----------

function renderVote(form, voted, score) {
  const button = form.querySelector(".vote__button");
  const count = form.querySelector("[data-vote-count]");
  button.setAttribute("aria-pressed", String(voted));
  button.setAttribute("aria-label", voted ? button.dataset.labelOn : button.dataset.labelOff);
  form.querySelector("input[name=value]").value = voted ? "0" : "1";
  if (score !== null && score !== undefined) count.textContent = String(score);
}

document.addEventListener("submit", async (event) => {
  const form = event.target.closest?.("[data-vote-form]");
  if (!form) return;
  event.preventDefault();
  const button = form.querySelector(".vote__button");
  if (button.disabled) return;

  const wasVoted = button.getAttribute("aria-pressed") === "true";
  const before = Number(form.querySelector("[data-vote-count]").textContent);
  const body = new FormData(form); // value=1 (upvote) or 0 (take it back), plus the CSRF token
  renderVote(form, !wasVoted, Math.max(0, before + (wasVoted ? -1 : 1)));
  if (!wasVoted) {
    button.classList.remove("is-ticked");
    void button.offsetWidth; // restart the animation
    button.classList.add("is-ticked");
  }
  button.disabled = true;

  try {
    const response = await fetch(form.action, {
      method: "POST",
      body,
      headers: { "X-CSRFToken": body.get("csrfmiddlewaretoken"), Accept: "application/json" },
      credentials: "same-origin",
    });
    const data = await response.json().catch(() => null);
    if (!response.ok || !data?.ok) throw new Error(data?.message || form.dataset.error || GENERIC_ERROR);
    renderVote(form, data.voted, data.score); // the server's count wins
  } catch (error) {
    renderVote(form, wasVoted, before);
    showToast(error instanceof TypeError ? form.dataset.error || GENERIC_ERROR : error.message, { kind: "error" });
  } finally {
    button.disabled = false;
  }
});

// ---------- Collapse a branch ----------

function armCollapse(root = document) {
  root.querySelectorAll("[data-collapse][hidden]").forEach((button) => { button.hidden = false; });
}

document.addEventListener("click", (event) => {
  const button = event.target.closest?.("[data-collapse]");
  if (!button) return;
  const branch = document.getElementById(button.getAttribute("aria-controls"));
  if (!branch) return;
  const open = button.getAttribute("aria-expanded") !== "true";
  button.setAttribute("aria-expanded", String(open));
  button.querySelector("[data-collapse-label]").textContent = open ? button.dataset.labelOpen : button.dataset.labelClosed;
  branch.hidden = !open;
  if (open) {
    branch.classList.remove("is-opening");
    void branch.offsetWidth;
    branch.classList.add("is-opening");
  }
});

armCollapse();
// "Load more" appends replies: show their collapse buttons too.
const replyList = document.querySelector(".replies[data-feed-list]");
if (replyList) new MutationObserver(() => armCollapse(replyList)).observe(replyList, { childList: true });

// ---------- "Reply" moves the composer under the reply ----------

const replyForm = document.querySelector("[data-reply-form]");
const replyBox = replyForm?.closest("#reply-form");

if (replyForm && replyBox) {
  const parentInput = replyForm.querySelector("[data-reply-parent]");
  const title = replyForm.querySelector("[data-reply-title]");
  const cancel = replyForm.querySelector("[data-reply-cancel]");
  const home = document.createComment("reply-form-home");
  replyBox.before(home);

  function placeUnder(reply, id, name) {
    parentInput.value = id;
    title.textContent = name ? title.dataset.to.replace("%(name)s", name) : title.dataset.toReply;
    cancel.hidden = false;
    reply.querySelector(":scope > .reply__card").after(replyBox);
    replyBox.classList.add("is-inline");
    replyForm.querySelector("textarea")?.focus();
  }

  function placeHome() {
    parentInput.value = "";
    title.textContent = title.dataset.default;
    cancel.hidden = true;
    home.after(replyBox);
    replyBox.classList.remove("is-inline");
  }

  document.addEventListener("click", (event) => {
    const link = event.target.closest?.("[data-reply-to]");
    if (link) {
      event.preventDefault();
      const reply = link.closest(".reply");
      if (reply) placeUnder(reply, link.dataset.replyTo, link.dataset.replyName);
      return;
    }
    if (event.target.closest?.("[data-reply-cancel]")) {
      event.preventDefault();
      placeHome();
      replyForm.querySelector("textarea")?.focus();
    }
  });
}
