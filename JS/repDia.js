document.addEventListener('DOMContentLoaded', () => {
    // --- Selección de Elementos del DOM ---
    const modalOverlay = document.getElementById('modal-overlay');
    const closeModalButton = document.querySelector('.modal-close');
    const listaActividades = document.getElementById('lista-actividades');
    const modalBody = document.getElementById('modal-body'); // Asegúrate de que tu modal tenga este ID
    
    // Asumimos que tus botones tienen estos IDs en el HTML
    const btnRegresar = document.getElementById('btn-regresar');
    const btnConfirmar = document.getElementById('btn-confirmar');


    // --- Funciones Auxiliares ---

    /**
     * Muestra el modal y opcionalmente un estado de carga.
     * @param {boolean} loading - Si es true, muestra un mensaje de carga.
     */
    const mostrarModal = (loading = false) => {
        if (loading) {
            modalBody.innerHTML = '<p>Cargando detalles...</p>';
        }
        modalOverlay.style.display = 'flex';
    };

    /**
     * Oculta el modal.
     */
    const cerrarModal = () => {
        modalOverlay.style.display = 'none';
    };

    /**
     * Construye y devuelve el HTML para la lista de ítems de un pedido.
     * @param {object} data - El objeto de datos recibido de la API.
     * @returns {string} - El string HTML de la lista.
     */
    const renderizarListaItems = (data) => {
        let itemsHTML = '';

        if ((data.productos && data.productos.length > 0) || (data.materias_primas && data.materias_primas.length > 0)) {
            itemsHTML += '<h4>Contenido del Pedido</h4><ul>';
            
            data.productos?.forEach(item => {
                itemsHTML += `<li><strong>Producto:</strong> <span>${item.detpedpro_cantidad} x ${item.pro_nombre}</span></li>`;
            });
            
            data.materias_primas?.forEach(item => {
                itemsHTML += `<li><strong>Materia Prima:</strong> <span>${item.detpedmat_cantidad} x ${item.matprim_nombre}</span></li>`;
            });

            itemsHTML += '</ul>';
        } else {
            itemsHTML = '<p>Este pedido no contiene productos o materias primas detalladas.</p>';
        }
        return itemsHTML;
    };

    
    // --- Funciones Principales ---

    /**
     * Busca los detalles de un reparto y los muestra en el modal.
     * @param {string} repartoId - El ID del reparto a buscar.
     */
    const abrirModalConDetalles = async (repartoId) => {
        mostrarModal(true); // Muestra el modal con estado de carga

        try {
            const response = await fetch(`/detalles_reparto/${repartoId}`);
            if (!response.ok) {
                throw new Error('Reparto no encontrado');
            }
            const data = await response.json();

            // Llenar el modal con los datos
            const montoFormateado = parseFloat(data.ped_monto_total).toFixed(2);
            const itemsHTML = renderizarListaItems(data);

            modalBody.innerHTML = `
                <h4>Detalles Generales</h4>
                <ul>
                    <li><strong>ID Reparto:</strong> <span>${data.rep_id}</span></li>
                    <li><strong>Asunto:</strong> <span>${data.ped_asunto}</span></li>
                    <li><strong>Estado:</strong> <span>${data.rep_estado_reparto}</span></li>
                    <li><strong>Monto Total:</strong> <span>$${montoFormateado}</span></li>
                </ul>
                <h4>Origen y Destino</h4>
                <ul>
                    <li><strong>Origen:</strong> <span>${data.sucursal_origen || 'N/A'}</span></li>
                    <li><strong>Destino:</strong> <span>${data.sucursal_destino || 'N/A'}</span></li>
                    <li><strong>Dirección:</strong> <span>${data.sucursal_destino_direccion || 'No especificada'}</span></li>
                </ul>
                <h4>Fechas</h4>
                <ul>
                    <li><strong>Fecha de Entrega:</strong> <span>${data.rep_fecha_entrega}</span></li>
                </ul>
                ${itemsHTML}
            `;
        } catch (error) {
            console.error('Error al obtener detalles:', error);
            modalBody.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    };

    /**
     * Confirma la entrega de los pedidos seleccionados.
     */
    const confirmarEntrega = async () => {
        const seleccionados = Array.from(
            document.querySelectorAll('input[name="pedidos"]:checked')
        ).map(cb => cb.value);

        if (seleccionados.length === 0) {
            alert("Por favor, selecciona al menos un pedido para confirmar.");
            return;
        }

        btnConfirmar.disabled = true; // Deshabilitar botón para evitar doble clic
        btnConfirmar.textContent = 'Procesando...';

        try {
            const response = await fetch('/confirmar_entregas', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pedidos: seleccionados })
            });
            const res = await response.json();
            if (!response.ok) {
                throw new Error(res.message);
            }
            alert(res.message);
            location.reload();
        } catch (err) {
            console.error("Error al confirmar:", err);
            alert("Error: " + err.message);
            btnConfirmar.disabled = false; // Rehabilitar botón en caso de error
            btnConfirmar.textContent = 'Confirmar avance';
        }
    };


    // --- Asignación de Eventos (Event Listeners) ---

    // 1. Abrir modal
    if (listaActividades) {
        listaActividades.addEventListener('click', (event) => {
            if (event.target.classList.contains('btn-detalles')) {
                const repartoId = event.target.dataset.repartoId;
                abrirModalConDetalles(repartoId);
            }
        });
    }

    // 2. Cerrar modal
    closeModalButton.addEventListener('click', cerrarModal);
    modalOverlay.addEventListener('click', (event) => {
        if (event.target === modalOverlay) {
            cerrarModal();
        }
    });

    // 3. Botones de acción principales
    if (btnRegresar) {
        btnRegresar.addEventListener('click', () => window.history.back());
    }
    if (btnConfirmar) {
        btnConfirmar.addEventListener('click', confirmarEntrega);
    }
});