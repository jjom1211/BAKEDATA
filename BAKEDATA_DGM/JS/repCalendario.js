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
            dayElement.addEventListener('click', () => {
                dayElement.classList.toggle('event');
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
    alert('Envio de entrega de pedido completado.');
});

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}
