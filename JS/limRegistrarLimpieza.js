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

    if (selectedTask && actividadesDesdeServidor.includes(selectedTask)) {
        addTask(selectedTask);
        selectedInput.value = "";
        clearAutocomplete();
    } else {
        alert("Por favor, selecciona una actividad válida.");
    }
}

function removeTask(index) {
    let tasks = JSON.parse(localStorage.getItem("tasks")) || [];
    tasks.splice(index, 1);
    localStorage.setItem("tasks", JSON.stringify(tasks));
    loadTasks();
}

function confirmTasks() {
    alert("Actividades confirmadas.");
}

function goBack() {
    window.history.back();
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('active');
}

function filtrarActividades() {
    const input = document.getElementById("taskSelect").value.toLowerCase();
    const autocompleteList = document.getElementById("autocompleteList");
    autocompleteList.innerHTML = "";

    if (input === "") return;

    const filtradas = actividadesDesdeServidor.filter(act =>
        act.toLowerCase().includes(input)
    );

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

function clearAutocomplete() {
    document.getElementById("autocompleteList").innerHTML = "";
}
