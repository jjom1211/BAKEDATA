let produccionDelDia = [];

/**
 * Función principal: Obtiene los datos de la API de Flask y los muestra en la tabla.
 */
function obtenerYMostrarProduccion() {
    // 1. Obtener los datos del servidor (API de Flask)
    fetch('/api/obtener_produccion_hoy') 
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.message || 'Error desconocido del servidor.'); });
            }
            return response.json();
        })
        .then(data => {
            produccionDelDia = data; 
            mostrarProduccionHoy(); 
        })
        .catch(error => {
            console.error('Error al cargar la producción:', error);
            document.querySelector('#tablaProduccion tbody').innerHTML = 
                `<tr><td colspan="3">❌ Error al cargar la producción: ${error.message}</td></tr>`;
        });
}

/**
 * Función para confirmar los productos seleccionados como 'C' (Completados) en la BD.
 */
async function confirmarProduccion() {
    // 1. Obtener los nombres de los productos cuyo estado local es 'C' y que necesitan confirmación.
    const productos_a_confirmar = [];
    
    // Iteramos sobre el array local.
    produccionDelDia.forEach(item => {
        // 🔑 CORRECCIÓN CLAVE: Buscamos productos que marcamos como 'C' en la UI 
        // pero que el estado en la DB (el original) era 'P'.
        // No necesitamos la bandera uiChecked temporal, usamos el estado de la variable.
        if (item.pro_dia_estado === 'C' && item.estadoOriginalDB === 'P') {
            productos_a_confirmar.push(item.pro_dia_nombre);
        }
    });

    if (productos_a_confirmar.length === 0) {
        alert("Selecciona al menos un producto pendiente para confirmar.");
        return;
    }

    try {
        const response = await fetch('/api/confirmar_produccion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ productos: productos_a_confirmar })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // 2. Mensaje de éxito con cantidad confirmada
            alert(`✅ Se confirmaron ${data.rows_affected || 0} productos como Completados.`);
            
            // 3. Recargar la tabla para ver los cambios bloqueados
            obtenerYMostrarProduccion(); 
        } else {
            alert('❌ Error al confirmar: ' + (data.message || 'Error desconocido.'));
        }

    } catch (err) {
        console.error("Error de conexión al confirmar:", err);
        alert("Ocurrió un error al intentar confirmar la producción.");
    }
}


/**
 * Función para mostrar la producción de hoy en la tabla HTML.
 */
function mostrarProduccionHoy() {
    const tablaBody = document.querySelector('#tablaProduccion tbody');
    tablaBody.innerHTML = ''; 

    if (produccionDelDia.length === 0) {
        tablaBody.innerHTML = '<tr><td colspan="3">No hay producción registrada para hoy.</td></tr>';
        return;
    }

    produccionDelDia.forEach((item, index) => {
        const fila = document.createElement('tr');
        
        // 🔑 CLAVE: Almacenamos el estado original de la DB (P o C)
        item.estadoOriginalDB = item.pro_dia_estado; 
        
        // Columna Nombre y Cantidad (sin cambios)
        const celdaNombre = document.createElement('td');
        celdaNombre.textContent = item.pro_dia_nombre;
        fila.appendChild(celdaNombre);

        const celdaCantidad = document.createElement('td');
        celdaCantidad.textContent = item.pro_dia_cantidad;
        fila.appendChild(celdaCantidad);

        // Columna Checkbox
        const celdaRealizado = document.createElement('td');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        
        const estaCompletado = item.pro_dia_estado === 'C';
        
        checkbox.checked = estaCompletado;
        checkbox.disabled = estaCompletado; // BLOQUEAR COMPLETADOS

        // Evento: cuando se cambia el estado del checkbox (solo si está pendiente)
        if (!estaCompletado) {
            checkbox.addEventListener('change', (e) => {
                 // 🔑 CORRECCIÓN CRÍTICA: Actualiza DIRECTAMENTE el estado en el array local.
                 // Si está marcado, cambia a 'C'. Si se desmarca, cambia a 'P'.
                item.pro_dia_estado = e.target.checked ? 'C' : 'P';
            });
        }

        celdaRealizado.appendChild(checkbox);
        fila.appendChild(celdaRealizado);
        tablaBody.appendChild(fila);
    });
}

// Ejecutar la función automáticamente al cargar la página
obtenerYMostrarProduccion();