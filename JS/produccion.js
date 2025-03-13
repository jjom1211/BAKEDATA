function solicitarMateriaPrima() {
    alert("Solicitando materia prima...");
}
function verPan() {
    alert("Mostrando lista de pan...");
}
function actualizarPan() {
    alert("Actualizando pan...");
}
function eliminarPan() {
    alert("Eliminando pan...");
}
function verMateriaPrima() {
    alert("Mostrando materia prima disponible...");
}
function agregarPan() {
    alert("Agregando pan al inventario...");
}
function reservarProductos() {
    alert("Reservando productos para pedido (Solo Admin)...");
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}
