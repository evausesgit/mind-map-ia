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
    terms.forEach((t) => {
      t.addEventListener("mouseenter", () => show(t));
      t.addEventListener("mouseleave", () => show(pinned));
      t.addEventListener("focus", () => show(t));
      t.addEventListener("blur", () => show(pinned));
      t.addEventListener("click", () => { pinned = pinned === t ? null : t; show(pinned); });
    });
  });
})();
