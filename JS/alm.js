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
// ✅ FUNCIÓN CORREGIDA: Redirige a la página que muestra los datos de la BD
function verProductos() {
    window.location.href = "/productos.html";
}
// Función para redirigir a la página de materias primas
function verMateriaPrima() {
    // Cambia la URL actual para mostrar la página "materias_primas.html"
    window.location.href = "/materias_primas.html";
}
function solicitarProductos() {
    alert("solicitando productos...");
}
function solicitarMateriaPrima() {
    window.location.href = "/solicitarMateriaPrima.html";
}
function enviarProductosaTienda() {
    alert("Enviando productos a tienda...");
}
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    // Nota: El selector '.content' fue eliminado, el toggle se aplica a 'sidebar'
    sidebar.classList.toggle('active');
}
function toggleSubmenu(button) {
    const submenu = button.closest('.menu-item').querySelector('.submenu');
    if (submenu) {
        submenu.style.display = submenu.style.display === 'flex' ? 'none' : 'flex';
        button.textContent = submenu.style.display === 'flex' ? '▾' : '▸';
    }
}