    //Funcion para regresar a la pagina anterior
    function goBack() {
    window.history.back();
    }
function crearRepartos() {
    // 1. Obtener todos los checkboxes seleccionados
    const seleccionados = Array.from(
        document.querySelectorAll('input[name="pedidos"]:checked')
    ).map(cb => cb.value);

    // 2. Validar que se haya seleccionado al menos uno
    if (seleccionados.length === 0) {
        alert("Por favor, selecciona al menos un pedido para crear un reparto.");
        return;
    }

    // 3. Confirmar la acción con el usuario
    if (!confirm(`¿Estás seguro de que deseas crear ${seleccionados.length} nuevo(s) reparto(s)?`)) {
        return;
    }

    // 4. Enviar los datos al endpoint '/crear_reparto'
    fetch('/crear_reparto', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ pedidos: seleccionados })
    })
    .then(response => {
        if (!response.ok) {
            // Manejar errores del servidor
            return response.json().then(err => { throw new Error(err.message) });
        }
        return response.json();
    })
    .then(data => {
        // Mostrar mensaje de éxito y recargar la página
        alert(data.message);
        location.reload();
    })
    .catch(error => {
        console.error('Error al crear repartos:', error);
        alert('Error: ' + error.message);
    });
}
