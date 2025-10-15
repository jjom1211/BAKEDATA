// sidebar.js - Controla la apertura/cierre de la sidebar

// Función para abrir o cerrar la sidebar
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar'); // Selecciona el elemento con clase "sidebar"
    const content = document.querySelector('.content'); // Selecciona el contenedor principal con clase "content"

    // Alterna (agrega o quita) la clase "active" en sidebar y content
    // Esto permite mostrar u ocultar la barra lateral y ajustar el contenido
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}

// Función para abrir/cerrar un submenú dentro de la sidebar
function toggleSubmenu(button) {
    // Busca el contenedor más cercano con clase "menu-item" y dentro de él selecciona el ".submenu"
    const submenu = button.closest('.menu-item').querySelector('.submenu');

    if (submenu) {
        // Alterna el estilo de display: si está en "flex" lo oculta, si no, lo muestra
        submenu.style.display = submenu.style.display === 'flex' ? 'none' : 'flex';

        // Cambia el símbolo del botón dependiendo del estado del submenú
        button.textContent = submenu.style.display === 'flex' ? '▾' : '▸';
    }
}

// Opcional: Cerrar la sidebar si se hace clic fuera de ella
document.addEventListener('click', (event) => {
    const sidebar = document.querySelector('.sidebar');       // Selecciona la sidebar
    const openBtn = document.querySelector('.open-sidebar');  // Selecciona el botón que abre la sidebar

    // Si el clic no ocurre dentro de la sidebar ni en el botón de abrir
    // entonces se cierra la sidebar removiendo la clase "active"
    if (!sidebar.contains(event.target) && event.target !== openBtn) {
        sidebar.classList.remove('active');
    }
});
