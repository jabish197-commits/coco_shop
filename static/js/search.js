"use strict";
const filters = document.querySelector(".filters");
if (filters) {
  const search = filters.elements.q;
  const results = document.querySelector("#search-results");
  const status = document.querySelector("#search-status");
  let timer;
  let controller;
  let version = 0;
  const update = async (current) => {
    controller = new AbortController();
    const url = new URL(filters.action || window.location.href);
    url.search = new URLSearchParams(new FormData(filters)).toString();
    results.setAttribute("aria-busy", "true");
    status.textContent = "Searching…";
    try {
      const response = await fetch(url, {signal: controller.signal});
      if (!response.ok) throw new Error("Search failed");
      const page = new DOMParser().parseFromString(await response.text(), "text/html");
      const replacement = page.querySelector("#search-results");
      if (!replacement) throw new Error("Missing results");
      if (current !== version) return;
      results.replaceChildren(...replacement.childNodes);
      status.textContent = page.querySelector("#search-status").textContent;
      history.replaceState(null, "", url);
    } catch (error) {
      if (error.name !== "AbortError" && current === version) {
        status.textContent = "Could not update results. Press Enter in the search box to try again.";
      }
    } finally {
      if (current === version) results.setAttribute("aria-busy", "false");
    }
  };
  const schedule = () => {
    clearTimeout(timer);
    if (controller) controller.abort();
    const current = ++version;
    timer = setTimeout(() => update(current), 250);
  };
  search.addEventListener("input", schedule);
  filters.elements.category.addEventListener("change", schedule);
  document.querySelectorAll("[data-category]").forEach(link => {
    link.addEventListener("click", event => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      filters.elements.category.value = link.dataset.category;
      document.querySelectorAll("[data-category]").forEach(item => {
        const selected = item === link;
        item.classList.toggle("is-selected", selected);
        if (selected) item.setAttribute("aria-current", "true");
        else item.removeAttribute("aria-current");
      });
      schedule();
    });
  });
  // Enter in the search box and pagination retain normal navigation as a fallback.
}
