// Array para almacenar la producción del día
let produccionDelDia = JSON.parse(localStorage.getItem('produccionDelDia')) || [];

// Función para mostrar la producción de hoy en la tabla
function mostrarProduccionHoy() {
    const tablaBody = document.querySelector('#tablaProduccion tbody');
    tablaBody.innerHTML = ''; // Limpiar la tabla antes de actualizar

    produccionDelDia.forEach((item, index) => {
        const fila = document.createElement('tr');

        // Columna Nombre
        const celdaNombre = document.createElement('td');
        celdaNombre.textContent = item.producto;
        fila.appendChild(celdaNombre);

        // Columna Cantidad
        const celdaCantidad = document.createElement('td');
        celdaCantidad.textContent = item.cantidad;
        fila.appendChild(celdaCantidad);

        // Columna Realizado (checkbox)
        const celdaRealizado = document.createElement('td');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = item.realizado || false; // Marcar si ya está realizado
        checkbox.addEventListener('change', () => {
            produccionDelDia[index].realizado = checkbox.checked;
            localStorage.setItem('produccionDelDia', JSON.stringify(produccionDelDia));
        });
        celdaRealizado.appendChild(checkbox);
        fila.appendChild(celdaRealizado);

        // Agregar la fila a la tabla
        tablaBody.appendChild(fila);
    });
}

// Ejecutar la función para mostrar la producción al cargar la página
if (window.location.href.includes('produccion-hoy.html')) {
    mostrarProduccionHoy();
}