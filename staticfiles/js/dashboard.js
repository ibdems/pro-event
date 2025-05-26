/**
 * Fonctions JavaScript communes pour le tableau de bord
 */

/**
 * Initialise un tableau DataTable avec des options par défaut
 * @param {string} selector - Sélecteur CSS pour les tables à initialiser
 * @param {object} options - Options supplémentaires pour DataTables
 */
function initializeDataTable(selector, options = {}) {
  // Options par défaut
  const defaultOptions = {
    responsive: true,
    language: {
      url: "//cdn.datatables.net/plug-ins/1.11.5/i18n/fr-FR.json",
    },
    pageLength: 25,
    lengthMenu: [
      [10, 25, 50, 100, -1],
      [10, 25, 50, 100, "Tous"],
    ],
    dom: '<"d-flex justify-content-between align-items-center mb-3"<"dataTables_info"i><"dataTables_length"l>>t<"d-flex justify-content-between align-items-center mt-3"<"dataTables_info"p><"export-options"B>>',
    buttons: [
      {
        extend: "excel",
        className: "btn btn-outline-success btn-sm",
        text: '<i class="fas fa-file-excel me-1"></i>Excel',
      },
      {
        extend: "csv",
        className: "btn btn-outline-primary btn-sm",
        text: '<i class="fas fa-file-csv me-1"></i>CSV',
      },
      {
        extend: "pdf",
        className: "btn btn-outline-danger btn-sm",
        text: '<i class="fas fa-file-pdf me-1"></i>PDF',
      },
      {
        extend: "print",
        className: "btn btn-outline-secondary btn-sm",
        text: '<i class="fas fa-print me-1"></i>Imprimer',
      },
    ],
  };

  // Fusionner les options par défaut avec les options spécifiées
  const mergedOptions = { ...defaultOptions, ...options };

  try {
    // Initialiser DataTables sur les éléments correspondant au sélecteur
    const tables = $(selector);
    if (tables.length) {
      return tables.DataTable(mergedOptions);
    } else {
      console.warn(`Aucun élément trouvé pour le sélecteur: ${selector}`);
      return null;
    }
  } catch (error) {
    console.error("Erreur lors de l'initialisation de DataTable:", error);
    return null;
  }
}

// Autres fonctions utilitaires pour le tableau de bord peuvent être ajoutées ici...
