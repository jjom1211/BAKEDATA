document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.querySelector('.table-logistica tbody');

    if (tableBody) {
        tableBody.addEventListener('click', function(event) {
            if (event.target && event.target.classList.contains('btn-guardar')) {
                const boton = event.target;
                
                // Obtenemos los IDs del dataset
                const pedId = boton.dataset.pedId;
                const repId = boton.dataset.repId; 

                // Buscamos la fila específica
                const fila = document.getElementById(`fila-${pedId}`);
                
                // Obtenemos valores actuales de los inputs
                const nuevaFecha = fila.querySelector('.input-fecha').value;
                const nuevaHora = fila.querySelector('.input-hora').value;
                const nuevoEstado = fila.querySelector('.select-estado').value;

                guardarLogistica(boton, pedId, repId, nuevaFecha, nuevaHora, nuevoEstado);
            }
        });
    }
});

function guardarLogistica(boton, pedId, repId, nuevaFecha, nuevaHora, nuevoEstado) {
    // --- 1. VALIDACIONES LÓGICAS ---

    // A. Coherencia de datos: No permitir Fecha sin Hora o viceversa
    // (A menos que quieras permitir solo fecha, pero mejor ser estrictos)
    if ((nuevaFecha && !nuevaHora) || (!nuevaFecha && nuevaHora)) {
        alert('Datos incompletos: Si asignas fecha, debes asignar hora (y viceversa).');
        return;
    }

    // B. Validación por Estado
    // Caso: Quiero ponerlo EN REPARTO o ENTREGADO -> OBLIGATORIO tener fecha/hora.
    if ((nuevoEstado === 'R' || nuevoEstado === 'E') && (!nuevaFecha || !nuevaHora)) {
        alert('No puedes cambiar a estado "En Reparto" o "Entregado" sin definir Fecha y Hora.');
        return;
    }

    // Caso: Estado PENDIENTE ('P') -> Permitimos TODO.
    // - Puede tener fecha (Planificado pero no salido).
    // - Puede NO tener fecha (Pendiente puro / Backlog).
    // Por tanto, no necesitamos un else if aquí que bloquee.

    // --- 2. PREPARACIÓN UI ---
    const textoOriginal = boton.innerText;
    boton.innerText = "⏳";
    boton.disabled = true;

    // --- 3. ENVÍO AL SERVIDOR ---
    fetch('/guardar_gestion_logistica', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            ped_id: pedId,
            rep_id: repId || null,
            fecha: nuevaFecha, // Puede ir vacío
            hora: nuevaHora,   // Puede ir vacío
            estado: nuevoEstado
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) throw new Error(data.error);
        
        // Éxito
        alert(data.message);
        
        // Recargamos para ver los cambios reflejados (colores, inputs bloqueados si aplica, etc.)
        location.reload(); 
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ocurrió un error: ' + error.message);
        boton.innerText = textoOriginal;
        boton.disabled = false;
    });
}