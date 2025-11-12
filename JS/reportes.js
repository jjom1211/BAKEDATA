document.addEventListener("DOMContentLoaded", () => {
    // Lógica para ocultar/mostrar botones de admin
    const roles = JSON.parse(sessionStorage.getItem("roles") || "[]").map(r => r.toUpperCase());
    const esGerente = roles.includes("G");
    // Si el usuario tiene alguno de los roles de administrador, muestra los botones
    if (esGerente) {
        document.querySelectorAll(".admin-only").forEach(elemento => {
            elemento.style.display = 'block';
        });
    }

    // Lógica para manejar clics en botones con data-url
    document.querySelectorAll(".container .button").forEach(button => {
        button.addEventListener("click", () => {
            if (button.dataset.url) {
                window.location.href = button.dataset.url;
            }
        });
    });
});