(function () {
  function toggleThemePreference() {
    var root = document.documentElement;
    var next = !root.classList.contains("dark");
    root.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-theme-toggle]");
    if (button) toggleThemePreference();
  });
})();
