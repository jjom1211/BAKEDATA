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

// ... (El código del renderCalendar se mantiene IGUAL, solo cambia esta función) ...

function mostrarDetallesDelDia(fechaStr) {
    const detallesDiv = document.getElementById('pedidosDelDia');
    
    // Mostramos un mensaje de carga
    detallesDiv.style.display = 'block';
    detallesDiv.innerHTML = `<h3>Repartos del día: ${fechaStr}</h3><p>Cargando datos...</p>`;

    fetch(`/api/entregas_por_fecha/${fechaStr}`)
        .then(response => {
            if (!response.ok) throw new Error('Error en la red');
            return response.json();
        })
        .then(entregas => {
            detallesDiv.innerHTML = `<h3>Repartos del día: ${fechaStr}</h3>`;

            if (entregas.length === 0) {
                detallesDiv.innerHTML += '<p>No hay repartos programados para esta fecha en tu sucursal.</p>';
                return;
            }

            // Crear tabla única
            const table = document.createElement('table');
            table.classList.add('pedidos-table');
            
            // Encabezados
            const headerRow = document.createElement('tr');
            ['Hora', 'Pedido', 'Destino', 'Asunto', 'Estado Reparto', 'Monto'].forEach(text => {
                const th = document.createElement('th');
                th.textContent = text;
                headerRow.appendChild(th);
            });
            table.appendChild(headerRow);

            // Filas
            entregas.forEach(p => {
                const row = document.createElement('tr');
                
                // --- LÓGICA VISUAL BASADA EN ESTADO DE REPARTO ---
                let estadoColor = '#fff';
                let textoEstado = p.rep_estado_reparto;

                // Mapeo de colores y textos
                if(p.rep_estado_reparto === 'R') {
                    estadoColor = '#fef3c7'; // Amarillo claro (En Camino)
                    textoEstado = 'En Ruta';
                } else if(p.rep_estado_reparto === 'E') {
                    estadoColor = '#dcfce7'; // Verde claro (Entregado)
                    textoEstado = 'Entregado';
                } else if(p.rep_estado_reparto === 'X') {
                    estadoColor = '#fee2e2'; // Rojo claro (Cancelado)
                    textoEstado = 'Cancelado';
                } else if(p.rep_estado_reparto === 'P') {
                     estadoColor = '#e0f2fe'; // Azul claro (Pendiente)
                     textoEstado = 'Pendiente';
                }

                row.innerHTML = `
                    <td style="font-weight:bold;">${p.ped_hora_entrega}</td>
                    <td>${p.ped_id}</td>
                    <td>${p.sucursal_destino_nombre || 'Sin Sucursal'}</td>
                    <td>${p.ped_asunto}</td>
                    <td style="background-color: ${estadoColor}; color: #333; font-weight:bold; text-align:center;">
                        ${textoEstado}
                    </td>
                    <td>$${p.ped_monto_total.toFixed(2)}</td>
                `;
                table.appendChild(row);
            });

            detallesDiv.appendChild(table);
        })
        .catch(error => {
            console.error('Error:', error);
            detallesDiv.innerHTML = '<p style="color:white; background:red; padding:10px;">Error al cargar las entregas.</p>';
        });
}