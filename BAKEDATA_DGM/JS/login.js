document.getElementById("loginForm").addEventListener("submit", function(event) {
    event.preventDefault();

    let username = document.getElementById("username").value;
    let password = document.getElementById("contraseña").value;

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