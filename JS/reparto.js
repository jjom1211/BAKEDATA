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
    sidebar.classList.toggle('active');
}
function verMateriaPrima() {
    window.location.href = "/materias_primas";  // Debe coincidir con la ruta en Flask
}
function toggleSubmenu(button) {
    const submenu = button.closest('.menu-item').querySelector('.submenu');
    if (submenu) {
        submenu.style.display = submenu.style.display === 'flex' ? 'none' : 'flex';
        button.textContent = submenu.style.display === 'flex' ? '▾' : '▸';
    }
}
