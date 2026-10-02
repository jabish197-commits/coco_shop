"use strict";
(() => {
  const key = "cocoa-bliss-favourites";
  let favourites = new Set();
  let timer;
  const read = () => {
    try {
      const saved = JSON.parse(localStorage.getItem(key) || "[]");
      favourites = new Set(Array.isArray(saved) ? saved.filter(id => typeof id === "string") : []);
    } catch (_) { favourites = new Set(); }
  };
  const render = () => {
    document.querySelectorAll("[data-favourite-count]").forEach(count => {
      count.textContent = favourites.size;
    });
    document.querySelectorAll(".favourite-button").forEach(button => {
      const selected = favourites.has(button.dataset.productId);
      button.hidden = false;
      button.setAttribute("aria-pressed", String(selected));
      button.setAttribute("aria-label", (selected ? "Remove " : "Add ") +
        button.dataset.productName + (selected ? " from favourites" : " to favourites"));
      button.title = selected ? "Remove from favourites" : "Save to favourites";
    });
    const grid = document.getElementById("favourites-grid");
    if (grid) {
      let visible = 0;
      grid.querySelectorAll(".product-card").forEach(card => {
        const id = card.querySelector(".favourite-button").dataset.productId;
        card.hidden = !favourites.has(id);
        if (!card.hidden) visible += 1;
      });
      grid.hidden = visible === 0;
      document.getElementById("favourites-empty").hidden = visible !== 0;
    }
  };
  read();
  render();
  document.addEventListener("click", event => {
    const button = event.target.closest(".favourite-button");
    if (!button) return;
    const id = button.dataset.productId;
    const selected = !favourites.has(id);
    selected ? favourites.add(id) : favourites.delete(id);
    let saved = true;
    try { localStorage.setItem(key, JSON.stringify([...favourites])); }
    catch (_) { saved = false; }
    render();
    const status = document.getElementById("favourite-status");
    status.textContent = saved
      ? button.dataset.productName + (selected ? " saved to favourites." : " removed from favourites.")
      : "Updated for this page. Your browser could not save favourites.";
    clearTimeout(timer);
    timer = setTimeout(() => { status.textContent = ""; }, 3000);
  });
  const results = document.getElementById("search-results");
  if (results) new MutationObserver(render).observe(results, {childList: true});
  window.addEventListener("storage", event => {
    if (event.key === key || event.key === null) { read(); render(); }
  });
})();
