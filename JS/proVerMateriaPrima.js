
document.addEventListener("DOMContentLoaded", function () {
    const sucursalSelect = document.getElementById("sucursal");
    const tbody = document.querySelector("#tablaInventario tbody"); // Apunta al tbody de la tabla

    sucursalSelect.addEventListener("change", function () {
        const sucursalId = this.value;
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center;">Cargando...</td></tr>'; // Mensaje de carga

        if (!sucursalId) {
            tbody.innerHTML = `
                <tr><td colspan="4" style="text-align: center;">Seleccione una sucursal para ver el inventario</td></tr>
            `;
            return;
        }

        // Petición al backend Flask
        fetch(`/api/inventario/${sucursalId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error("Error en la respuesta del servidor");
                }
                return response.json();
            })
            .then(data => {
                console.log("📦 Datos recibidos:", data);
                
                tbody.innerHTML = ""; // Limpia la tabla antes de llenarla

                if (!data || data.length === 0) {
                    tbody.innerHTML = `
                        <tr><td colspan="4" style="text-align: center;">No hay materias registradas para esta sucursal</td></tr>
                    `;
                    return;
                }

                // Llena la tabla
                data.forEach(item => {
                    const row = `
                        <tr>
                            <td>${item.id}</td>
                            <td>${item.nombre}</td>
                            <td>${item.unidad}</td>
                            <td>${item.stock}</td>
                        </tr>
                    `;
                    tbody.insertAdjacentHTML("beforeend", row);
                });
            })
            .catch(error => {
                console.error("❌ Error al cargar inventario:", error);
                tbody.innerHTML = `
                    <tr><td colspan="4" style="text-align: center;">Error al cargar inventario</td></tr>
                `;
            });
    });
});
