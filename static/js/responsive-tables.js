/**
 * Responsive Tables Helper
 * Ce script améliore l'affichage des tableaux sur mobiles et tablettes
 */

(function () {
  // Attendre que le document soit chargé
  document.addEventListener("DOMContentLoaded", function () {
    // Appliquer les ajustements une fois que les DataTables sont initialisées
    initResponsiveTables();

    // Observer les changements dans le DOM pour les tableaux dynamiques
    observeDOMChanges();
  });

  /**
   * Initialise les ajustements pour les tableaux responsifs
   */
  function initResponsiveTables() {
    // Ajuster la largeur du conteneur DataTables
    const dataTablesWrappers = document.querySelectorAll(".dataTables_wrapper");
    dataTablesWrappers.forEach((wrapper) => {
      wrapper.style.width = "100%";
      wrapper.style.maxWidth = "100%";

      // Ajuster les contrôles de pagination
      const paginationControls = wrapper.querySelectorAll(
        ".dataTables_paginate"
      );
      paginationControls.forEach((control) => {
        control.style.fontSize = "0.85rem";
        control.style.marginTop = "0.5rem";
      });

      // Ajuster les contrôles de longueur
      const lengthControls = wrapper.querySelectorAll(".dataTables_length");
      lengthControls.forEach((control) => {
        control.style.fontSize = "0.85rem";
        control.style.marginBottom = "0.5rem";
      });

      // Ajuster les contrôles de filtre
      const filterControls = wrapper.querySelectorAll(".dataTables_filter");
      filterControls.forEach((control) => {
        control.style.fontSize = "0.85rem";
        control.style.marginBottom = "0.5rem";
      });
    });

    // Ajouter des classes d'overflow aux tables
    const tableResponsiveContainers =
      document.querySelectorAll(".table-responsive");
    tableResponsiveContainers.forEach((container) => {
      // S'assurer que le conteneur a un overflow-x auto
      container.style.overflowX = "auto";
      container.style.maxWidth = "100%";

      // Ajuster les tables à l'intérieur
      const tables = container.querySelectorAll("table");
      tables.forEach((table) => {
        // Empêcher le tableau de dépasser
        table.style.width = "100%";
        table.style.maxWidth = "100%";
      });
    });

    // Ajouter des tooltips aux textes tronqués
    const truncatedTexts = document.querySelectorAll(
      ".long-text, .buyer-name, .event-link"
    );
    truncatedTexts.forEach((text) => {
      const content = text.textContent.trim();
      if (content && text.offsetWidth < text.scrollWidth) {
        // Le texte est tronqué, ajouter un tooltip
        text.setAttribute("title", content);
        text.style.cursor = "help";
      }
    });
  }

  /**
   * Observer les changements dans le DOM pour réappliquer les ajustements
   * lorsque des tableaux sont ajoutés ou modifiés dynamiquement
   */
  function observeDOMChanges() {
    // Créer un observateur pour détecter les changements dans le DOM
    const observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        // Si des nœuds ont été ajoutés
        if (mutation.addedNodes.length > 0) {
          // Vérifier s'il y a des tableaux parmi les nœuds ajoutés
          mutation.addedNodes.forEach(function (node) {
            if (node.nodeType === 1) {
              // Type 1 = élément
              // Si c'est un tableau ou contient un tableau
              if (node.tagName === "TABLE" || node.querySelector("table")) {
                // Réappliquer les ajustements
                setTimeout(initResponsiveTables, 100);
              }
            }
          });
        }
      });
    });

    // Observer le corps du document pour les changements
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }

  /**
   * Gestion de la rotation de l'écran pour réagencer les tableaux
   */
  window.addEventListener("resize", function () {
    // Délai pour éviter trop d'appels lors du redimensionnement
    if (window.resizeTimer) {
      clearTimeout(window.resizeTimer);
    }

    window.resizeTimer = setTimeout(function () {
      initResponsiveTables();
    }, 250);
  });
})();
