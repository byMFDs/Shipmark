// Після невдалої форми фокус переходить на підсумок помилок.
// After a failed form submit the page reloads. Move focus to the error summary so a screen reader
// reads it first and a keyboard user starts at the problems. Without JS the summary is still on the page.

const summary = document.querySelector("[data-error-summary]");
if (summary) summary.focus();
