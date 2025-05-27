function verCalendario() {
    alert("Abriendo calendario...");
    window.location.href = "limCalendario.jinja2";
}
function limpiezaDelDia() {
    alert("Viendo limpieza del dia...");
    window.location.href = "limDia.jinja2";
}
function registrarLimpieza() {
    alert("Registrando limpieza...");
    window.location.href = "limRegistrarLimpieza.jinja2";
}
function actualizarFechaDeLimpieza() {
    alert("Actualizando limpieza del dia...");
    window.location.href = "limActualizarFechaLimpieza.jinja2";
}

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