    //Funcion para regresar a la pagina anterior
    function goBack() {
    window.history.back();
    }
document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('.table-repartos tbody').addEventListener('click', function(event) {
        if (event.target && event.target.classList.contains('btn-guardar')) {
            const boton = event.target;
            const repartoId = boton.dataset.repartoId;
            
            // Encontrar la fila (tr) del botón para obtener los valores
            const fila = document.getElementById(`reparto-${repartoId}`);
            const nuevaFecha = fila.querySelector('.input-fecha').value;
            const nuevoEstado = fila.querySelector('.select-estado').value;

            guardarCambios(repartoId, nuevaFecha, nuevoEstado);
        }
    });
});

function guardarCambios(repartoId, nuevaFecha, nuevoEstado) {
    if (!nuevaFecha) {
        alert('Por favor, selecciona una fecha válida.');
        return;
    }

    fetch('/guardar_cambios_reparto', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            rep_id: repartoId,
            nueva_fecha: nuevaFecha,
            nuevo_estado: nuevoEstado
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        alert(data.message);
        // Opcional: podrías añadir una animación de éxito a la fila
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Hubo un error al guardar los cambios.');
    });
}