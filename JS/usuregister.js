// Archivo: venUsuRegister.js

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-registro-venta');

    // --- LÓGICA MEJORADA Y CENTRALIZADA PARA EL TOGGLE PASSWORD ---
    const toggleIcons = document.querySelectorAll('.toggle-password');

    toggleIcons.forEach(icon => {
        icon.addEventListener('click', () => {
            // Encuentra el input que está justo antes del icono
            const passwordInput = icon.previousElementSibling;
            if (passwordInput) {
                const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordInput.setAttribute('type', type);
            }
        });
    });

    // --- LÓGICA PARA ENVIAR EL FORMULARIO (FETCH) ---
    if (form) {
        const actionUrl = form.dataset.action;
        const redirectUrl = form.dataset.redirectUrl;

        form.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevenimos que la página se recargue

            const contraseña = document.getElementById("contraseña").value;
            const confirmacion = document.getElementById("confirmacion_de_contraseña").value;
            if (contraseña !== confirmacion) {
                alert("Las contraseñas no coinciden.");
                return;
            }

            const submitButton = form.querySelector('button[type="submit"]');
            const formData = new FormData(form);

            submitButton.disabled = true;
            submitButton.textContent = 'Registrando...';

            try {
                const response = await fetch(actionUrl, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                alert(data.message);

                if (response.ok) {
                    window.location.href = redirectUrl;
                } else {
                    submitButton.disabled = false;
                    submitButton.textContent = 'Registrar y Volver a Venta';
                }

            } catch (error) {
                console.error('Error de red o en el fetch:', error);
                alert('Ocurrió un error de comunicación. Inténtalo de nuevo.');
                submitButton.disabled = false;
                submitButton.textContent = 'Registrar y Volver a Venta';
            }
        });
    }
});