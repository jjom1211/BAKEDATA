document.getElementById("loginForm").addEventListener("submit", function (event) {
    event.preventDefault();

    let username = document.getElementById("username").value;
    let password = document.getElementById("contraseña").value;

    $.ajax({
        url: "/login",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ username: username, contraseña: password }),
        success: function (respuesta) {
            if (respuesta.error) {
                document.getElementById("error-message").innerText = respuesta.error;
            } else {
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
        error: function () {
            console.log("Error en la petición AJAX")
            alert("Error, usuario no existente o contraseña equivocada");
        }
    });
    const users = {
        "admin": "gerente.html",
        "user": "usuario.html",
        "sale": "ventas.html",
        "alm": "almacen.html",
        "rep": "reparto.html",
        "lim": "limpieza.html",
        "prod": "produccion.html"
    };

    if (users[username]) {
        window.location.href = users[username];
    } else {
        document.getElementById("error-message").innerText = "Usuario o contraseña incorrectos.";
    }
});

function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    input.type = input.type === "password" ? "text" : "password";
}
