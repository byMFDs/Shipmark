// Живе прев'ю картки профілю на сторінці налаштувань.
// Live preview on the settings page: the profile card follows the fields as you type.
// Nothing is saved here and nothing is sent: it only copies text. Without JS the card shows the saved values.
// A chosen picture is read in the browser (FileReader -> data: URL), so it never leaves the device until Save.

const card = document.querySelector("[data-profile-preview]");

if (card) {
  const field = (name) => document.getElementById(`id_${name}`);
  const slot = (name) => card.querySelector(`[data-pv="${name}"]`);
  const avatarSlot = card.querySelector("[data-pv-avatar]");
  const nameSlot = slot("display_name");

  function initials(text) {
    const parts = text.split(/[\s_.-]+/).filter(Boolean);
    return (parts.slice(0, 2).map((p) => p[0]).join("") || "?").toUpperCase();
  }

  function setText(name, value) {
    const el = slot(name);
    if (!el) return;
    el.textContent = value;
    el.hidden = value === "";
  }

  function bind(name, read) {
    const input = field(name);
    if (!input) return;
    const update = () => setText(name, read(input).trim());
    input.addEventListener("input", update);
    input.addEventListener("change", update);
  }

  // Name: falls back to the username while the field is empty.
  const nameInput = field("display_name");
  const username = nameSlot?.dataset.fallback || "";
  const showName = () => {
    const value = nameInput.value.trim() || username;
    nameSlot.textContent = value;
    return value;
  };
  if (nameInput && nameSlot) {
    nameInput.addEventListener("input", () => {
      showName();
      if (avatarSlot?.querySelector(".avatar--initials")) showInitials();
    });
  }

  function showInitials() {
    const span = document.createElement("span");
    span.className = "avatar avatar--96 avatar--initials";
    span.setAttribute("role", "img");
    span.setAttribute("aria-label", nameSlot.textContent);
    span.textContent = initials(nameSlot.textContent);
    avatarSlot.replaceChildren(span);
  }

  bind("headline", (input) => input.value);
  bind("location", (input) => input.value);
  bind("status", (select) => (select.value ? select.selectedOptions[0].text : ""));

  // Picture: a chosen file replaces the avatar; "remove" shows initials.
  const picture = document.querySelector("[data-preview-file=avatar]");
  const remove = field("remove_avatar");
  picture?.addEventListener("change", () => {
    const file = picture.files[0];
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      const img = document.createElement("img");
      img.className = "avatar avatar--96";
      img.width = img.height = 96;
      img.alt = nameSlot.textContent;
      img.src = reader.result;
      avatarSlot.replaceChildren(img);
      if (remove) remove.checked = false;
    });
    reader.readAsDataURL(file);
  });
  remove?.addEventListener("change", () => {
    if (remove.checked) showInitials();
  });
}
