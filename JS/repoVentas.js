// Archivo: JS/venReporteVentas.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Selección de Elementos ---
    const fechaInput = document.getElementById('fecha-reporte');
    const filtroBotones = document.querySelectorAll('.btn-filtro');
    const resultadoContainer = document.getElementById('resultado-reporte');
    const mensajeEl = document.getElementById('reporte-mensaje');
    
    // Referencias a los elementos del reporte
    const totalVendidoEl = document.getElementById('reporte-total-vendido');
    const numeroTicketsEl = document.getElementById('reporte-numero-tickets');
    const ticketPromedioEl = document.getElementById('reporte-ticket-promedio');
    const tablaProductosBody = document.getElementById('tabla-productos-body');
    
    // --- CORRECCIÓN 1: Seleccionar el CONTENEDOR y el CANVAS ---
    const graficaContainer = document.querySelector('.grafica-container'); // Contenedor
    const canvas = document.getElementById('graficaVentas'); // Gráfica
    const ctx = canvas ? canvas.getContext('2d') : null;
    let graficaVentasInstance = null; 

    // Leer la URL desde el HTML
    const selectorFechaContainer = document.querySelector('.selector-fecha');
    const actionUrl = selectorFechaContainer ? selectorFechaContainer.dataset.actionUrl : null;

    // Poner la fecha de hoy por defecto (formato YYYY-MM-DD)
    if (fechaInput) {
        const hoy = new Date();
        const anio = hoy.getFullYear();
        const mes = (hoy.getMonth() + 1).toString().padStart(2, '0'); 
        const dia = hoy.getDate().toString().padStart(2, '0');
        fechaInput.value = `${anio}-${mes}-${dia}`;
    }

    const formatearMoneda = (valor) => {
        let numValor = parseFloat(valor);
        if (isNaN(numValor)) numValor = 0;
        return numValor.toLocaleString('es-MX', { style: 'currency', currency: 'MXN' });
    };

    /**
     * Función principal para generar el reporte
     * @param {string} rango - 'dia', 'semana', 'mes', 'ano'
     */
    const generarReporte = async (rango) => {
        const fecha = fechaInput.value;
        if (!fecha) {
            alert('Por favor, selecciona una fecha base.');
            return;
        }

        if (!actionUrl) {
            mensajeEl.textContent = 'Error: No se pudo encontrar la URL de la API.';
            return;
        }

        mensajeEl.textContent = 'Cargando reporte...';
        resultadoContainer.style.display = 'none';
        filtroBotones.forEach(btn => btn.disabled = true);

        try {
            const response = await fetch(actionUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fecha: fecha, rango: rango })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Error del servidor');

            const totales = data.resumen_totales;
            const productos = data.productos_top;
            const grafica_data = data.grafica_data;

            if (!totales || totales.numero_tickets === 0) {
                mensajeEl.textContent = `No se encontraron ventas para ${rango} en esta fecha.`;
                if (graficaVentasInstance) graficaVentasInstance.destroy();
                graficaContainer.style.display = 'none'; // Oculta el contenedor si no hay datos
                return;
            }

            // Llenar resumen
            const totalVendido = totales.total_vendido || 0;
            const numTickets = totales.numero_tickets || 0;
            const ticketPromedio = (numTickets > 0) ? (totalVendido / numTickets) : 0;
            totalVendidoEl.textContent = formatearMoneda(totalVendido);
            numeroTicketsEl.textContent = numTickets;
            ticketPromedioEl.textContent = formatearMoneda(ticketPromedio);

            // Llenar tabla
            tablaProductosBody.innerHTML = '';
            if (productos && productos.length > 0) {
                productos.forEach(prod => {
                    const row = `<tr><td>${prod.detven_pro_nombre}</td><td>${prod.cantidad_total}</td></tr>`;
                    tablaProductosBody.insertAdjacentHTML('beforeend', row);
                });
            } else {
                tablaProductosBody.innerHTML = '<tr><td colspan="2">No hay detalle de productos.</td></tr>';
            }
            
            // --- CORRECCIÓN 2: Renderizar Gráfica (ocultar contenedor si no hay datos) ---
            if (graficaVentasInstance) {
                graficaVentasInstance.destroy();
            }
            
            if (grafica_data && grafica_data.labels.length > 0 && ctx) {
                graficaContainer.style.display = 'block'; // Muestra el contenedor
                graficaVentasInstance = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: grafica_data.labels,
                        datasets: [{
                            label: 'Total Vendido $MXN',
                            data: grafica_data.data,
                            backgroundColor: 'rgba(218, 96, 73, 0.7)',
                            borderColor: 'rgba(218, 96, 73, 1)',
                            borderWidth: 1,
                            maxBarThickness: 100 
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false, 
                        scales: { y: { beginAtZero: true } }
                    }
                });
            } else {
                // Si no hay datos de gráfica (ej. rango 'dia'), oculta el CONTENEDOR
                graficaContainer.style.display = 'none'; 
            }
            // --- FIN CORRECCIÓN ---

            mensajeEl.textContent = '';
            resultadoContainer.style.display = 'block';

        } catch (error) {
            console.error('Error al generar reporte:', error);
            mensajeEl.textContent = `Error: ${error.message}`;
        } finally {
            filtroBotones.forEach(btn => btn.disabled = false);
        }
    };

    // --- Asignar Eventos a los Botones ---
    filtroBotones.forEach(boton => {
        boton.addEventListener('click', () => {
            const rango = boton.dataset.rango;
            generarReporte(rango);
        });
    });

    // Generar el reporte del día actual al cargar la página
    generarReporte('dia');
});