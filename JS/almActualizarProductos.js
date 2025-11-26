function guardarCambiosProducto(boton) {
    const fila = boton.closest('tr');
    const id = fila.dataset.id; // Este será el pro_id

    // Asumimos que la estructura de la fila es similar
    const descripcion = fila.querySelector('.input-desc').value;     // Mapea a pro_descr
    const unidad = fila.querySelector('.select-unidad').value;    // Mapea a pro_unimed
    const precio = fila.querySelector('.input-nuevo-precio').value; // Mapea a pro_precio
    const costo_unit = fila.querySelector('.input-costo-precio').value; // Mapea a pro_precio

    if (precio.trim() === '') {
        alert('Error: El nuevo precio no puede estar vacío.');
        return;
    }

    // El JS envía 'precio'
    const datos = {
        id: parseInt(id),
        descripcion: descripcion,
        unidad: unidad,
        precio: parseFloat(precio), // Cambiado de 'costo' a 'precio'
        costo_unit: parseFloat(costo_unit)
    };

    if (isNaN(datos.precio) || isNaN(datos.costo_unit)) { // Validación sobre 'precio'
        alert('Error: El valor ingresado no es un número válido.');
        return;
    }
    if (datos.precio < 0 || datos.costo_unit < 0) { // Validación sobre 'precio'
        alert("Error: El precio/costo no puede ser un número negativo.");
        return; // Detener la ejecución
    }

    boton.disabled = true;
    boton.textContent = 'Guardando...';

    // *** CAMBIO CLAVE ***
    // Cambiamos el endpoint de la API al de productos
    fetch('/api/producto/actualizar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                boton.style.backgroundColor = '#28a745';
                boton.textContent = '¡Guardado!';
                // Actualizamos el "Precio Actual" visualmente
                // Esta lógica es idéntica a la anterior
                fila.querySelector('.cell-precio-actual').textContent = `$ ${parseFloat(precio).toFixed(2)}`;
                fila.querySelector('.cell-costo-actual').textContent = `$ ${parseFloat(costo_unit).toFixed(2)}`;
                fila.querySelector('.input-nuevo-precio').value = '';
                fila.querySelector('.input-costo-precio').value = '';
            } else {
                boton.style.backgroundColor = '#dc3545';
                boton.textContent = 'Error';
                alert('Error al actualizar: ' + (data.error || 'Error desconocido'));
            }

            // El resto de la lógica para resetear el botón es idéntica
            setTimeout(() => {
                boton.disabled = false;
                boton.style.backgroundColor = '#007bff';
                boton.textContent = 'Guardar';
            }, 2000);
        })
        .catch(error => {
            console.error('Error en fetch:', error);
            alert('Error de conexión. Revisa la consola.');
            boton.disabled = false;
            boton.style.backgroundColor = '#dc3545';
            boton.textContent = 'Error';
        });
}

