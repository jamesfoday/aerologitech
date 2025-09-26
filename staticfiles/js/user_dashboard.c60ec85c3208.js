// Optional UX: focus the first action for keyboard users and add a tiny greet effect
document.addEventListener("DOMContentLoaded", () => {
  const firstAction = document.querySelector(".ud-actions .ud-action");
  firstAction && firstAction.setAttribute("tabindex", "0");
});
