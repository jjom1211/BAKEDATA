//Funcion DOM de precarga de elementos y funciones
document.addEventListener('DOMContentLoaded', function() {
    //Constantes para la construccion del calendario
    const calendarGrid = document.getElementById('calendarGrid');
    const currentMonthElement = document.getElementById('currentMonth');
    const prevMonthButton = document.getElementById('prevMonth');
    const nextMonthButton = document.getElementById('nextMonth');
    let currentDate = new Date();

function renderCalendar(date) {
    calendarGrid.innerHTML = '';
    const year = date.getFullYear();
    const month = date.getMonth();
    // ... (el código para configurar el mes y los días en blanco sigue igual) ...
    currentMonthElement.textContent = `${date.toLocaleString('es-MX', { month: 'long' })} ${year}`;
    const lastDayOfMonth = new Date(year, month + 1, 0);
    const daysInMonth = lastDayOfMonth.getDate();
    const startDay = new Date(year, month, 1).getDay();
    for (let i = 0; i < startDay; i++) {
        calendarGrid.appendChild(document.createElement('div'));
    }

    const hoy = new Date();
    const hoySinHora = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());

    for (let i = 1; i <= daysInMonth; i++) {
        const dayElement = document.createElement('div');
        dayElement.textContent = i;
        const fechaActual = new Date(year, month, i);
        const fechaStr = fechaActual.toISOString().split('T')[0];

        // --- LÓGICA DE ESTILOS SIMPLIFICADA ---
        const status = diasConEventos[fechaStr];
        if (status) {
            dayElement.classList.add(status); // Añade 'rojo', 'amarillo' o 'verde'
        }

        // La prioridad máxima sigue siendo el día actual
        if (fechaActual.getTime() === hoySinHora.getTime()) {
            dayElement.classList.remove('rojo', 'amarillo', 'verde');
            dayElement.classList.add('actualday');
        }
        
        dayElement.addEventListener('click', () => {
            mostrarDetallesDelDia(fechaStr);
        });
        calendarGrid.appendChild(dayElement);
    }
}
    prevMonthButton.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar(currentDate);
    });

    nextMonthButton.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar(currentDate);
    });

    renderCalendar(currentDate);
});

//Accion del boton para regresar a la pagina anterior
document.getElementById('backButton').addEventListener('click', () => {
    window.history.back();
});


// --- FUNCIÓN TOTALMENTE NUEVA QUE REEMPLAZA A LA ANTERIOR ---
function mostrarDetallesDelDia(fechaStr) {
    const detallesDiv = document.getElementById('pedidosDelDia');
    detallesDiv.innerHTML = `<h3>Detalles para ${fechaStr}</h3>`; // Título principal
    detallesDiv.style.display = 'block';

    // Peticiones a ambos endpoints al mismo tiempo
    const fetchPedidos = fetch(`/pedidos_por_fecha/${fechaStr}`).then(res => res.json());
    const fetchRepartos = fetch(`/repartos_por_fecha/${fechaStr}`).then(res => res.json());

    // Cuando ambas promesas se resuelvan...
    Promise.all([fetchPedidos, fetchRepartos])
        .then(([pedidos, repartos]) => {
            
            // --- Sección para Pedidos Creados ---
            detallesDiv.innerHTML += '<h4>Pedidos Creados</h4>';
            if (pedidos.length === 0) {
                detallesDiv.innerHTML += '<p>No hay pedidos creados en esta fecha.</p>';
            } else {
                const table = document.createElement('table');
                table.classList.add('pedidos-table');
                const headerRow = document.createElement('tr');
                ['# Ped', 'Asunto', 'Estado', 'Monto', 'Sucursal Destino'].forEach(text => {
                    const th = document.createElement('th');
                    th.textContent = text;
                    headerRow.appendChild(th);
                });
                table.appendChild(headerRow);
                
                pedidos.forEach(p => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${p.ped_id}</td>
                        <td>${p.ped_asunto}</td>
                        <td>${p.ped_estado_pedido}</td>
                        <td>$${parseFloat(p.ped_monto_total).toFixed(2)}</td>
                        <td>${p.sucursal_destino_nombre || 'N/A'}</td>
                    `;
                    table.appendChild(row);
                });
                detallesDiv.appendChild(table);
            }

            // --- Sección para Repartos Programados ---
            detallesDiv.innerHTML += '<hr><h4>Repartos Programados</h4>';
            if (repartos.length === 0) {
                detallesDiv.innerHTML += '<p>No hay repartos programados para esta fecha.</p>';
            } else {
                const table = document.createElement('table');
                table.classList.add('pedidos-table');
                const headerRow = document.createElement('tr');
                ['# Rep', 'Asunto', 'Estado', 'Monto', 'Sucursal Destino'].forEach(text => {
                    const th = document.createElement('th');
                    th.textContent = text;
                    headerRow.appendChild(th);
                });
                table.appendChild(headerRow);

                repartos.forEach(r => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${r.rep_id}</td>
                        <td>${r.ped_asunto}</td>
                        <td>${r.rep_estado_reparto}</td>
                        <td>$${parseFloat(r.ped_monto_total).toFixed(2)}</td>
                        <td>${r.sucursal_destino_nombre || 'N/A'}</td>
                    `;
                    table.appendChild(row);
                });
                detallesDiv.appendChild(table);
            }
        })
        .catch(error => {
            console.error('Error al obtener detalles del día:', error);
            detallesDiv.innerHTML += '<p>Ocurrió un error al cargar los detalles.</p>';
        });
}