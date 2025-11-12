// Archivo: venMovimientosEfectivo.js

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-movimiento');

    if (form) {
        // Obtenemos la URL desde el atributo data-action que pusimos en el HTML
        const actionUrl = form.dataset.action;

        form.addEventListener('submit', async (event) => {
            event.preventDefault(); // Evitamos que la página se recargue

            const submitButton = form.querySelector('button[type="submit"]');
            const formData = new FormData(form);

            // Validaciones del lado del cliente
            if (formData.get('fuente_origen') === formData.get('fuente_destino')) {
                alert('La fuente de origen y destino no pueden ser la misma.');
                return;
            }
            if (parseFloat(formData.get('monto')) <= 0) {
                alert('El monto debe ser un número mayor a cero.');
                return;
            }
            
            submitButton.disabled = true;
            submitButton.textContent = 'Procesando...';

            try {
                // Usamos la variable actionUrl que contiene la URL correcta
                const response = await fetch(actionUrl, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                alert(data.message);

                if (response.ok) {
                    window.location.reload();
                } else {
                    submitButton.disabled = false;
                    submitButton.textContent = 'Confirmar Movimiento';
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Ocurrió un error de comunicación.');
                submitButton.disabled = false;
                submitButton.textContent = 'Confirmar Movimiento';
            }
        });
    }
});