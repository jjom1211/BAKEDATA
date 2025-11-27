document.addEventListener('DOMContentLoaded', function() {
    
    const tableBody = document.getElementById('pedidos-table-body');
    const modalOverlay = document.getElementById('detalle-modal-overlay');
    const modalContent = document.getElementById('modal-body-content');
    const closeButton = document.querySelector('.modal-close-button');

    function showModal() {
        if(modalOverlay) modalOverlay.style.display = 'block';
    }

    function hideModal() {
        if(modalOverlay) modalOverlay.style.display = 'none';
        if(modalContent) modalContent.innerHTML = '<p style="text-align:center; padding:20px;">Cargando información...</p>';
    }

    if(closeButton) closeButton.addEventListener('click', hideModal);
    
    if(modalOverlay) {
        modalOverlay.addEventListener('click', function(event) {
            if (event.target === modalOverlay) hideModal();
        });
    }

    if(tableBody) {
        tableBody.addEventListener('click', function(event) {
            if (event.target.classList.contains('btn-detalles')) {
                const pedidoId = event.target.dataset.id;
                showModal();
                
                fetch(`/Pedidos/${pedidoId}`)
                    .then(response => {
                        if (!response.ok) throw new Error('Error al consultar el servidor.');
                        return response.json();
                    })
                    .then(details => {
                        if (details.error) throw new Error(details.error);
                        
                        const montoFormateado = details.ped_monto_total.toLocaleString('es-MX', {
                            style: 'currency', currency: 'MXN'
                        });

                        // --- CONSTRUCCIÓN DEL HTML DEL MODAL ---
                        let contenidoHTML = `
                            <div class="modal-section">
                                <h4><i class="fas fa-info-circle"></i> Detalles Generales</h4>
                                <ul class="details-list">
                                    <li><strong># Pedido:</strong> ${details.ped_id}</li>
                                    <li><strong>Estado:</strong> <span class="status-badge">${details.ped_estado_pedido}</span></li>
                                    <li><strong>Registrado por:</strong> ${details.creador_nombre}</li>
                                    <li><strong>Fecha Solicitud:</strong> ${details.ped_fecha_pedido}</li>
                                    <li><strong>Programación Entrega:</strong> ${details.ped_fecha_entrega} (${details.ped_hora_entrega})</li>
                                    <li><strong>Asunto:</strong> ${details.ped_asunto}</li>
                                    <li><strong>Monto Total:</strong> <span class="amount">${montoFormateado}</span></li>
                                </ul>
                            </div>

                            <div class="modal-section">
                                <h4><i class="fas fa-map-marker-alt"></i> Ruta Logística</h4>
                                <ul class="details-list">
                                    <li><strong>Origen:</strong> ${details.origen_nombre}</li>
                                    <li><strong>Destino:</strong> ${details.destino_nombre}</li>
                                    <li><strong>Dirección:</strong> <span style="font-size:0.9em; color:#555;">${details.destino_direccion}</span></li>
                                </ul>
                                <div class="comments-box">
                                    <strong  style= "color:#df6c55">Comentarios:</strong>
                                    <p>${details.ped_comentarios || 'Sin comentarios adicionales.'}</p>
                                </div>
                            </div>
                            
                            <div class="modal-section">
                                <h4><i class="fas fa-boxes"></i> Contenido del Pedido</h4>
                                <div id="lista-items-modal">`;

                        // --- Lógica de Ítems ---
                        let itemsHTML = '';

                        if (details.productos && details.productos.length > 0) {
                            itemsHTML += '<h5 style="margin:10px 0 5px 0; color:#df6c55;">Productos</h5><ul class="items-list">';
                            details.productos.forEach(item => {
                                const unidad = item.pro_unimed ? `(${item.pro_unimed})` : '';
                                itemsHTML += `<li><strong>${item.detpedpro_cantidad}</strong> x ${item.pro_nombre} ${unidad}</li>`;
                            });
                            itemsHTML += '</ul>';
                        }

                        if (details.materias_primas && details.materias_primas.length > 0) {
                            itemsHTML += '<h5 style="margin:10px 0 5px 0; color:#df6c55;">Materias Primas</h5><ul class="items-list">';
                            details.materias_primas.forEach(item => {
                                const unidad = item.matprim_unimed ? `(${item.matprim_unimed})` : '';
                                itemsHTML += `<li><strong>${item.detpedmat_cantidad}</strong> x ${item.matprim_nombre} ${unidad}</li>`;
                            });
                            itemsHTML += '</ul>';
                        }
                        
                        if (itemsHTML === '') {
                            itemsHTML = '<p class="empty-msg">No hay ítems detallados.</p>';
                        }

                        contenidoHTML += itemsHTML + `</div></div>`;
                        
                        modalContent.innerHTML = contenidoHTML;
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        modalContent.innerHTML = `<div class="error-msg"><p>Error: ${error.message}</p></div>`;
                    });
            }
        });
    }

    const backButton = document.getElementById('backButton');
    if (backButton) {
        backButton.addEventListener('click', () => window.history.back());
    }
});