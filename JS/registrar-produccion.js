// Array para almacenar la producción del día
let produccionDelDia = JSON.parse(localStorage.getItem('produccionDelDia')) || [];

// Función para registrar la producción
function registrarProduccion() {
    const producto = document.getElementById('producto').value;
    const cantidad = document.getElementById('cantidad').value;

    if (producto && cantidad) {
        produccionDelDia.push({ producto, cantidad });
        localStorage.setItem('produccionDelDia', JSON.stringify(produccionDelDia));
        alert('Producción registrada con éxito');
        document.getElementById('producto').value = '';
        document.getElementById('cantidad').value = '';
    } else {
        alert('Por favor, complete todos los campos');
    }
}

// Función para mostrar la producción de hoy
function mostrarProduccionHoy() {
    const listaProduccion = document.getElementById('listaProduccion');
    listaProduccion.innerHTML = '';
    produccionDelDia.forEach(item => {
        const li = document.createElement('li');
        li.textContent = `${item.producto}: ${item.cantidad} unidades`;
        listaProduccion.appendChild(li);
    });
}
