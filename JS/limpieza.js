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
<<<<<<< HEAD
=======

>>>>>>> 43f9cbdbba1d89295e2cf6bd631ed3186e8346d2
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}
<<<<<<< HEAD
function toggleSubmenu(button) {
    const submenu = button.closest('.menu-item').querySelector('.submenu');
    if (submenu) {
        submenu.style.display = submenu.style.display === 'flex' ? 'none' : 'flex';
        button.textContent = submenu.style.display === 'flex' ? '▾' : '▸';
    }
}
=======
>>>>>>> 43f9cbdbba1d89295e2cf6bd631ed3186e8346d2
