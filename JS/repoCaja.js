// Archivo: JS/venReporteCaja.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Selección de Elementos ---
    const fechaInput = document.getElementById('fecha-reporte');
    const generarBtn = document.getElementById('btn-generar-reporte');
    const resultadoContainer = document.getElementById('resultado-reporte');
    const mensajeEl = document.getElementById('reporte-mensaje');
    
    const selectorContainer = document.querySelector('.selector-fecha');
    const actionUrl = selectorContainer ? selectorContainer.dataset.actionUrl : null;
    
    // Referencias a los campos del reporte
    const ventasEfectivoEl = document.getElementById('rep-ventas-efectivo');
    const ventasTarjetaEl = document.getElementById('rep-ventas-tarjeta');
    const ajustesAgregoEl = document.getElementById('rep-ajustes-agrego');
    const ajustesRetiroEl = document.getElementById('rep-ajustes-retiro');
    const cortesRetiroEl = document.getElementById('rep-cortes-retiro');
    const saldoEfectivoEl = document.getElementById('rep-saldo-efectivo');
    const saldoTarjetaEl = document.getElementById('rep-saldo-tarjeta');

    // --- Función Auxiliar ---
    const formatearMoneda = (valor) => {
        let numValor = parseFloat(valor);
        if (isNaN(numValor)) numValor = 0;
        return numValor.toLocaleString('es-MX', { style: 'currency', currency: 'MXN' });
    };

    // Poner la fecha de hoy por defecto
    if (fechaInput) {
        const hoy = new Date();
        const anio = hoy.getFullYear();
        const mes = (hoy.getMonth() + 1).toString().padStart(2, '0'); 
        const dia = hoy.getDate().toString().padStart(2, '0');
        fechaInput.value = `${anio}-${mes}-${dia}`;
    }

    /**
     * Función principal para generar el reporte
     */
    const generarReporte = async () => {
        const fecha = fechaInput.value;
        if (!fecha) {
            alert('Por favor, selecciona una fecha.');
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
                body: JSON.stringify({ fecha: fecha })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Error del servidor');

            // Llenar el resumen con los datos
            ventasEfectivoEl.textContent = formatearMoneda(data.ventas_efectivo);
            ventasTarjetaEl.textContent = formatearMoneda(data.ventas_tarjeta);
            ajustesAgregoEl.textContent = formatearMoneda(data.ajustes_agregado);
            ajustesRetiroEl.textContent = formatearMoneda(data.ajustes_retiro);
            cortesRetiroEl.textContent = formatearMoneda(data.cortes_turno_retiro);
            saldoEfectivoEl.textContent = formatearMoneda(data.saldo_final_efectivo);
            saldoTarjetaEl.textContent = formatearMoneda(data.saldo_final_tarjeta);

            mensajeEl.textContent = '';
            resultadoContainer.style.display = 'block';

        } catch (error) {
            console.error('Error al generar reporte de caja:', error);
            mensajeEl.textContent = `Error: ${error.message}`;
        } finally {
            generarBtn.disabled = false;
        }
    };

    // --- Asignar Eventos ---
    generarBtn.addEventListener('click', generarReporte);

    // Generar el reporte del día actual al cargar la página
    generarReporte();
});