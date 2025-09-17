//Funcion para acceder al recurso Calendario
function verCalendario() {
    alert("Abriendo calendario...");
    window.location.href = "limCalendario.jinja2";
}
//Funcion para acceder al recurso Limpieza del dia
function limpiezaDelDia() {
    alert("Viendo limpieza del dia...");
    window.location.href = "limDia.jinja2";
}
//Funcion para acceder al recurso Registrar limpieza
function registrarLimpieza() {
    alert("Registrando limpieza...");
    window.location.href = "limRegistrarLimpieza.jinja2";
}
//Funcion para acceder al recurso Actualizar fecha de Limpieza
function actualizarFechaDeLimpieza() {
    alert("Actualizando limpieza del dia...");
    window.location.href = "limActualizarFechaLimpieza.jinja2";
}
