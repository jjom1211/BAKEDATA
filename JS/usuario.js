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
