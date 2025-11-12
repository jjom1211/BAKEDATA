document.addEventListener('DOMContentLoaded', function() {
    
    const tableBody = document.getElementById('pedidos-table-body');
    const modalOverlay = document.getElementById('detalle-modal-overlay');
    const modalContent = document.getElementById('modal-body-content');
    const closeButton = document.querySelector('.modal-close-button');

    // --- Función para MOSTRAR el modal ---
    function showModal() {
        modalOverlay.style.display = 'block';
    }

    // --- Función para OCULTAR el modal ---
    function hideModal() {
        modalOverlay.style.display = 'none';
        modalContent.innerHTML = '<p>Cargando...</p>'; // Resetea el contenido
    }

    // Cierra el modal al hacer clic en el botón de cerrar o en el fondo
    closeButton.addEventListener('click', hideModal);
    modalOverlay.addEventListener('click', function(event) {
        if (event.target === modalOverlay) {
            hideModal();
        }
    });

tableBody.addEventListener('click', function(event) {
    if (event.target.classList.contains('btn-detalles')) {
        const pedidoId = event.target.dataset.id;
        showModal();
        
        fetch(`/Pedidos/${pedidoId}`)
            .then(response => {
                if (!response.ok) throw new Error('Respuesta del servidor no fue exitosa.');
                return response.json();
            })
            .then(details => {
                if (details.error) throw new Error(details.error);
                
                const montoFormateado = details.ped_monto_total.toLocaleString('es-MX', {
                    style: 'currency',
                    currency: 'MXN'
                });

                // --- HTML CON UN LUGAR PARA LA LISTA DE ÍTEMS ---
                modalContent.innerHTML = `
                    <h4>Detalles Generales</h4>
                    <ul>
                        <li><strong># Pedido:</strong> ${details.ped_id}</li>
                        <li><strong>Fecha:</strong> ${details.ped_fecha_pedido}</li>
                        <li><strong>Asunto:</strong> ${details.ped_asunto}</li>
                        <li><strong>Monto Total:</strong> ${montoFormateado}</li>
                        <li><strong>Estado:</strong> ${details.ped_estado_pedido}</li>
                        <li><strong>Registrado por:</strong> ${details.creador_nombre}</li>
                    </ul>
                    <h4>Origen y Destino</h4>
                    <ul>
                        <li><strong>Origen:</strong> ${details.sucursal_origen_nombre}</li>
                        <li><strong>Destino:</strong> ${details.sucursal_destino_nombre}</li>
                        <li><strong>Dirección:</strong> ${details.sucursal_destino_direccion}</li>
                    </ul>
                    <h4>Comentarios</h4>
                    <p>${details.ped_comentarios || 'Ninguno'}</p>
                    
                    <div id="lista-items-modal"></div>
                `;

                // --- LÓGICA NUEVA PARA CONSTRUIR LA LISTA DE ÍTEMS ---
                const listaItemsDiv = modalContent.querySelector('#lista-items-modal');
                let itemsHTML = '';

                // Construir sección de Productos
                if (details.productos && details.productos.length > 0) {
                    itemsHTML += '<h4>Productos</h4><ul>';
                    details.productos.forEach(item => {
                        itemsHTML += `<li>${item.detpedpro_cantidad} x ${item.pro_nombre}</li>`;
                    });
                    itemsHTML += '</ul>';
                }

                // Construir sección de Materias Primas
                if (details.materias_primas && details.materias_primas.length > 0) {
                    itemsHTML += '<h4>Materias Primas</h4><ul>';
                    details.materias_primas.forEach(item => {
                        itemsHTML += `<li>${item.detpedmat_cantidad} x ${item.matprim_nombre}</li>`;
                    });
                    itemsHTML += '</ul>';
                }
                
                // Si no hay ningún ítem, mostrar un mensaje
                if (itemsHTML === '') {
                    listaItemsDiv.innerHTML = '<p>Este pedido no contiene productos o materias primas detalladas.</p>';
                } else {
                    listaItemsDiv.innerHTML = itemsHTML;
                }
            })
            .catch(error => {
                console.error('Error al obtener detalles:', error);
                modalContent.innerHTML = '<p style="color: red;">No se pudieron cargar los detalles.</p>';
            });
    }
    });
    const backButton = document.getElementById('backButton');
    if (backButton) {
        backButton.addEventListener('click', () => {
            window.history.back(); // Esta función te regresa a la página anterior
        });
    }
});
