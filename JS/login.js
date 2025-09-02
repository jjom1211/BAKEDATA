document.getElementById("loginForm").addEventListener("submit", function(event) {
    event.preventDefault();

    let correo = document.getElementById("correo").value;
    let password = document.getElementById("contraseña").value;

    $.ajax({
        url: "/login",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ correo: correo, contraseña: password }),
        success: function(respuesta) {
            if (respuesta.error) {
                document.getElementById("error-message").innerText = respuesta.error;
            } else {
                alert(respuesta.message);

                // Mapear rol a la página HTML
                const rolesMap = {
                    "G": "gerente.html",
                    "U": "usuario.html",
                    "V": "ventas.html",
                    "A": "almacen.html",
                    "R": "reparto.html",
                    "L": "/limpieza.jinja2",
                    "P": "produccion.html"
                };

                const pagina = rolesMap[respuesta.rol_principal];
                if (pagina) {
                    window.location.href = pagina;
                } else {
                    alert("Rol no reconocido, contacte al administrador");
                }
            }
        },
        error: function() {
            console.log("Error en la petición AJAX");
            alert("Error, usuario no existente o contraseña equivocada");
        }
    });
});
//Funcion para observar la contraseña 
function togglePassword(inputId) { 
    const input = document.getElementById(inputId); 
    input.type = input.type === "password" ? "text" : "password"; 
}



