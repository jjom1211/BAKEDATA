// Archivo: JS/venReporteInventario.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Selección de Elementos ---
    const tipoReporteSelect = document.getElementById('tipo_reporte');
    const sucursalSelect = document.getElementById('sucursal_selector');
    const generarBtn = document.getElementById('btn-generar-reporte');
    const resultadoContainer = document.getElementById('resultado-reporte');
    const mensajeEl = document.getElementById('reporte-mensaje');
    
    // --- CORRECCIÓN AQUÍ ---
    // Contenedor que tiene la URL de la API (buscamos .filtro-container)
    const selectorContainer = document.querySelector('.filtro-container');
    const actionUrl = selectorContainer ? selectorContainer.dataset.actionUrl : null;
    // --- FIN DE LA CORRECCIÓN ---
    
    // Referencias a los campos del reporte
    const valorTotalEl = document.getElementById('reporte-valor-total');
    const tablaBody = document.getElementById('tabla-inventario-body');

    // --- Función Auxiliar ---
    const formatearMoneda = (valor) => {
        let numValor = parseFloat(valor);
        if (isNaN(numValor)) numValor = 0;
        return numValor.toLocaleString('es-MX', { style: 'currency', currency: 'MXN' });
    };

    /**
     * Función principal para generar el reporte
     */
    const generarReporte = async () => {
        const sucursalId = sucursalSelect.value;
        const tipoReporte = tipoReporteSelect.value;

        if (!sucursalId || !tipoReporte) {
            alert('Por favor, selecciona un tipo de inventario y una sucursal.');
            return;
        }
        if (!actionUrl) {
            mensajeEl.textContent = 'Error: No se pudo encontrar la URL de la API.';
            return;
        }

        mensajeEl.textContent = 'Cargando reporte...';
        resultadoContainer.style.display = 'none';
        generarBtn.disabled = true;

        try {
            const response = await fetch(actionUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    sucursal_id: sucursalId, 
                    tipo_reporte: tipoReporte 
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Error del servidor');

            const items = data.items;
            
            if (!items || items.length === 0) {
                mensajeEl.textContent = 'No se encontró inventario para esta selección.';
                tablaBody.innerHTML = ''; // Limpia la tabla por si había algo antes
                valorTotalEl.textContent = formatearMoneda(0); // Pone el total en 0
                return;
            }

            // Llenar resumen
            valorTotalEl.textContent = formatearMoneda(data.valor_inventario_total);

            // Llenar tabla
            tablaBody.innerHTML = '';
            items.forEach(item => {
                const row = `
                    <tr>
                        <td>${item.id}</td>
                        <td>${item.nombre}</td>
                        <td>${item.stock}</td>
                        <td>${item.unidad}</td>
                        <td>${formatearMoneda(item.costo)}</td>
                        <td>${formatearMoneda(item.valor_total)}</td>
                    </tr>
                `;
                tablaBody.insertAdjacentHTML('beforeend', row);
            });

            mensajeEl.textContent = '';
            resultadoContainer.style.display = 'block';

        } catch (error) {
            console.error('Error al generar reporte de inventario:', error);
            mensajeEl.textContent = `Error: ${error.message}`;
        } finally {
            generarBtn.disabled = false;
        }
    };

    // --- Asignar Eventos ---
    generarBtn.addEventListener('click', generarReporte);

    // Generar el reporte inicial al cargar la página
    generarReporte();
});