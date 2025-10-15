// Array para almacenar la producción del día
// Se intenta cargar desde localStorage, si no existe se inicializa como un array vacío
let produccionDelDia = JSON.parse(localStorage.getItem('produccionDelDia')) || [];

/**
 * Función para mostrar la producción de hoy en la tabla HTML
 * - Crea filas dinámicamente para cada producto registrado
 * - Incluye nombre, cantidad y un checkbox para marcar si ya fue realizado
 */
function mostrarProduccionHoy() {
    // Selecciona el <tbody> de la tabla donde se insertarán los datos
    const tablaBody = document.querySelector('#tablaProduccion tbody');
    tablaBody.innerHTML = ''; // Limpia la tabla antes de volver a llenarla

    // Recorre el array de producción del día
    produccionDelDia.forEach((item, index) => {
        // Crea una nueva fila
        const fila = document.createElement('tr');

        // ----- Columna: Nombre del producto -----
        const celdaNombre = document.createElement('td');
        celdaNombre.textContent = item.producto; // Asigna el nombre del producto
        fila.appendChild(celdaNombre);

        // ----- Columna: Cantidad producida -----
        const celdaCantidad = document.createElement('td');
        celdaCantidad.textContent = item.cantidad; // Asigna la cantidad
        fila.appendChild(celdaCantidad);

        // ----- Columna: Checkbox de "Realizado" -----
        const celdaRealizado = document.createElement('td');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        // Marca el checkbox si el producto ya estaba marcado como realizado
        checkbox.checked = item.realizado || false;

        // Evento: cuando se cambia el estado del checkbox
        checkbox.addEventListener('change', () => {
            // Actualiza el estado de "realizado" en el array
            produccionDelDia[index].realizado = checkbox.checked;
            // Guarda los cambios en localStorage para persistencia
            localStorage.setItem('produccionDelDia', JSON.stringify(produccionDelDia));
        });

        // Agrega el checkbox a su celda y luego a la fila
        celdaRealizado.appendChild(checkbox);
        fila.appendChild(celdaRealizado);

        // Finalmente agrega la fila completa al cuerpo de la tabla
        tablaBody.appendChild(fila);
    });
}

// Ejecutar la función automáticamente al cargar la página de "produccion-hoy.html"
// Esto asegura que la tabla muestre los datos almacenados sin necesidad de interacción del usuario
if (window.location.href.includes('produccion-hoy.html')) {
    mostrarProduccionHoy();
}
