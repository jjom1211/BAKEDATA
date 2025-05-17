<<<<<<< HEAD
function verMateriaPrima() {
    window.location.href = "/materias_primas";  // Debe coincidir con la ruta en Flask
}
// Array para almacenar la producción del día
let produccionDelDia = JSON.parse(localStorage.getItem('produccionDelDia')) || [];

// Función para registrar la producción
function registrarProduccion() {
    const producto = document.getElementById('producto').value;
    const cantidad = document.getElementById('cantidad').value;

    if (producto && cantidad) {
        // Agregar la producción al array
        produccionDelDia.push({ producto, cantidad });
        // Guardar en localStorage
        localStorage.setItem('produccionDelDia', JSON.stringify(produccionDelDia));
        alert('Producción registrada con éxito');
        // Limpiar los campos del formulario
        document.getElementById('producto').value = '';
        document.getElementById('cantidad').value = '';
    } else {
        alert('Por favor, complete todos los campos');
    }
}

// Función para mostrar la producción de hoy
function mostrarProduccionHoy() {
    const listaProduccion = document.getElementById('listaProduccion');
    listaProduccion.innerHTML = ''; // Limpiar la lista antes de actualizar
    produccionDelDia.forEach(item => {
        const li = document.createElement('li');
        li.textContent = `${item.producto}: ${item.cantidad} unidades`;
        listaProduccion.appendChild(li);
    });
}

// Ejecutar la función para mostrar la producción al cargar la página
if (window.location.href.includes('produccion-hoy.html')) {
    mostrarProduccionHoy();
}
// FUNCIÓN PARA EL SUBMENÚ DE LA BARRA LATERAL
=======
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
