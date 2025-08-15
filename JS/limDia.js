
        //Funcion para regresar a la pagina anterior
        function goBack() {
        window.history.back();
        }
//Funcion para confirmar los cambios en el estado de una actividad o actividades
function confirmarLimpieza() {
    //Seleccion de las actividades realizadas
    const seleccionados = Array.from(
        document.querySelectorAll('input[name="actividad"]:checked')
    ).map(cb => cb.value);
    //Muestra en consola la seleccion
    console.log("IDs seleccionados:", seleccionados);  // <-- útil para depurar
    //Condicional para mandar el request de cambios en los estados de las actividades
    if (seleccionados.length === 0) {
        alert("Selecciona al menos una actividad.");
        return;
    }
    //Llamado al endpoint para confirmar los cambios en las actividades
    fetch('/confirmarLimpieza', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ actividades: seleccionados })
    })
    .then(response => response.json())
    .then(res => {
        alert(res.message || "Actividades confirmadas");
        location.reload();
    })
    .catch(err => {
        console.error("Error:", err);
        alert("Ocurrió un error al confirmar.");
    });
}

//Funcionalidad del slidebar
        function toggleSidebar() {
            const sidebar = document.querySelector('.sidebar');
            const content = document.querySelector('.content');
            sidebar.classList.toggle('active');
            content.classList.toggle('active');
        }
        function toggleSubmenu(button) {
            const submenu = button.parentElement.nextElementSibling;
            submenu.style.display = submenu.style.display === 'flex' ? 'none' : 'flex';
        }