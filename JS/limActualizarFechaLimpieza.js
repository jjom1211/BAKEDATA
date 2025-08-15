document.addEventListener('DOMContentLoaded', function () { //Funcion principal que se encarga de precargar la pagina y realizar funciones previo a mostrar el recurso
    //declaracion de constantes para referirse a partes del calendario
    const modal = document.getElementById('popupTareas'); 
    const overlay = document.getElementById('modalOverlay');
    const cerrarBtn = document.getElementById("cerrarPopupBtn");
    const confirmBtn = document.getElementById("confirmButton");
    //Agregar caracteristicas o elementos en base a las acciones que se van a realizar
    if (modal) modal.classList.add('popupTareas');
    if (overlay) overlay.classList.add('modalOverlay');
    if (cerrarBtn) cerrarBtn.addEventListener("click", cerrarModal);
    if (overlay) overlay.addEventListener("click", cerrarModal);
    //Declaracion de constantes para la construcción del calendario
    const calendarGrid = document.getElementById('calendarGrid');
    const currentMonthElement = document.getElementById('currentMonth');
    const prevMonthButton = document.getElementById('prevMonth');
    const nextMonthButton = document.getElementById('nextMonth');
    let currentDate = new Date();
    let fechaSeleccionada = null;
    let tareasDelDia = [];

    //Funcion para no mostrar la informacion de un dia en especifico hasta que se seleccione uno
    function cerrarModal() {
        modal.style.display = "none";
        overlay.style.display = "none";
        renderCalendar(currentDate);
    }
    //Funcion para construir el calendario
    function renderCalendar(date) {
        calendarGrid.innerHTML = '';
        const year = date.getFullYear();
        const month = date.getMonth();
        currentMonthElement.textContent = `${date.toLocaleString('default', { month: 'long' })} ${year}`;
        const firstDayOfMonth = new Date(year, month, 1);
        const lastDayOfMonth = new Date(year, month + 1, 0);
        const daysInMonth = lastDayOfMonth.getDate();
        const startDay = firstDayOfMonth.getDay();
        //Forma de generar un espacio para el calendario
        for (let i = 0; i < startDay; i++) {
            calendarGrid.appendChild(document.createElement('div'));
        }
        //Generacion de espacios en base a los dias que tiene un mes, así como su asignacion en base al iterante
        for (let i = 1; i <= daysInMonth; i++) {
            const dayElement = document.createElement('div');
            dayElement.textContent = i;
            //Constantes para contemplar el dia actual y el mismo pero con una funcionalidad aplicada
            const fechaActual = new Date(year, month, i);
            const fechaStr = fechaActual.toISOString().split('T')[0]; //Obtiene solo el dia
            //Si el dia tiene un registro de limpieza
            if (diasConLimpieza.includes(fechaStr)) {
                dayElement.classList.add('event'); // aplica el estilo púrpura
            }
            //Validacion de la fecha concurrente
            const hoy = new Date();
            if (
                fechaActual.getFullYear() === hoy.getFullYear() &&
                fechaActual.getMonth() === hoy.getMonth() &&
                fechaActual.getDate() === hoy.getDate()
            ) {
            dayElement.classList.add('actualday'); // estilo para el dia actual
            }
            dayElement.addEventListener('click', () => {
                mostrarTareasDelDia(fechaStr);//Si se selecciona un dia se despliega la funcion en base a la fecha seleccionada
            });
            calendarGrid.appendChild(dayElement);//Crea un espacio para el dia que se selecciono
        }
    }
    //Funcionalidad del boton que permite cambiar al mes anterior
    prevMonthButton.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar(currentDate);
    });
    //Funcionalidad del boton que permite cambiar al mes posterior
    nextMonthButton.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar(currentDate);
    });
    //Renderizacion del calendario antes de cargar toda la pagina
    renderCalendar(currentDate);
    //Funcion para mostrar las actividades del dia 
    function mostrarTareasDelDia(fechaStr) {
        fechaSeleccionada = fechaStr;
        const contenido = document.getElementById("contenidoPopup");
        contenido.innerHTML = ""; // Limpiar el contenido existente
        overlay.style.display = "block";
        modal.style.display = "block";
        //llamado al endpoint para obtener las tareas en base al dia seleccionado
        fetch(`/tareas_por_fecha/${fechaStr}`)
            .then(res => res.json())
            .then(data => {
                tareasDelDia = data;
                const titulo = document.createElement("h3");
                titulo.textContent = `Actividades para ${fechaStr}`;
                contenido.appendChild(titulo);
                //tabla de tareas
                const table = document.createElement("table");
                table.innerHTML = "<tr><th>Actividad</th><th>Estado</th></tr>";
                table.classList.add('popup-table'); // Clase para la tabla
                //Crea filas por cada tarea
                data.forEach((tarea, index) => {
                    const row = document.createElement("tr");
                    row.classList.add('table-row'); // Clase para las filas
                    const actividadCell = document.createElement("td");
                    actividadCell.textContent = tarea.actividad;
                    actividadCell.classList.add('table-cell'); // Clase para las celdas
                    const estadoCell = document.createElement("td");
                    estadoCell.classList.add('table-cell'); // Clase para las celdas
                    const select = document.createElement("select");
                    select.name = `estado_${index}`;
                    select.dataset.actividad = tarea.actividad;
                    select.classList.add('estado-select'); // Clase para el select
                    //Muestra las opciones de estados empezando con C de completado
                    ["C", "N", "P"].forEach(op => {
                        const option = document.createElement("option");
                        option.value = op;
                        option.textContent = op;
                        if (tarea.estado === op) option.selected = true; //Validacion del estado de la actividad
                        select.appendChild(option);//Creacion del selector de estado
                    });
                    estadoCell.appendChild(select);
                    row.appendChild(actividadCell);
                    row.appendChild(estadoCell);
                    table.appendChild(row);
                });
                contenido.appendChild(table);//Espacio para la tabla compleata

                //controles de búsqueda y agregar 
                const input = document.createElement("input");
                input.id = "taskSelect";
                input.type = "text";
                input.placeholder = "Buscar o seleccionar actividad...";
                input.addEventListener("input", filtrarActividades);
                input.classList.add('task-select-input'); // Clase para el input
                const list = document.createElement("ul");
                list.id = "autocompleteList";
                list.classList.add('autocomplete-list'); // Clase para la lista de autocompletado
                const botonAgregar = document.createElement("button"); //Boton para añadir tareas
                botonAgregar.textContent = "+";
                botonAgregar.type = "button";
                botonAgregar.onclick = () => addSelectedTask(fechaStr);
                botonAgregar.classList.add('autocomplete-container-row-button');
                botonAgregar.classList.add('add-task-button');
                const botonMostrarTodas = document.createElement("button"); //Boton para mostrar todas las actividades desde BD
                botonMostrarTodas.id = "toggleAllBtn";
                botonMostrarTodas.type = "button";
                botonMostrarTodas.onclick = toggleMostrarTodas;
                botonMostrarTodas.classList.add('autocomplete-container-row-button');
                botonMostrarTodas.classList.add('toggle-all-button');
                //Insertar imagen al boton de seleccion
                const img = document.createElement("img");
                img.src = "https://i.imgur.com/smPDt4w.png";
                img.style.width = "20px";
                botonMostrarTodas.appendChild(img);
                const divControles = document.createElement("div");
                divControles.classList.add('autocomplete-container-row'); // Clase para el contenedor
                divControles.appendChild(input);
                divControles.appendChild(botonAgregar);
                divControles.appendChild(botonMostrarTodas);
                divControles.appendChild(list);
                contenido.appendChild(divControles); // Añadir los controles aquí
                mostrarTodasActividades(); // Llama a esto para poblar la lista de autocompletado si está activa
            })
            //Captura en caso de no contactar a la BD
            .catch(error => {
                console.error("Error cargando tareas:", error);
                contenido.innerHTML = "<p>Error al cargar las tareas.</p>";
            });
    }
    //Listener para crear una lista en base a los cambios en las actividades y sus estados
    confirmBtn.addEventListener('click', () => {
        const selects = document.querySelectorAll('#contenidoPopup select');
        const cambios = Array.from(selects).map(select => ({
            actividad: select.dataset.actividad,
            estado: select.value
        }));
        //Se mandan los cambios al endpoint
        fetch(`/actualizar_estados/${fechaSeleccionada}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(cambios)
        })
        .then(res => res.ok ? alert("Estados actualizados.") : alert("Error actualizando."))
        .finally(cerrarModal);
    });
    //Limpieza del autocompletado de la barra de busqueda de actividades
    window.clearAutocomplete = function () {
        document.getElementById("autocompleteList").innerHTML = "";
    };
    //Funcion para mostrar todas las actividades dentro de una ventana emegente
    window.mostrarTodasActividades = function () {
        const list = document.getElementById("autocompleteList");
        list.innerHTML = "";
        actividadesDesdeServidor.forEach(act => {
            const li = document.createElement("li");
            li.textContent = act;
            li.classList.add('autocomplete-list-item'); // Clase para los elementos de la lista de autocompletado
            li.onclick = () => {
                document.getElementById("taskSelect").value = act;
                clearAutocomplete();
            };
            list.appendChild(li);
        });
    };
//Seleccion de una tarea de las disponibles en BD
window.addSelectedTask = function (fecha) {
    const selectedTask = document.getElementById("taskSelect").value.trim();
    // Validación: campo vacío o actividad no reconocida
    if (!selectedTask || !actividadesDesdeServidor.includes(selectedTask)) {
        alert("Selecciona una actividad válida.");
        return;
    }
    // Verificación: tarea ya agregada al arreglo
    if (tareasDelDia.some(t => t.actividad === selectedTask)) {
        alert("La actividad ya existe para este día.");
        return;
    }
    // Agrega la nueva tarea al arreglo local
    const nuevaTarea = {
        actividad: selectedTask,
        estado: "N"
    };
    tareasDelDia.push(nuevaTarea); //Agrega la tarea a la lista de tareas del dia
    // Regenerar la tabla con todas las tareas
    const table = document.querySelector("#contenidoPopup table");
    table.innerHTML = "<tr><th>Actividad</th><th>Estado</th></tr>";
    //Permite agregar los cambios a las tareas recien agregadas y ya agregadas
    tareasDelDia.forEach((tarea, index) => {
        const row = document.createElement("tr");
        row.classList.add("table-row");
        // Celda: actividad
        const actividadCell = document.createElement("td");
        actividadCell.textContent = tarea.actividad;
        actividadCell.classList.add("table-cell");
        // Celda: estado (select)
        const estadoCell = document.createElement("td");
        estadoCell.classList.add("table-cell");
        const select = document.createElement("select");
        select.name = `estado_${index}`;
        select.dataset.actividad = tarea.actividad;
        select.classList.add("estado-select");
        ["C", "N", "P"].forEach(op => {
            const option = document.createElement("option");
            option.value = op;
            option.textContent = op;
            if (tarea.estado === op) option.selected = true;
            select.appendChild(option);
        });
        estadoCell.appendChild(select);
        row.appendChild(actividadCell);
        row.appendChild(estadoCell);
        table.appendChild(row);
    });
    // Limpia el campo del autocompletado
    document.getElementById("taskSelect").value = "";
    // Actualiza el autocompletado sin cerrarlo
    if (mostrandoTodas) {
        mostrarTodasActividades();
    } else {
        filtrarActividades();
    }
}; //CIERRE DEL DOM


    //Seleccion de una actividad
    window.addSelectedTask = function (fecha) {
        const selectedTask = document.getElementById("taskSelect").value.trim();
        if (!selectedTask || !actividadesDesdeServidor.includes(selectedTask)) {
            alert("Selecciona una actividad válida.");
            return;
        }

        // Verifica que no esté ya en la tabla
        if (tareasDelDia.some(t => t.actividad === selectedTask)) {
            alert("La actividad ya existe para este día.");
                // Limpia el campo y actualiza la lista
            document.getElementById("taskSelect").value = "";
            if (mostrandoTodas) {
                mostrarTodasActividades();
            } else {
                filtrarActividades();
            }
            return;
            }

        // Agregar la actividad al arreglo local
        const nuevaTarea = {
            actividad: selectedTask,
            estado: "N"
        };
        tareasDelDia.push(nuevaTarea);

        // Regenerar la tabla completa
        const table = document.querySelector("#contenidoPopup table");
        table.innerHTML = "<tr><th>Actividad</th><th>Estado</th></tr>";

        tareasDelDia.forEach((tarea, index) => {
            const row = document.createElement("tr");
            row.classList.add('table-row');

            const actividadCell = document.createElement("td");
            actividadCell.textContent = tarea.actividad;
            actividadCell.classList.add('table-cell');

            const estadoCell = document.createElement("td");
            estadoCell.classList.add('table-cell');
            const select = document.createElement("select");
            select.name = `estado_${index}`;
            select.dataset.actividad = tarea.actividad;
            select.classList.add('estado-select');

            ["C", "N", "P"].forEach(op => {
                const option = document.createElement("option");
                option.value = op;
                option.textContent = op;
                if (tarea.estado === op) option.selected = true;
                select.appendChild(option);
            });

            estadoCell.appendChild(select);
            row.appendChild(actividadCell);
            row.appendChild(estadoCell);
            table.appendChild(row);
        });

        document.getElementById("taskSelect").value = "";
        if (mostrandoTodas) { // Si el modo "mostrar todas" está activo
            mostrarTodasActividades();
        } else { // Si hay un filtro aplicado
            filtrarActividades();
        }
    };

//Filtro de las actividades en base a la entrada y la lista de actividades
    window.filtrarActividades = function () {
        const input = document.getElementById("taskSelect").value.toLowerCase();
        const list = document.getElementById("autocompleteList");
        list.innerHTML = "";
        //Se realiza la comparacion en minusculas de las actividades
        const filtradas = actividadesDesdeServidor.filter(act =>
            act.toLowerCase().includes(input)
        );
        //Condicional para cuando no se desplegan todas las tareas y no hay nada en el input
        if (!mostrandoTodas || input.length > 0) { 
            filtradas.forEach(act => {
                const li = document.createElement("li");
                li.textContent = act;
                li.classList.add('autocomplete-list-item');
                li.onclick = () => {
                    document.getElementById("taskSelect").value = act;
                    clearAutocomplete(); // Decide si quieres que se cierre al seleccionar
                };
                list.appendChild(li);
            });
        }
    };
    //Funcion para mostrar todas las actividades
    window.toggleMostrarTodas = function () {
        mostrandoTodas = !mostrandoTodas;
        if (mostrandoTodas) {
            mostrarTodasActividades();
        } else {
            clearAutocomplete(); // Limpiar la lista si se desactiva "mostrar todas"
        }
    };
    //Funcion para filtrar las actividades
    window.filtrarActividades = function () {
        const input = document.getElementById("taskSelect").value.toLowerCase();
        const list = document.getElementById("autocompleteList");
        list.innerHTML = "";
        const filtradas = actividadesDesdeServidor.filter(act =>
            act.toLowerCase().includes(input)
        );
        filtradas.forEach(act => {
            const li = document.createElement("li");
            li.textContent = act;
            li.classList.add('autocomplete-list-item'); // Clase para los elementos de la lista de autocompletado
            li.onclick = () => {
                document.getElementById("taskSelect").value = act;
                clearAutocomplete();
            };
            list.appendChild(li);
        });
    };
//Condicional para cuando se muestran o no todas las actividades
    let mostrandoTodas = true;
    window.toggleMostrarTodas = function () {
        mostrandoTodas = !mostrandoTodas;
        if (mostrandoTodas) {
            mostrarTodasActividades();
        } else {
            clearAutocomplete();
        }
    };
//Funcionalidad del boton de regresar
document.getElementById('backButton').addEventListener('click', () => {
    window.history.back(); // Regresa a la página anterior
});
    // Sidebar
    window.toggleSidebar = function () {
        document.querySelector('.sidebar')?.classList.toggle('active');
        document.querySelector('.content')?.classList.toggle('active');
    };
    window.toggleSubmenu = function (btn) {
        const submenu = btn.closest('.menu-item').querySelector('.submenu');
        if (submenu) {
            submenu.style.display = submenu.style.display === 'flex' ? 'none' : 'flex';
            btn.textContent = submenu.style.display === 'flex' ? '▾' : '▸';
        }
    };
});