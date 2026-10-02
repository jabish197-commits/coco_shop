"use strict";
document.querySelectorAll(".cart-row input[type=number]").forEach((input) => {
  input.addEventListener("change", () => {
    input.setCustomValidity(input.validity.rangeOverflow || input.validity.rangeUnderflow
      ? "Choose between 1 and 99." : "");
  });
});
