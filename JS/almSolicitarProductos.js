document.addEventListener('DOMContentLoaded', () => {
    // --- Referencias ---
    const buscador = document.getElementById('buscador-productos');
    const listaProductosDiv = document.getElementById('lista-productos');
    const listaCarritoDiv = document.getElementById('lista-carrito');
    const carritoTotalMonto = document.getElementById('carrito-total-monto');
    const btnConfirmarSolicitud = document.getElementById('btn-confirmar-solicitud');
    
    // Inputs de formulario
    const sucursalOrigenSelector = document.getElementById('sucursal-origen');
    const fechaInput = document.getElementById('fecha-entrega');
    const horaInput = document.getElementById('hora-entrega');
    const comentariosInput = document.getElementById('comentarios-solicitud');
    
    let carrito = []; 

    // --- Helpers ---
    const formatearMoneda = (val) => val.toLocaleString('es-MX', { style: 'currency', currency: 'MXN' });

    // --- Renderizado ---
    const renderizarProductos = (productosFiltrados) => {
        listaProductosDiv.innerHTML = '';
        if (productosFiltrados.length === 0) {
            listaProductosDiv.innerHTML = '<p class="empty-msg">No se encontraron productos.</p>'; return;
        }
        productosFiltrados.forEach(prod => {
            const enCarrito = carrito.find(item => item.id === prod.id);
            const div = document.createElement('div');
            div.className = 'item-producto';
            div.innerHTML = `
                <div class="info">
                    <span class="name">${prod.nombre}</span>
                    <span class="meta">#${prod.id} | ${prod.unidad} | ${formatearMoneda(prod.costo)}</span>
                </div>
                <button data-id="${prod.id}" class="btn-add" ${enCarrito ? 'disabled' : ''}>
                    ${enCarrito ? 'Añadido' : 'Añadir'}
                </button>
            `;
            listaProductosDiv.appendChild(div);
        });
    };

    const renderizarCarrito = () => {
        listaCarritoDiv.innerHTML = '';
        let total = 0;
        
        if (carrito.length === 0) {
            listaCarritoDiv.innerHTML = '<p class="empty-msg">El carrito está vacío.</p>';
            validarBoton();
            return;
        } 
        
        carrito.forEach((item, index) => {
            const itemTotal = item.costo * item.cantidad;
            total += itemTotal;
            
            const div = document.createElement('div');
            div.className = 'item-carrito';
            div.innerHTML = `
                <div class="cart-info">
                    <span class="cart-name">${item.nombre}</span>
                    <small>${formatearMoneda(itemTotal)}</small>
                </div>
                <div class="cart-controls">
                    <input type="number" value="${item.cantidad}" min="1" data-index="${index}" class="input-cantidad">
                    <button data-index="${index}" class="btn-remove">X</button>
                </div>
            `;
            listaCarritoDiv.appendChild(div);
        });
        
        carritoTotalMonto.textContent = formatearMoneda(total);
        validarBoton();
    };

    // --- Validación del Botón Enviar ---
    const validarBoton = () => {
        const tieneItems = carrito.length > 0;
        const tieneOrigen = sucursalOrigenSelector.value !== "";
        const tieneFecha = fechaInput.value !== ""; // Validación visual simple
        
        btnConfirmarSolicitud.disabled = !(tieneItems && tieneOrigen);
    };

    // --- Listeners ---
    sucursalOrigenSelector.addEventListener('change', validarBoton);
    fechaInput.addEventListener('change', validarBoton);

    const actualizarCantidad = (index, val) => {
        if (val > 0) carrito[index].cantidad = val;
        else carrito.splice(index, 1);
        renderizarCarrito();
        // Re-renderizar productos para habilitar botones si se eliminó algo
        const termino = buscador.value.toLowerCase().trim();
        const filtrados = TODOS_LOS_PRODUCTOS.filter(p => p.nombre.toLowerCase().includes(termino));
        renderizarProductos(filtrados);
    };

    buscador.addEventListener('input', () => {
        const termino = buscador.value.toLowerCase().trim();
        const filtrados = TODOS_LOS_PRODUCTOS.filter(p => 
            p.nombre.toLowerCase().includes(termino) || p.id.toString().includes(termino)
        );
        renderizarProductos(filtrados);
    });

    // Click en Productos (Añadir)
    listaProductosDiv.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-add') && !e.target.disabled) {
            const id = e.target.dataset.id;
            const prod = TODOS_LOS_PRODUCTOS.find(p => p.id == id);
            if (prod) {
                carrito.push({ ...prod, cantidad: 1 });
                renderizarCarrito();
                e.target.textContent = 'Añadido';
                e.target.disabled = true;
            }
        }
    });

    // Click en Carrito (Editar/Borrar)
    listaCarritoDiv.addEventListener('change', (e) => {
        if (e.target.classList.contains('input-cantidad')) {
            actualizarCantidad(parseInt(e.target.dataset.index), parseInt(e.target.value));
        }
    });
    listaCarritoDiv.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-remove')) {
            carrito.splice(parseInt(e.target.dataset.index), 1);
            renderizarCarrito();
            // Resetear filtro para actualizar estados de botones
            buscador.dispatchEvent(new Event('input')); 
        }
    });

    // --- ENVIAR SOLICITUD ---
    btnConfirmarSolicitud.addEventListener('click', async () => {
        const origenId = sucursalOrigenSelector.value;
        const fecha = fechaInput.value;
        const hora = horaInput.value;

        // Validación final estricta
        if (!origenId) return alert('Selecciona una sucursal de origen.');
        if (!fecha) return alert('Debes seleccionar una fecha de entrega.');
        if (carrito.length === 0) return alert('El carrito está vacío.');

        const payload = {
            carrito: carrito,
            sucursal_origen_id: origenId,
            fecha_entrega: fecha,
            hora_entrega: hora,
            comentarios: comentariosInput.value
        };

        btnConfirmarSolicitud.disabled = true;
        btnConfirmarSolicitud.textContent = 'Enviando...';

        try {
            const res = await fetch('/api/finalizar_solicitud', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if (res.ok && data.success) {
                alert(data.message);
                // Reset completo
                carrito = [];
                comentariosInput.value = '';
                fechaInput.value = '';
                horaInput.value = '';
                renderizarCarrito();
                buscador.value = '';
                buscador.dispatchEvent(new Event('input'));
            } else {
                alert('Error: ' + data.message);
            }
        } catch (err) {
            alert('Error de conexión con el servidor.');
        } finally {
            btnConfirmarSolicitud.disabled = false;
            btnConfirmar.textContent = 'Finalizar Solicitud';
            validarBoton(); // Re-checar estado
        }
    });

    // Inicialización
    renderizarProductos(TODOS_LOS_PRODUCTOS);
    renderizarCarrito();
});