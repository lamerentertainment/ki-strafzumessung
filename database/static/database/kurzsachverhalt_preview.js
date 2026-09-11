/**
 * Hover-Vorschau für den Kurzsachverhalt in Urteilslisten.
 *
 * Reagiert auf Mausbewegungen über Zeilen mit [data-kurzsachverhalt]
 * und blendet ein kompaktes, rand-sensitives Vorschaufenster ein.
 */
document.addEventListener("DOMContentLoaded", function () {
  const preview = document.createElement("div");
  preview.id = "kurzsachverhalt-preview";
  preview.className = "kurzsachverhalt-hovercard";
  preview.setAttribute("role", "tooltip");
  preview.innerHTML = `
    <div class="hovercard-header">
      <div class="d-flex justify-content-between align-items-baseline gap-2">
        <span class="hovercard-title fw-bold"></span>
        <span class="hovercard-meta text-body-secondary small"></span>
      </div>
      <div class="hovercard-delikt small mt-1"></div>
    </div>
    <div class="hovercard-body mt-2"></div>
    <div class="hovercard-footer small text-body-secondary border-top pt-2 mt-2 d-flex justify-content-between align-items-center">
      <span>Urteilsdetails ansehen</span>
      <span class="text-primary fw-bold">→</span>
    </div>
  `;
  document.body.appendChild(preview);

  let hoverTimer = null;
  let activeRow = null;

  function positionPreview(e) {
    const cardWidth = 440;
    const padding = 16;
    let x = e.clientX + 16;
    let y = e.clientY + 16;

    // Horizontale Begrenzung (Viewport)
    if (x + cardWidth > window.innerWidth - padding) {
      x = e.clientX - cardWidth - 16;
    }
    if (x < padding) x = padding;

    // Vertikale Begrenzung (Viewport)
    const cardHeight = preview.offsetHeight || 160;
    if (y + cardHeight > window.innerHeight - padding) {
      y = e.clientY - cardHeight - 16;
    }
    if (y < padding) y = padding;

    preview.style.left = `${x}px`;
    preview.style.top = `${y}px`;
  }

  function showPreview(row, e) {
    activeRow = row;
    const fallNr = row.dataset.fallNr || "";
    const gericht = row.dataset.gericht || "";
    const datum = row.dataset.urteilsdatum || "";
    const delikt = row.dataset.hauptdelikt || "";
    const text = row.dataset.kurzsachverhalt || "";

    preview.querySelector(".hovercard-title").textContent = fallNr ? `Fall ${fallNr}` : "Kurzsachverhalt";
    preview.querySelector(".hovercard-meta").textContent = [gericht, datum].filter(Boolean).join(", ");
    preview.querySelector(".hovercard-delikt").textContent = delikt ? `Hauptdelikt: ${delikt}` : "";
    preview.querySelector(".hovercard-body").textContent = text;

    positionPreview(e);
    preview.classList.add("visible");
  }

  function hidePreview() {
    clearTimeout(hoverTimer);
    activeRow = null;
    preview.classList.remove("visible");
  }

  // Event-Delegation am Tabellenkörper für Performanz und Verträglichkeit mit Sortierung/Filterung
  const tbody = document.querySelector("[data-urteilsliste]");
  if (tbody) {
    tbody.addEventListener("mouseover", function (e) {
      const row = e.target.closest("tr[data-kurzsachverhalt]");
      if (row) {
        if (row !== activeRow) {
          clearTimeout(hoverTimer);
          hoverTimer = setTimeout(() => {
            showPreview(row, e);
          }, 150);
        }
      } else {
        hidePreview();
      }
    });

    tbody.addEventListener("mousemove", function (e) {
      if (activeRow && preview.classList.contains("visible")) {
        positionPreview(e);
      }
    });

    tbody.addEventListener("mouseout", function (e) {
      const related = e.relatedTarget;
      const row = e.target.closest("tr[data-kurzsachverhalt]");
      if (row && (!related || !row.contains(related))) {
        hidePreview();
      }
    });
  }

  // Bei Scrollen oder ESC-Taste Vorschau schliessen
  window.addEventListener("scroll", hidePreview, { passive: true });
  window.addEventListener("keydown", function (e) {
    if (e.key === "Escape") hidePreview();
  });
});
