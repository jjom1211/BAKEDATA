// --- Guardar roles al iniciar sesión ---
document.getElementById("loginForm").addEventListener("submit", function(event) {
    event.preventDefault();

    let correo = document.getElementById("correo").value;
    let password = document.getElementById("contraseña").value;
    
    // Limpiamos el mensaje de error anterior
    document.getElementById("error-message").innerText = "";

    $.ajax({
        url: "/login",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ correo: correo, contraseña: password }),
        success: function(respuesta) {
            // Si llegamos aquí, el login fue exitoso (status 200 OK)
            document.getElementById("success-message").innerText = respuesta.message; // Muestra el mensaje de bienvenida
            // Guardar en sessionStorage
            sessionStorage.setItem('rol_principal', respuesta.rol_principal);
            sessionStorage.setItem('roles', JSON.stringify(respuesta.roles));

            // Redirigir según rol principal
            const rolesMap = {
                "G": "/gerente",
                "U": "/usuario",
                "V": "/ventas",
                "A": "/almacen",
                "R": "/reparto",
                "L": "/limpieza",
                "P": "/produccion",
                "E": "/encargado",
                "EV": "/ventas",
                "EA": "/almacen",
                "ER": "/reparto",
                "EL": "/limpieza",
                "EP": "/produccion",
            };
            const pagina = rolesMap[respuesta.rol_principal];
            
            if (pagina) {
                setTimeout(() => {
                    window.location.href = pagina;
                }, 1500); // 1.5 segundos de espera para mostrar el mensaje
            } else {
                // Si el rol es válido pero no está en el mapa, lo mostramos como error
                document.getElementById("error-message").innerText = "Rol no configurado. Contacte al administrador.";
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            // Esta función se activa cuando el servidor responde con un error (ej. 401)
            console.error("Error en la petición AJAX:", textStatus, errorThrown);
            let mensajeError = "Error de conexión. Inténtalo más tarde."; // Mensaje por defecto

            // jqXHR.responseJSON contiene el JSON que enviaste desde Flask
            if (jqXHR.responseJSON && jqXHR.responseJSON.error) {
                // Muestra el mensaje específico del backend (ej. "Usuario o contraseña no válidos")
                mensajeError = jqXHR.responseJSON.error;
            }
            
            // Muestra el error en el div, no en un alert
            document.getElementById("error-message").innerText = mensajeError;
        }
    });
});

//Funcion para observar la contraseña 
function togglePassword(inputId) { 
    const input = document.getElementById(inputId); 
    input.type = input.type === "password" ? "text" : "password"; 
}