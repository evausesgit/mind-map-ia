(function () {
  document.querySelectorAll(".slide").forEach((slide) => {
    const svg = slide.querySelector("svg.diagram");
    const terms = [...slide.querySelectorAll(".term")];
    let pinned = null;
    function show(term) {
      const key = term && term.dataset.n;
      terms.forEach((t) => t.classList.toggle("on", t === term));
      svg.classList.toggle("focus", !!key);
      svg.querySelectorAll("[data-n]").forEach((el) => {
        el.classList.toggle("on", !!key && el.dataset.n.split(" ").includes(key));
      });
    }
    function toggle(term) { pinned = pinned === term ? null : term; show(pinned); }
    terms.forEach((t) => {
      t.addEventListener("mouseenter", () => show(t));
      t.addEventListener("mouseleave", () => show(pinned));
      t.addEventListener("focus", () => show(t));
      t.addEventListener("blur", () => show(pinned));
      t.addEventListener("click", () => toggle(t));
    });
    // Diagram blocks behave like their glossary term: hover previews, click pins.
    function termFor(node) {
      const keys = node.dataset.n.split(" ");
      return terms.find((t) => keys.includes(t.dataset.n)) || null;
    }
    const nodes = [...svg.querySelectorAll(".n[data-n]")].filter((n) => termFor(n));
    nodes.forEach((n) => {
      n.classList.add("clickable");
      n.setAttribute("tabindex", "0");
      n.setAttribute("role", "button");
      n.addEventListener("focus", () => show(termFor(n)));
      n.addEventListener("blur", () => show(pinned));
      n.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(termFor(n)); }
      });
    });
    function nodeAt(e) {
      const n = e.target.closest && e.target.closest(".n[data-n]");
      return n && nodes.includes(n) ? n : null;
    }
    svg.addEventListener("mouseover", (e) => { const n = nodeAt(e); show(n ? termFor(n) : pinned); });
    svg.addEventListener("mouseleave", () => show(pinned));
    svg.addEventListener("click", (e) => { const n = nodeAt(e); if (n) toggle(termFor(n)); });
  });
})();
