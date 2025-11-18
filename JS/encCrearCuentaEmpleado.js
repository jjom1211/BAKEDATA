
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    if (input) {
        input.type = (input.type === "password") ? "text" : "password";
    }
}

function validarFormulario(event) {
    let contraseña = document.getElementById("contraseña").value;
    let confirmacion = document.getElementById("confirmacion_de_contraseña").value;

    if (contraseña !== confirmacion) {
        alert("Las contraseñas no coinciden. Por favor, inténtalo de nuevo.");
        event.preventDefault(); // Detiene el envío del formulario
        return false;
    }
    
    // Si las contraseñas coinciden, el formulario se envía
    return true;
}