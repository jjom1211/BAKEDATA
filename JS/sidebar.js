// sidebar.js - Controla la apertura/cierre de la sidebar
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}

// Opcional: Cerrar sidebar al hacer clic fuera de ella
document.addEventListener('click', (event) => {
    const sidebar = document.querySelector('.sidebar');
    const openBtn = document.querySelector('.open-sidebar');
    
    if (!sidebar.contains(event.target) && event.target !== openBtn) {
        sidebar.classList.remove('active');
    }
});