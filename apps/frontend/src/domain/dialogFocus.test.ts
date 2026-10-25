import { expect, it } from "vitest";
import { containDialogFocus } from "./dialogFocus";

it("wraps keyboard focus across enabled modal actions without activating them", () => {
  const dialog = document.createElement("dialog");
  dialog.innerHTML =
    "<button>Stay</button><button disabled>Saving</button><button>Leave</button>";
  document.body.append(dialog);
  dialog.addEventListener("keydown", containDialogFocus);
  const [first, , last] = dialog.querySelectorAll("button");
  try {
    first!.focus();
    const backward = new KeyboardEvent("keydown", {
      key: "Tab",
      shiftKey: true,
      bubbles: true,
      cancelable: true,
    });
    first!.dispatchEvent(backward);
    expect(document.activeElement).toBe(last);
    expect(backward.defaultPrevented).toBe(true);
    const forward = new KeyboardEvent("keydown", {
      key: "Tab",
      bubbles: true,
      cancelable: true,
    });
    last!.dispatchEvent(forward);
    expect(document.activeElement).toBe(first);
    expect(forward.defaultPrevented).toBe(true);
  } finally {
    dialog.remove();
  }
});
