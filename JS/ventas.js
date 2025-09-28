document.addEventListener("DOMContentLoaded", () => {
    // Lógica para ocultar/mostrar botones de admin
    const roles = JSON.parse(sessionStorage.getItem("roles") || "[]").map(r => r.toUpperCase());
    // Define los roles con permisos de administrador
    const esGerente = roles.includes("G");
    const esEncargado = roles.includes("E");
    const esEncargadoVentas = roles.includes("EV"); // Agregamos el rol de Subgerente
    // Si el usuario tiene alguno de los roles de administrador, muestra los botones
    if (esGerente || esEncargado || esEncargadoVentas) {
        document.querySelectorAll(".admin-only").forEach(elemento => {
            elemento.style.display = 'block';
        });
    }
    // Lógica para manejar clics en botones con data-url
    document.querySelectorAll(".container .button").forEach(button => {
        button.addEventListener("click", () => {
            // Muestra una alerta con el texto del botón
            alert("Función no implementada: " + button.textContent);
            
        });
    });
});