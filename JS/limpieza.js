function verCalendario() {
    alert("Abriendo calendario...");
    window.location.href = "limCalendario.html";
}
function limpiezaDelDia() {
    alert("Viendo limpieza del dia...");
    window.location.href = "limDia.html";
}
function registrarLimpieza() {
    alert("Registrando limpieza...");
}
function actualizarFechaDeLimpieza() {
    alert("Actualizando limpieza del dia...");
}
function verMateriaPrima() {
    window.location.href = "/materias_primas";  // Debe coincidir con la ruta en Flask
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
