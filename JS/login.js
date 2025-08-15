//Funcion para envio de la informacion dentro del formulario
document.getElementById("loginForm").addEventListener("submit", function(event) {
    event.preventDefault();
    //Se almacenan como variables la contraseña y nombre de usuario
    let username = document.getElementById("username").value;
    let password = document.getElementById("contraseña").value;
    //Con AJAX se manda un request pata identificar si hay concordancia de nombres y contraseñas de usuarios
    $.ajax({
        url: "/login",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ username: username, contraseña: password }),
        success: function(respuesta) {
            if (respuesta.error) {
                document.getElementById("error-message").innerText = respuesta.error;
            } 
            //Uso temporal para cambio de ambiente, aplicarse en base a roles que se deben de obtener de la BD en base al usuario
            else {
                alert(respuesta.message);
                const users = {
                    "gerente": "gerente.html",
                    "usuario": "usuario.html",
                    "venta": "ventas.html",
                    "almacen": "almacen.html",
                    "reparto": "reparto.html",
                    "limpieza": "limpieza.html",
                    "produccion": "produccion.html"
                };
                if (users[username]) {
                    window.location.href = users[username]; 
                }
            }
        },
        error: function() {
            console.log("Error en la petición AJAX")
            alert("Error, usuario no existente o contraseña equivocada");
        }
    });
});
//Funcion para observar la contraseña
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    input.type = input.type === "password" ? "text" : "password";
}  