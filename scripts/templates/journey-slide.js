// Journey slides: one request followed step by step. Each step lights the
// diagram blocks it involves. Next: click on the diagram, →, ↓, Space,
// PageDown (remote clicker); back: ←, ↑, PageUp. The step is kept in the URL
// hash and shared by the language versions, so switching language keeps it.
(function () {
  const slides = [...document.querySelectorAll(".slide")].map((slide) => ({
    svg: slide.querySelector("svg.diagram"),
    steps: [...slide.querySelectorAll(".step")],
    count: slide.querySelector(".count"),
    slide,
  }));
  const total = slides[0].steps.length;
  let cur = 0;

  function go(i) {
    cur = Math.max(0, Math.min(total - 1, i));
    slides.forEach(({ svg, steps, count }) => {
      const keys = new Set(steps[cur].dataset.nodes.split(" "));
      steps.forEach((s, j) => {
        s.classList.toggle("on", j === cur);
        s.classList.toggle("done", j < cur);
        if (j === cur) s.setAttribute("aria-current", "step"); else s.removeAttribute("aria-current");
      });
      svg.classList.add("focus");
      svg.querySelectorAll("[data-n]").forEach((el) => {
        el.classList.toggle("on", el.dataset.n.split(" ").some((k) => keys.has(k)));
      });
      count.textContent = `${cur + 1} / ${total}`;
    });
    try { history.replaceState(null, "", location.pathname + location.search + "#" + (cur + 1)); } catch (e) {}
  }

  slides.forEach(({ svg, steps, slide }) => {
    steps.forEach((s, j) => s.addEventListener("click", () => go(j)));
    slide.querySelector(".prev").addEventListener("click", () => go(cur - 1));
    slide.querySelector(".next").addEventListener("click", () => go(cur + 1));
    svg.addEventListener("click", () => go(cur + 1));
  });
  document.addEventListener("keydown", (e) => {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    const next = ["ArrowRight", "ArrowDown", "PageDown", " "].includes(e.key);
    const prev = ["ArrowLeft", "ArrowUp", "PageUp"].includes(e.key);
    if (next) go(cur + 1);
    else if (prev) go(cur - 1);
    else if (e.key === "Home") go(0);
    else if (e.key === "End") go(total - 1);
    else return;
    e.preventDefault();
  });

  const start = parseInt(location.hash.slice(1), 10);
  go(Number.isFinite(start) ? start - 1 : 0);
})();
