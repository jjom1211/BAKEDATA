document.addEventListener("DOMContentLoaded", function() {
    loadTasks();
    loadTaskOptions();
});

function loadTasks() {
    const taskList = document.getElementById("taskList");
    const tasks = JSON.parse(localStorage.getItem("tasks")) || [];
    taskList.innerHTML = "";
    tasks.forEach((task, index) => {
        const li = document.createElement("li");
        li.innerHTML = `<input type='checkbox'> ${task} <button onclick='removeTask(${index})'>X</button>`;
        taskList.appendChild(li);
    });
}

function addTask() {
    const newTaskInput = document.getElementById("newTask");
    const task = newTaskInput.value.trim();
    if (task) {
        let tasks = JSON.parse(localStorage.getItem("tasks")) || [];
        tasks.push(task);
        localStorage.setItem("tasks", JSON.stringify(tasks));
        newTaskInput.value = "";
        loadTasks();
        loadTaskOptions();
    }
}

function removeTask(index) {
    let tasks = JSON.parse(localStorage.getItem("tasks")) || [];
    tasks.splice(index, 1);
    localStorage.setItem("tasks", JSON.stringify(tasks));
    loadTasks();
    loadTaskOptions();
}

function loadTaskOptions() {
    const taskSelect = document.getElementById("taskSelect");
    const tasks = JSON.parse(localStorage.getItem("tasks")) || [];
    taskSelect.innerHTML = "";
    tasks.forEach(task => {
        const option = document.createElement("option");
        option.textContent = task;
        taskSelect.appendChild(option);
    });
}

function confirmTasks() {
    alert("Actividades confirmadas.");
}

function goBack() {
    alert("Regresando a la pantalla anterior.");
    window.history.back(); // Regresa a la página anterior
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}
