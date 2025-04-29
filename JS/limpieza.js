function verCalendario() {
    alert("Abriendo calendario...");
    window.location.href = "limCalendario.jinja2";
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

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}
