function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    input.type = (input.type === "password") ? "text" : "password";
}

function enviarFormulario(event) {
    event.preventDefault();

    let contraseña = document.getElementById("contraseña").value;
    let confirmacion = document.getElementById("confirmacion_de_contraseña").value;

    if (contraseña !== confirmacion) {
        alert("Las contraseñas no coinciden. Inténtalo de nuevo.");
        return;
    }

    const nombre = document.getElementById("nombre").value;
    const correo = document.getElementById("correo").value;
    const telefono = document.getElementById("telefono").value;
    const direccion = document.getElementById("direccion").value;

    sessionStorage.setItem("nombre", nombre);
    sessionStorage.setItem("correo", correo);
    sessionStorage.setItem("telefono", telefono);
    sessionStorage.setItem("direccion", direccion);
    alert("confirmando registro ...");
    window.location.href = "../HTML/confirmacionregistro.html";
}