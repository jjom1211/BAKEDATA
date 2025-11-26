function guardarCambiosMateria(boton) {
    const fila = boton.closest('tr');
    const id = fila.dataset.id;

    const descripcion = fila.querySelector('.input-desc').value;
    const unidad = fila.querySelector('.select-unidad').value;
    const costo = fila.querySelector('.input-nuevo-precio').value;

    if (costo.trim() === '') {
        alert('Error: El nuevo precio no puede estar vacío.');
        return;
    }
    // El JS envía 'costo', lo cual es correcto para la API
    const datos = {
        id: parseInt(id),
        descripcion: descripcion,
        unidad: unidad,
        costo: parseFloat(costo)
    };

    if (isNaN(datos.costo)) {
        alert('Error: El valor ingresado para el precio no es un número válido.');
        return;
    }
    if (datos.costo < 0) {
        alert("Error: El precio no puede ser un número negativo.");
        // No deshabilitamos el botón, permitimos al usuario corregir.
        return; // Detener la ejecución
    }

    boton.disabled = true;
    boton.textContent = 'Guardando...';

    fetch('/api/materia_prima/actualizar', {
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
                fila.querySelector('.cell-precio-actual').textContent = `$ ${parseFloat(costo).toFixed(2)}`;
            } else {
                boton.style.backgroundColor = '#dc3545';
                boton.textContent = 'Error';
                alert('Error al actualizar: ' + (data.error || 'Error desconocido'));
            }

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
