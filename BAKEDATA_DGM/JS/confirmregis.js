        // Cargar datos guardados en sessionStorage
        document.getElementById("resumen-nombre").innerText = sessionStorage.getItem("nombre");
        document.getElementById("resumen-correo").innerText = sessionStorage.getItem("correo");
        document.getElementById("resumen-telefono").innerText = sessionStorage.getItem("telefono");
        document.getElementById("resumen-direccion").innerText = sessionStorage.getItem("direccion");
        document.getElementById("resumen-correo2").innerText = sessionStorage.getItem("correo");

        function regresarRegistro() {
            window.location.href = "login.html";
        }