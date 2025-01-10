// Bouton "Retour en haut"
const backToTopButton = document.getElementById("backToTop");

// Afficher le bouton lorsque l'utilisateur fait défiler
window.addEventListener("scroll", () => {
  if (window.scrollY > 200) {
    backToTopButton.style.display = "block";
  } else {
    backToTopButton.style.display = "none";
  }
});

// Remonter en haut de la page lorsque l'utilisateur clique
backToTopButton.addEventListener("click", () => {
  window.scrollTo({
    top: 0,
    behavior: "smooth", // Animation fluide
  });
});

// Animation d'apparition progressive des éléments (scroll-animated)
const observerOptions = {
  root: null, // Fenêtre visible par défaut
  rootMargin: "0px", // Pas de marge autour du viewport
  threshold: 0.1, // Élément visible à 10% avant déclenchement
};

const observer = new IntersectionObserver((entries, observer) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible"); // Ajouter la classe visible
      observer.unobserve(entry.target); // Arrêter d'observer cet élément
    }
  });
});

// Appliquer l'animation aux éléments avec la classe scroll-animated
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".scroll-animated").forEach((element) => {
    observer.observe(element); // Observer chaque élément
  });
});

// Animation de comptage pour les statistiques
const counters = document.querySelectorAll(".counter");

const animateCounters = () => {
  counters.forEach((counter) => {
    const updateCount = () => {
      const target = +counter.getAttribute("data-target"); // Valeur cible
      const count = +counter.innerText; // Valeur actuelle
      const increment = target / 100; // Diviser en 100 étapes pour un effet fluide

      if (count < target) {
        counter.innerText = Math.ceil(count + increment); // Augmenter la valeur
        setTimeout(updateCount, 30); // Répéter toutes les 30 ms
      } else {
        counter.innerText = target; // Assurer une valeur exacte
      }
    };

    updateCount();
  });
};

// Observer les éléments des statistiques pour démarrer le comptage lorsqu'ils deviennent visibles
const countersObserverOptions = {
  root: null, // Fenêtre visible par défaut
  threshold: 0.2, // Élément visible à 20% avant déclenchement
};

const countersObserver = new IntersectionObserver((entries, observer) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      animateCounters(); // Lancer l'animation de comptage
      observer.unobserve(entry.target); // Arrêter d'observer cet élément
    }
  });
});

// Observer chaque compteur pour l'animation
counters.forEach((counter) => countersObserver.observe(counter));
