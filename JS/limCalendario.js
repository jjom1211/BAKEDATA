//Funcion DOM de precarga de elementos y funciones
document.addEventListener('DOMContentLoaded', function() {
    //Constantes para la construccion del calendario
    const calendarGrid = document.getElementById('calendarGrid');
    const currentMonthElement = document.getElementById('currentMonth');
    const prevMonthButton = document.getElementById('prevMonth');
    const nextMonthButton = document.getElementById('nextMonth');
    //Variable para considerar punto temporal de referencia
    let currentDate = new Date();
    //Funcion para crear el calendario
    function renderCalendar(date) {
        calendarGrid.innerHTML = '';
        const year = date.getFullYear();
        const month = date.getMonth();
        currentMonthElement.textContent = `${date.toLocaleString('default', { month: 'long' })} ${year}`;
        const firstDayOfMonth = new Date(year, month, 1);
        const lastDayOfMonth = new Date(year, month + 1, 0);
        const daysInMonth = lastDayOfMonth.getDate();
        const startDay = firstDayOfMonth.getDay();
        //Creacion del espacio del calendario (espacio de solo 1 dia)
        for (let i = 0; i < startDay; i++) {
            calendarGrid.appendChild(document.createElement('div'));
        }
        //Creacion de espacios para los dias del mes así como su identificacion por el iterador
        for (let i = 1; i <= daysInMonth; i++) {
            const dayElement = document.createElement('div');
            dayElement.textContent = i;
            //Toma de referencia temporal local
            const fechaActual = new Date(year, month, i);
            const fechaStr = fechaActual.toISOString().split('T')[0];
            //Aplicacion de estilo si hay registro de actividades
            if (diasConLimpieza.includes(fechaStr)) {
                dayElement.classList.add('event'); // aplica el estilo púrpura
            }
            const hoy = new Date();
            //Condicionales para confirmacion temporal
            if (
                fechaActual.getFullYear() === hoy.getFullYear() &&
                fechaActual.getMonth() === hoy.getMonth() &&
                fechaActual.getDate() === hoy.getDate()
            ) {
            dayElement.classList.add('actualday'); // estilo para el dia actual
            }
            //Si se selecciona un dia este listener desplega las actividades de este
            dayElement.addEventListener('click', () => {
                mostrarTareasDelDia(fechaStr);
            });
            //Agrega los elementos de los dias al recurso
            calendarGrid.appendChild(dayElement);
        }
    }
    //Funcionalidad del boton para ir al mes anterior
    prevMonthButton.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar(currentDate);
    });
    //Funcionalidad del boton para ir al mes posterior
    nextMonthButton.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar(currentDate);
    });
    //Carga del calendario
    renderCalendar(currentDate);
});
//Accion del boton para regresar a la pagina anterior
document.getElementById('backButton').addEventListener('click', () => {
    window.history.back(); // Regresa a la página anterior
});

//Funcion para mostrar las tareas del dia seleccionado
function mostrarTareasDelDia(fechaStr) {
    //Llamada al endpoint para obtener las tareas
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

// FUNCIÓN PARA EL SUBMENÚ DE LA BARRA LATERAL
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}
function toggleSubmenu(button) {
    const submenu = button.closest('.menu-item').querySelector('.submenu');
    if (submenu) {
        submenu.style.display = submenu.style.display === 'flex' ? 'none' : 'flex';
        button.textContent = submenu.style.display === 'flex' ? '▾' : '▸';
    }
}