
let produccionDelDia = [];

// Referencias al DOM
const sucursalAdminSelect = document.getElementById('sucursal_admin');
const wrapper = document.getElementById('tabla-wrapper');
const sucursalPorDefecto = wrapper ? wrapper.dataset.sucursalPropia : null;

/**
 * Obtiene el ID de la sucursal activa
 */
function getSucursalActiva() {
    if (sucursalAdminSelect) {
        return sucursalAdminSelect.value;
    }
    return sucursalPorDefecto;
}

function obtenerYMostrarProduccion() {
    const sucursalId = getSucursalActiva();
    if (!sucursalId) return;

    const tablaBody = document.querySelector('#tablaProduccion tbody');
    tablaBody.innerHTML = '<tr><td colspan="3">Cargando...</td></tr>';

    // Enviamos el ID como parámetro GET
    fetch(`/api/obtener_produccion_hoy?sucursal_id=${sucursalId}`) 
        .then(response => response.json())
        .then(data => {
            produccionDelDia = data; 
            mostrarProduccionHoy(); 
        })
        .catch(error => {
            console.error('Error:', error);
            tablaBody.innerHTML = `<tr><td colspan="3">Error de conexión</td></tr>`;
        });
}

function mostrarProduccionHoy() {
    const tablaBody = document.querySelector('#tablaProduccion tbody');
    tablaBody.innerHTML = ''; 

    if (!produccionDelDia || produccionDelDia.length === 0) {
        tablaBody.innerHTML = '<tr><td colspan="3">No hay producción registrada hoy en esta sucursal.</td></tr>';
        return;
    }

    produccionDelDia.forEach((item) => {
        const fila = document.createElement('tr');
        
        // Nombre
        const celdaNombre = document.createElement('td');
        celdaNombre.textContent = item.pro_dia_nombre;
        fila.appendChild(celdaNombre);

        // Cantidad
        const celdaCantidad = document.createElement('td');
        celdaCantidad.textContent = item.pro_dia_cantidad; 
        celdaCantidad.style.fontWeight = "bold";
        fila.appendChild(celdaCantidad);

        // Checkbox
        const celdaRealizado = document.createElement('td');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        
        const estaCompletado = item.pro_dia_estado === 'C';
        checkbox.checked = estaCompletado;
        checkbox.disabled = estaCompletado; 

        item.uiChecked = estaCompletado;

        if (!estaCompletado) {
            checkbox.addEventListener('change', (e) => {
                item.uiChecked = e.target.checked;
            });
        }

        celdaRealizado.appendChild(checkbox);
        fila.appendChild(celdaRealizado);
        tablaBody.appendChild(fila);
    });
}

async function confirmarProduccion() {
    let todosLosIdsAConfirmar = [];
    
    produccionDelDia.forEach(grupo => {
        // Si está marcado en UI y estaba pendiente
        if (grupo.uiChecked && grupo.pro_dia_estado === 'P') {
            if (grupo.ids_reales) {
                todosLosIdsAConfirmar = todosLosIdsAConfirmar.concat(grupo.ids_reales);
            }
        }
    });

    if (todosLosIdsAConfirmar.length === 0) {
        alert("Selecciona al menos un producto pendiente para confirmar.");
        return;
    }

    const sucursalId = getSucursalActiva(); 

    try {
        const response = await fetch('/api/confirmar_produccion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                ids_produccion: todosLosIdsAConfirmar,
                sucursal_id: sucursalId // Enviamos la sucursal activa
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            alert(data.message || "Confirmado exitosamente.");
            obtenerYMostrarProduccion(); 
        } else {
            alert('❌ Error al confirmar: ' + (data.message || 'Error desconocido.'));
        }

    } catch (err) {
        alert("Ocurrió un error de conexión.");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Listener para cuando el gerente cambia de sucursal
    if (sucursalAdminSelect) {
        sucursalAdminSelect.addEventListener('change', obtenerYMostrarProduccion);
    }
    obtenerYMostrarProduccion();
});