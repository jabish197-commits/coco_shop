"use strict";
// Keep native HTML validation and server-side validation as the source of truth.
document.querySelectorAll('textarea[maxlength]').forEach((field) => {
  const counter = document.createElement("small");
  counter.setAttribute("aria-live", "polite");
  field.after(counter);
  const update = () => { counter.textContent = field.value.length + " / " + field.maxLength; };
  field.addEventListener("input", update);
  update();
});
