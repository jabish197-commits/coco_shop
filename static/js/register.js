"use strict";
document.querySelectorAll(".password-toggle").forEach((button) => {
  const input = document.getElementById(button.dataset.target);
  button.hidden = false;
  input.classList.add("has-toggle");
  const label = document.querySelector('label[for="' + input.id + '"]').textContent.replace(/:$/, "").toLowerCase();
  button.addEventListener("click", () => {
    const visible = input.type === "password";
    input.type = visible ? "text" : "password";
    button.textContent = visible ? "Hide" : "Show";
    button.setAttribute("aria-pressed", String(visible));
    button.setAttribute("aria-label", (visible ? "Hide " : "Show ") + label);
  });
});
const password = document.getElementById("id_password1");
const confirmation = document.getElementById("id_password2");
if (password && confirmation) {
  const lengthHint = document.getElementById("password-length");
  const matchHint = document.getElementById("password-match");
  const update = () => {
    const length = Array.from(password.value).length;
    lengthHint.textContent = !length ? "" : length < 8
      ? "Add " + (8 - length) + " more characters to reach 8."
      : "Minimum length reached.";
    const matches = password.value === confirmation.value;
    confirmation.setCustomValidity(confirmation.value && !matches
      ? "Type the same password in both boxes." : "");
    matchHint.textContent = !confirmation.value ? "" : matches
      ? "Passwords match." : "Passwords do not match yet.";
    matchHint.dataset.state = !confirmation.value ? "" : matches ? "success" : "error";
  };
  password.addEventListener("input", update);
  confirmation.addEventListener("input", update);
  update();
}
