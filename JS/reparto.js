function verCalendario() {
    alert("Abriendo calendario...");
    window.location.href = "repCalendario.html";
}
function verPedidos() {
    alert("Abriendo pedidos pendientes...");
    window.location.href = "repPedidos.html";
}
function actualizarEntrega() {
    alert("Actualizando entrega...");
}
function confirmarEntrega() {
    alert("Confirmando entrega...");
}
function agregarEntrega() {
    alert("Agregando entrega...");
}
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
