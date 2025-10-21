// Archivo: JS/venActualizarCaja.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Selección de Elementos ---
    const cajaSelector = document.getElementById('caja_selector');
    const formContainer = document.getElementById('form-container'); // Still needed to reference elements inside
    const form = document.getElementById('form-actualizar-caja');
    const efectivoDisplay = document.querySelector('.efectivo-actual');
    const cajaIdHiddenInput = document.getElementById('caja_id_hidden');
    const confirmButton = document.getElementById('btn-confirmar'); // Reference the confirm button directly

    let efectivoActualEnCaja = 0; // Variable to store current cash amount

    // --- Lógica para el Selector de Caja ---
    if (cajaSelector) {
        // Disable confirm button initially
        if (confirmButton) { // Check if the button exists
            confirmButton.disabled = true;
        }

        cajaSelector.addEventListener('change', async () => {
            const cajaId = cajaSelector.value;
            cajaIdHiddenInput.value = cajaId; // Update hidden input value

            // If no cash register is selected
            if (!cajaId) {
                efectivoDisplay.textContent = '$--.--'; // Reset display
                efectivoActualEnCaja = 0;
                if (confirmButton) {
                    confirmButton.disabled = true; // Disable confirm button
                }
                return;
            }

            try {
                // Show loading state
                efectivoDisplay.textContent = 'Cargando...';

                // Fetch details for the selected cash register
                const response = await fetch(`/api/caja_detalle/${cajaId}`);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'No se pudo cargar la información de la caja.');
                }
                const data = await response.json();

                // Update display and stored cash amount
                efectivoActualEnCaja = data.caja_efectivo;
                efectivoDisplay.textContent = efectivoActualEnCaja.toLocaleString('es-MX', { style: 'currency', currency: 'MXN' });
                if (confirmButton) {
                    confirmButton.disabled = false; // Enable confirm button
                }

            } catch (error) {
                alert(error.message);
                efectivoDisplay.textContent = '$--.--'; // Reset display on error
                efectivoActualEnCaja = 0;
                if (confirmButton) {
                    confirmButton.disabled = true; // Disable confirm button on error
                }
            }
        });
    }

    // --- Lógica para el Envío del Formulario ---
    if (form) {
        const actionUrl = form.dataset.action; // Get API endpoint from data attribute

        form.addEventListener('submit', async (event) => {
            // Prevent default page reload
            event.preventDefault();

            // Use the direct reference to the confirm button
            const submitButton = confirmButton;
            const formData = new FormData(form);
            const monto = formData.get('monto');
            const tipoOperacion = formData.get('tipo_operacion');

            // --- Client-Side Validations ---
            // 1. Check if a cash register is selected
            if (!cajaIdHiddenInput.value) {
                alert('Por favor, selecciona una caja antes de continuar.');
                return;
            }

            // 2. Check if the amount is positive
            if (!monto || parseFloat(monto) <= 0) {
                alert('El monto debe ser un número mayor a cero.');
                return;
            }

            // 3. Check if a reason is selected
            if (!formData.get('motivo')) {
                alert('Debe seleccionar un motivo.');
                return;
            }

            // 4. Confirmation for withdrawals
            if (tipoOperacion === 'retirar') {
                if (!confirm(`¿Estás seguro de que deseas RETIRAR $${monto} de la caja?`)) {
                    return; // User cancelled
                }
            }
            // --- End Validations ---

            // Disable button during processing
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = 'Procesando...';
            }

            try {
                // Send data to the backend
                const response = await fetch(actionUrl, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                alert(data.message); // Show backend message (success or error)

                if (response.ok) { // If operation was successful (HTTP 200)
                    window.location.reload(); // Reload the page to show updated balance
                } else {
                    // If backend reported an error, re-enable the button
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.textContent = 'Confirmar Ajuste';
                    }
                }
            } catch (error) {
                // Handle network errors
                console.error('Error de comunicación:', error);
                alert('Ocurrió un error de comunicación. Inténtalo de nuevo.');
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = 'Confirmar Ajuste';
                }
            }
        });
    }
});