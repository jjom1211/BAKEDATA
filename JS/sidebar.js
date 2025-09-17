window.addEventListener("DOMContentLoaded", () => {
    // Roles desde sessionStorage (ejemplo: ["L", "V"])
    const roles = JSON.parse(sessionStorage.getItem("roles") || "[]")
        .map(r => r.toUpperCase());

    if (!roles.length) {
        window.location.href = "/";
        return;
    }

    const esGerente = roles.includes("G");
    const esEncargado = roles.includes("E");

    // Contenedor de la sidebar
    const sidebarContent = document.querySelector(".sidebar-content");

    // Guardamos la plantilla del sidebar original
    const plantilla = document.querySelectorAll(".menu-item.doble-opcion");

    // Limpiamos el sidebar antes de reconstruir (dejamos solo logo y botón salir)
    const logo = sidebarContent.querySelector(".sidebar-logo");
    const salir = sidebarContent.querySelector(".return-login").closest(".menu-item");

    sidebarContent.innerHTML = "";
    sidebarContent.appendChild(logo);

    // Recorremos cada menu-item de la plantilla
    plantilla.forEach(menuItem => {
        const btnPrincipal = menuItem.querySelector(".ir-item");
        if (!btnPrincipal) return;

        // Normalizar texto (quitar acentos, mayúsculas)
        const texto = btnPrincipal.textContent
            .trim()
            .normalize("NFD") // separar acentos
            .replace(/[\u0300-\u036f]/g, "") // quitar diacríticos
            .toUpperCase();

        let rolAsociado = null;

        if (texto.includes("ALMACEN")) rolAsociado = "A";
        if (texto.includes("REPARTO")) rolAsociado = "R";
        if (texto.includes("USUARIO")) rolAsociado = "U";
        if (texto.includes("PRODUCCION")) rolAsociado = "P";
        if (texto.includes("VENTAS")) rolAsociado = "V";
        if (texto.includes("LIMPIEZA")) rolAsociado = "L";
        if (texto.includes("GERENTE")) rolAsociado = "G";
        if (texto.includes("REPORTE")) rolAsociado = "G"; // reportes solo gerente

        // Validar si el usuario debe ver este menú
        if (esGerente || roles.includes(rolAsociado)) {
            const clon = menuItem.cloneNode(true);
            // Si es usuario normal (no gerente ni encargado), quitar los -admin
            if (!esGerente && !esEncargado) {
                const adminBtns = clon.querySelectorAll(".button[class*='-admin']");
                adminBtns.forEach(btn => btn.remove());
            }

            sidebarContent.appendChild(clon);
        }
    });

    // Al final, agregamos el botón de salir
    sidebarContent.appendChild(salir);
});


// FUNCIÓN PARA EL SUBMENÚ DE LA BARRA LATERAL
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}

function toggleSubmenu(button) {
    const submenu = button.closest('.menu-item').querySelector('.submenu');
    if (submenu) {
        submenu.style.display = submenu.style.display === 'flex' ? 'none' : 'flex';
        button.textContent = submenu.style.display === 'flex' ? '▾' : '▸';
    }
}
// Función de salir
function Salir() {
    sessionStorage.clear();
    window.location.href = "/";
}
