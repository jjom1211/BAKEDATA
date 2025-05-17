function registrarEntradas() {
    alert("Registrando Entradas...");
}
function actualizarMateriaPrima() {
    alert("Actualizando materia prima...");
}
function registrarSalidas() {
    alert("Registrando salidas...");
}
function actualizarProductos() {
    alert("Actualizando productos...");
}
function verProductos() {
    alert("Viendo productos...");
}
function verMateriaPrima() {
    window.location.href = "/materias_primas";  // Debe coincidir con la ruta en Flask
}
function solicitarProductos() {
    alert("solicitando productos...");
}
function solicitarMateriaPrima() {
    alert("solicitando materia prima...");
}
function enviarProductosaTienda() {
    alert("Enviando productos a tienda...");
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