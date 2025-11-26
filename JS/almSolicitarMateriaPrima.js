// Archivo: JS/solicitar_materia_prima.js

// Variable global para este módulo, guarda las materias primas seleccionadas
let materiasSeleccionadas = {};

/**
 * Busca materias primas en la API y muestra sugerencias.
 * Esta función es llamada por el 'oninput' del buscador.
 */
async function buscarMaterias() {
    const sugerenciasUl = document.getElementById('sugerencias');
    const contenedor = document.getElementById('contenedor-sugerencias-MatPri');
    const query = document.getElementById('buscador').value;

    if (!contenedor || !sugerenciasUl) {
        console.error("Error: Faltan contenedores de sugerencias.");
        return;
    }

    sugerenciasUl.innerHTML = "";
    if (query.trim() === "") {
        contenedor.style.display = "none";
        return;
    }
    
    contenedor.style.display = "block";

    try {
        const response = await fetch(`/buscar_materias?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.length === 0) {
            sugerenciasUl.innerHTML = "<div style='padding: 10px;'>No se encontraron materias primas.</div>";
        } else {
            data.forEach(materia => {
                const div = document.createElement("div");
                div.textContent = `${materia.nombre} (${materia.unidad}) - ${materia.descripcion || ''}`;
                // Codificamos el objeto completo para pasarlo al hacer clic
                const encoded = encodeURIComponent(JSON.stringify(materia));
                div.onclick = () => agregarMateriaASeleccionados(encoded);
                sugerenciasUl.appendChild(div);
            });
        }
    } catch (err) {
        console.error("Error al buscar materias primas:", err);
        contenedor.style.display = "none";
    }
}

/**
 * Añade una materia prima a la lista de "Materias Seleccionadas"
 * @param {string} encodedData - El objeto 'materia' codificado como string URI.
 */
function agregarMateriaASeleccionados(encodedData) {
    const materia = JSON.parse(decodeURIComponent(encodedData));
    const id = materia.id.toString();
    const lista = document.getElementById("listaSeleccionadas");

    if (materiasSeleccionadas[id]) {
        alert(`La materia "${materia.nombre}" ya está en la lista.`);
        return;
    }

    // Añade al objeto global
    materiasSeleccionadas[id] = {
        nombre: materia.nombre,
        unidad: materia.unidad,
        cantidad: "1"
    };

    // Crea el elemento visual en la lista
    const li = document.createElement("li");
    li.id = `item-matp-${id}`;
    li.innerHTML = `
        <div class="confirm-header">
            <input type="checkbox" class="check-matp" id="check-matp-${id}" checked
                    data-id="${id}" data-nombre="${materia.nombre}" data-unidad="${materia.unidad}">
            <strong>${materia.nombre} (${materia.unidad})</strong>
        </div>
        <div class="confirm-quantity">
            <label>Cantidad:</label>
            <input type="number" id="cantidad-matp-${id}" min="1" value="1">
        </div>
    `;
    lista.appendChild(li);
    
    // Añade los listeners para el checkbox y el input de cantidad
    agregarListenersAMateria(id);
    
    // Muestra el contenedor de seleccionadas
    const container = document.getElementById("seleccionadasContainerMateriaPrima");
    container.style.display = "block";
}

/**
 * Añade los event listeners (change, input) al nuevo item de la lista.
 * @param {string} id - El ID de la materia prima.
 */
function agregarListenersAMateria(id) {
    const check = document.getElementById(`check-matp-${id}`);
    const cantidadInput = document.getElementById(`cantidad-matp-${id}`);

    // Listener para el Checkbox (Habilitar/Deshabilitar)
    check.addEventListener('change', () => {
        if (check.checked) {
            // Si se marca, se añade/actualiza en el objeto
            materiasSeleccionadas[id] = {
                nombre: check.dataset.nombre,
                unidad: check.dataset.unidad,
                cantidad: cantidadInput.value
            };
            cantidadInput.disabled = false;
        } else {
            // Si se desmarca, se elimina del objeto
            delete materiasSeleccionadas[id];
            cantidadInput.disabled = true;
        }
    });

    // Listener para el Input de Cantidad
    cantidadInput.addEventListener('input', () => {
        if (check.checked) { // Solo actualiza si está marcado
            let val = cantidadInput.value || "1";
            if (parseFloat(val) < 1) val = "1";
            cantidadInput.value = val;
            materiasSeleccionadas[id].cantidad = val;
        }
    });
}

/**
 * Recolecta los datos y los envía a la API de solicitud de materia prima.
 * Esta función es llamada por el botón 'onclick="enviarSolicitud()"'.
 */ 
async function enviarSolicitud() {
    // 1. Recolectar materias primas
    const seleccionados = Object.entries(materiasSeleccionadas).map(([id, item]) => ({
        id: id,
        cantidad: parseFloat(item.cantidad) || 0
    }));

    if (seleccionados.length === 0) {
        alert("No has seleccionado ninguna materia prima.");
        return;
    }

    // 2. Obtener origen
    const tipoOrigen = document.getElementById('tipo_origen').value;
    let origenId = null;

    if (tipoOrigen === 'proveedor') {
        origenId = document.getElementById('proveedor_selector').value;
    } else if (tipoOrigen === 'sucursal') {
        origenId = document.getElementById('sucursal_selector').value;
    }

    if (!tipoOrigen || !origenId) {
        alert("Por favor, selecciona un origen válido.");
        return;
    }
    
    // 3. Obtener Fecha y Hora (NUEVO)
    const fecha = document.getElementById('fecha_solicitud').value;
    const hora = document.getElementById('hora_solicitud').value;
    const comentarios = document.getElementById('comentarios-solicitud').value;

    if (!fecha) {
        alert("Por favor, selecciona una fecha requerida para la entrega.");
        return;
    }
    // La hora puede ser opcional si así lo deseas, aquí la dejo como opcional en la validación estricta
    // pero se envía al backend.

    // 4. Preparar datos
    const dataParaEnviar = {
        carrito: seleccionados,
        tipo_origen: tipoOrigen,
        origen_id: origenId,
        fecha_entrega: fecha,
        hora_entrega: hora,
        comentarios: comentarios
    };
    
    const botonEnviar = document.getElementById('botonEnviar');
    botonEnviar.disabled = true;
    botonEnviar.textContent = "Procesando...";

    try {
        const response = await fetch("/api/solicitar_materia_prima", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dataParaEnviar)
        });
        const data = await response.json();
        
        if (response.ok && data.success) {
            alert("✅ Solicitud registrada exitosamente.");
            // Limpieza completa
            materiasSeleccionadas = {};
            document.getElementById('listaSeleccionadas').innerHTML = '';
            document.getElementById('tipo_origen').value = '';
            document.getElementById('selector-proveedor-div').style.display = 'none';
            document.getElementById('selector-sucursal-div').style.display = 'none';
            document.getElementById('buscador').value = '';
            // Limpiar fecha y hora
            document.getElementById('fecha_solicitud').value = '';
            document.getElementById('hora_solicitud').value = '';
            document.getElementById('comentarios-solicitud').value = '';
        } else {
            alert(`❌ Error: ${data.message}`);
        }
    } catch (err) {
        console.error("Error:", err);
        alert("❌ Error de conexión.");
    } finally {
        botonEnviar.disabled = false;
        botonEnviar.textContent = "Confirmar y Registrar Solicitud";
    }
}

// --- Lógica para mostrar/ocultar selectores de Origen (Añadido) ---
document.addEventListener('DOMContentLoaded', () => {
    const tipoOrigenSelect = document.getElementById('tipo_origen');
    const proveedorDiv = document.getElementById('selector-proveedor-div');
    const sucursalDiv = document.getElementById('selector-sucursal-div');

    if (tipoOrigenSelect) {
        tipoOrigenSelect.addEventListener('change', () => {
            const tipo = tipoOrigenSelect.value;
            
            proveedorDiv.style.display = (tipo === 'proveedor') ? 'block' : 'none';
            sucursalDiv.style.display = (tipo === 'sucursal') ? 'block' : 'none';
        });
    } else {
        console.warn("Elemento 'tipo_origen' no encontrado. Asegúrate de estar en la página correcta.");
    }
});