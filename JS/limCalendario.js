
document.addEventListener('DOMContentLoaded', function() {
    const calendarGrid = document.getElementById('calendarGrid');
    const currentMonthElement = document.getElementById('currentMonth');
    const prevMonthButton = document.getElementById('prevMonth');
    const nextMonthButton = document.getElementById('nextMonth');

    let currentDate = new Date();

    function renderCalendar(date) {
        calendarGrid.innerHTML = '';
        const year = date.getFullYear();
        const month = date.getMonth();
        currentMonthElement.textContent = `${date.toLocaleString('default', { month: 'long' })} ${year}`;
    
        const firstDayOfMonth = new Date(year, month, 1);
        const lastDayOfMonth = new Date(year, month + 1, 0);
        const daysInMonth = lastDayOfMonth.getDate();
        const startDay = firstDayOfMonth.getDay();
    
        for (let i = 0; i < startDay; i++) {
            calendarGrid.appendChild(document.createElement('div'));
        }
    
        for (let i = 1; i <= daysInMonth; i++) {
            const dayElement = document.createElement('div');
            dayElement.textContent = i;
    
            const fechaActual = new Date(year, month, i);
            const fechaStr = fechaActual.toISOString().split('T')[0];
    
            if (diasConLimpieza.includes(fechaStr)) {
                dayElement.classList.add('event'); // aplica el estilo púrpura
            }
            const hoy = new Date();
            if (
                fechaActual.getFullYear() === hoy.getFullYear() &&
                fechaActual.getMonth() === hoy.getMonth() &&
                fechaActual.getDate() === hoy.getDate()
            ) {
            dayElement.classList.add('actualday'); // estilo para el dia actual
            }
            dayElement.addEventListener('click', () => {
                mostrarTareasDelDia(fechaStr);
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

document.getElementById('backButton').addEventListener('click', () => {
    window.history.back(); // Regresa a la página anterior
});

document.getElementById('confirmButton').addEventListener('click', () => {
    alert('Envio de requerimiento de limpieza completado.');
});

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}

function mostrarTareasDelDia(fechaStr) {
    fetch(`/tareas_por_fecha/${fechaStr}`)
        .then(response => response.json())
        .then(data => {
            const tareasDiv = document.getElementById('tareasDelDia');
            tareasDiv.innerHTML = `<h3>Tareas para ${fechaStr}</h3>`;

            if (data.length === 0) {
                tareasDiv.innerHTML += "<p>No hay tareas registradas.</p>";
            } else {
                const lista = document.createElement('ul');
                data.forEach(tarea => {
                    const item = document.createElement('li');
                    item.textContent = `${tarea.actividad} - ${tarea.estado}`;
                    lista.appendChild(item);
                });
                tareasDiv.appendChild(lista);
            }
            // Mostrar el div siempre que se selecciona un día
            tareasDiv.style.display = 'block';
        })
        .catch(error => {
            console.error('Error al obtener tareas:', error);
            // En caso de error, ocultamos el div por precaución
            document.getElementById('tareasDelDia').style.display = 'none';
        });
}