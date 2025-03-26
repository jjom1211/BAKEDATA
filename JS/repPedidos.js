function verDetalles(id) {
    alert('Mostrar detalles del pedido ' + id);
}
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}