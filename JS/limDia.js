
        function goBack() {
        window.history.back();
        }

function confirmarLimpieza() {
    const seleccionados = Array.from(
        document.querySelectorAll('input[name="actividad"]:checked')
    ).map(cb => cb.value);

    console.log("IDs seleccionados:", seleccionados);  // <-- útil para depurar

    if (seleccionados.length === 0) {
        alert("Selecciona al menos una actividad.");
        return;
    }

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