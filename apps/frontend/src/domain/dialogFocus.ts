/** Keep keyboard traversal inside a modal, including browser-chrome boundaries. */
export function containDialogFocus(event: KeyboardEvent) {
  if (event.key !== "Tab") return;
  const dialog = event.currentTarget as HTMLElement;
  const buttons = Array.from(
    dialog.querySelectorAll<HTMLButtonElement>("button:not(:disabled)"),
  );
  const first = buttons[0],
    last = buttons[buttons.length - 1];
  if (!first || !last) {
    event.preventDefault();
    return;
  }
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
