function RegistrarCliente() {
    alert("Registrando cliente...");
}
function RegistrarVenta() {
    alert("Registrando venta...");
}
function RealizarPedido() {
    alert("Realizando pedido...");
}
function VerProductos() {
    alert("Viendo productos...");
}
function ActualizarCaja() {
    alert("Actualizando caja...");
}
function VerCaja() {
    alert("Viendo caja...");
}
function ReportedelDía() {
    alert("Reporte del día...");
}
function ReporteMensual() {
    alert("Reporte mensual...");
}
function verCatalogo() {
    alert("Abriendo catalogo...");
    window.location.href = "usuprincipal.html";
}


function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}