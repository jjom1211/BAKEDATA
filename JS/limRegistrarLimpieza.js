document.addEventListener("DOMContentLoaded", function () {
    loadTasks();
});

function loadTasks() {
    const taskList = document.getElementById("taskList");
    const tasks = JSON.parse(localStorage.getItem("tasks")) || [];
    taskList.innerHTML = "";

    tasks.forEach((task, index) => {
        const li = document.createElement("li");
        li.textContent = task;

        const removeButton = document.createElement("button");
        removeButton.textContent = "X";
        removeButton.onclick = () => removeTask(index);

        li.appendChild(removeButton);
        taskList.appendChild(li);
    });
}

function addTask(task) {
    let tasks = JSON.parse(localStorage.getItem("tasks")) || [];
    if (!tasks.includes(task)) {
        tasks.push(task);
        localStorage.setItem("tasks", JSON.stringify(tasks));
        loadTasks();
    }
}

function addSelectedTask() {
    const selectedInput = document.getElementById("taskSelect");
    const selectedTask = selectedInput.value.trim();

    const tasks = JSON.parse(localStorage.getItem("tasks")) || [];

    if (!selectedTask || !actividadesDesdeServidor.includes(selectedTask)) {
        alert("Por favor, selecciona una actividad válida.");
        return;
    }

    // Verificar si ya existe
    if (tasks.includes(selectedTask)) {
        alert("Esta actividad ya está en el listado.");
    }

    // Agregar si es válida y no existe
    addTask(selectedTask);
    selectedInput.value = "";
    clearAutocomplete();

    // Reabrir el menú con todas las actividades
    mostrandoTodas = true;
    mostrarTodasActividades();

    // Restaurar ícono
    const btn = document.getElementById("toggleAllBtn");
    const img = btn.querySelector("img");
    img.src = "https://i.imgur.com/smPDt4w.png";
}


function removeTask(index) {
    let tasks = JSON.parse(localStorage.getItem("tasks")) || [];
    tasks.splice(index, 1);
    localStorage.setItem("tasks", JSON.stringify(tasks));
    loadTasks();
}

function confirmTasks() {
    const tasks = JSON.parse(localStorage.getItem("tasks")) || [];

    if (tasks.length === 0) {
        alert("No hay actividades para registrar.");
        return;
    }

    fetch("/registrar_limpieza", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ actividades: tasks })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Error al registrar limpieza.");
        }
        return response.json();
    })
    .then(data => {
        if (data.omitidas && data.omitidas.length === tasks.length) {
            alert(`Ninguna actividad fue registrada.\nTodas ya estaban registradas hoy:\n\n- ${data.omitidas.join("\n")}`);
        } else if (data.omitidas && data.omitidas.length > 0) {
            alert(`${data.mensaje}\n\n${data.advertencia}\n\nOmitidas:\n- ${data.omitidas.join("\n")}`);
        } else {
            alert(data.mensaje || "Limpieza registrada exitosamente.");
        }

        localStorage.removeItem("tasks");
        loadTasks();  // actualiza la lista mostrada
    })
    .catch(error => {
        console.error("Error:", error);
        alert("Error al registrar la limpieza.");
    });
}

function filtrarActividades() {
    const input = document.getElementById("taskSelect").value.toLowerCase();
    const autocompleteList = document.getElementById("autocompleteList");
    autocompleteList.innerHTML = "";

    const filtradas = input === ""
        ? actividadesDesdeServidor
        : actividadesDesdeServidor.filter(act => act.toLowerCase().includes(input));

    filtradas.forEach(act => {
        const li = document.createElement("li");
        li.textContent = act;
        li.onclick = () => {
            document.getElementById("taskSelect").value = act;
            clearAutocomplete();
        };
        autocompleteList.appendChild(li);
    });
}

let mostrandoTodas = true; // Abierto por defecto

document.addEventListener("DOMContentLoaded", function () {
    loadTasks();
    mostrarTodasActividades(); // Mostrar al iniciar
});

function toggleMostrarTodas() {
    mostrandoTodas = !mostrandoTodas;

    const btn = document.getElementById("toggleAllBtn");
    const img = btn.querySelector("img");

    if (mostrandoTodas) {
        mostrarTodasActividades();
        img.src = "https://i.imgur.com/smPDt4w.png"; // ícono de "mostrar"
    } else {
        clearAutocomplete();
        img.src = "https://i.imgur.com/smPDt4w.png"; // ícono de "ocultar" (puedes usar otro)
    }
}


function mostrarTodasActividades() {
    const autocompleteList = document.getElementById("autocompleteList");
    autocompleteList.innerHTML = "";

    actividadesDesdeServidor.forEach(act => {
        const li = document.createElement("li");
        li.textContent = act;
        li.onclick = () => {
            document.getElementById("taskSelect").value = act;
            clearAutocomplete();
        };
        autocompleteList.appendChild(li);
    });
}


function clearAutocomplete() {
    document.getElementById("autocompleteList").innerHTML = "";
}

function goBack() {
    window.history.back();
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