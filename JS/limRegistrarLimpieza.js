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

    // Evita duplicados
    if (!tasks.includes(task)) {
        tasks.push(task);
        localStorage.setItem("tasks", JSON.stringify(tasks));
        loadTasks();
    }
}

function addSelectedTask() {
    const selectedInput = document.getElementById("taskSelect");
    const selectedTask = selectedInput.value.trim();

    if (selectedTask) {
        addTask(selectedTask);
        selectedInput.value = "";
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
    alert("Regresando a la pantalla anterior.");
    window.history.back();
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}
