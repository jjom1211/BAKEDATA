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