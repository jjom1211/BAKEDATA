function verCatalogo() {
    alert("Abriendo catalogo...");
    window.location.href = "usuprincipal.html";
}
function realizarPedido() {
    alert("Realizando pedido...");
}
function verSucursales() {
    alert("Abriendo listado de sucursales...");
    window.location.href = "ususucursales.html";
}
function confirmarEntrega() {
    alert("Confirmando entrega del pedido...");
}

function promocionesycupones(){
    alert("Abriendo promociones y cupones disponibles ...");
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}
