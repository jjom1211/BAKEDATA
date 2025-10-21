// Archivo: JS/solicitar_productos.js
document.addEventListener('DOMContentLoaded', () => {
    // --- Referencias a Elementos ---
    const buscador = document.getElementById('buscador-productos');
    const listaProductosDiv = document.getElementById('lista-productos');
    const listaCarritoDiv = document.getElementById('lista-carrito');
    const carritoTotalMonto = document.getElementById('carrito-total-monto');
    const btnConfirmarSolicitud = document.getElementById('btn-confirmar-solicitud');
    const comentariosInput = document.getElementById('comentarios-solicitud');
    const sucursalOrigenSelector = document.getElementById('sucursal-origen');
    // TODOS_LOS_PRODUCTOS viene de la plantilla Jinja
    let carrito = []; 

    // --- Funciones Auxiliares ---
    const formatearMoneda = (valor) => valor.toLocaleString('es-MX', { style: 'currency', currency: 'MXN' });

    const renderizarProductos = (productosFiltrados) => {
        listaProductosDiv.innerHTML = '';
        if (productosFiltrados.length === 0) {
            listaProductosDiv.innerHTML = '<p>No se encontraron productos.</p>'; return;
        }
        productosFiltrados.forEach(prod => {
            const enCarrito = carrito.find(item => item.id === prod.id);
            const botonDeshabilitado = enCarrito ? 'disabled' : '';
            const textoBoton = enCarrito ? 'En Solicitud' : 'Añadir';
            const divProducto = document.createElement('div');
            divProducto.classList.add('item-producto');
            divProducto.innerHTML = `
                <span>#${prod.id} - ${prod.nombre} (${prod.unidad}) - ${formatearMoneda(prod.costo)}</span>
                <button data-id="${prod.id}" class="btn-add" ${botonDeshabilitado}>${textoBoton}</button>
            `;
            listaProductosDiv.appendChild(divProducto);
        });
    };

    const renderizarCarrito = () => {
        listaCarritoDiv.innerHTML = '';
        let total = 0;
        if (carrito.length === 0) {
            listaCarritoDiv.innerHTML = '<p>Añade productos desde la lista.</p>';
            btnConfirmarSolicitud.disabled = true;
        } else {
            carrito.forEach((item, index) => {
                const itemTotal = item.costo * item.cantidad;
                total += itemTotal;
                const divItem = document.createElement('div');
                divItem.classList.add('item-carrito');
                divItem.innerHTML = `
                    <span>${item.nombre}</span>
                    <input type="number" value="${item.cantidad}" min="1" data-index="${index}" class="input-cantidad">
                    <span>${formatearMoneda(itemTotal)}</span>
                    <button data-index="${index}" class="btn-remove">X</button>
                `;
                listaCarritoDiv.appendChild(divItem);
            });
            btnConfirmarSolicitud.disabled = !sucursalOrigenSelector.value;
        }
        carritoTotalMonto.textContent = formatearMoneda(total);
    };

// --- CAMBIO: Listener para el selector de sucursal de ORIGEN ---
    sucursalOrigenSelector.addEventListener('change', () => {
        if (carrito.length > 0) {
            btnConfirmarSolicitud.disabled = !sucursalOrigenSelector.value;
        }
    });



    const actualizarCantidad = (index, nuevaCantidad) => {
        if (nuevaCantidad > 0) {
            carrito[index].cantidad = nuevaCantidad;
        } else {
            carrito.splice(index, 1); // Elimina si la cantidad es 0 o menos
        }
        renderizarCarrito();
        renderizarProductos(TODOS_LOS_PRODUCTOS); // Actualiza botones "Añadir"
    };

    // --- Lógica del Buscador ---
    buscador.addEventListener('input', () => {
        const termino = buscador.value.toLowerCase().trim();
        const filtrados = TODOS_LOS_PRODUCTOS.filter(prod =>
            prod.nombre.toLowerCase().includes(termino) || prod.id.toString().includes(termino)
        );
        renderizarProductos(filtrados);
    });

    // --- Lógica de Añadir al Carrito ---
    listaProductosDiv.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-add') && !e.target.disabled) {
            const productoId = e.target.dataset.id;
            const producto = TODOS_LOS_PRODUCTOS.find(p => p.id == productoId);
            if (producto) {
                carrito.push({
                    id: producto.id,
                    nombre: producto.nombre,
                    costo: producto.costo, // Usamos costo
                    cantidad: 1
                });
                renderizarCarrito();
                e.target.disabled = true;
                e.target.textContent = 'En Solicitud';
            }
        }
    });

    // --- Lógica del Carrito (Actualizar Cantidad y Eliminar) ---
    listaCarritoDiv.addEventListener('change', (e) => {
        if (e.target.classList.contains('input-cantidad')) {
            const index = parseInt(e.target.dataset.index);
            const nuevaCantidad = parseInt(e.target.value);
            actualizarCantidad(index, nuevaCantidad);
        }
    });
    listaCarritoDiv.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-remove')) {
            const index = parseInt(e.target.dataset.index);
            carrito.splice(index, 1);
            renderizarCarrito();
            renderizarProductos(TODOS_LOS_PRODUCTOS);
        }
    });

    // --- Lógica para Finalizar Solicitud ---
    btnConfirmarSolicitud.addEventListener('click', async () => {
        const sucursalOrigenId = sucursalOrigenSelector.value;
        if (!sucursalOrigenId) {
            alert('Por favor, selecciona una sucursal de origen.');
            return;
        }
        const solicitudData = {
            carrito: carrito,
            comentarios: comentariosInput.value,
            sucursal_origen_id: sucursalOrigenId // --- ENVIAR AL BACKEND ---
        };

        btnConfirmarSolicitud.disabled = true;
        btnConfirmarSolicitud.textContent = 'Registrando...';

        try {
            const response = await fetch('/api/finalizar_solicitud', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(solicitudData)
            });
            const result = await response.json();
            alert(result.message);

            if (response.ok) {
                carrito = [];
                comentariosInput.value = '';
                renderizarCarrito();
                renderizarProductos(TODOS_LOS_PRODUCTOS);
            }
        } catch (error) {
            alert('Error al registrar la solicitud: ' + error.message);
        } finally {
            btnConfirmarSolicitud.disabled = false;
            btnConfirmarSolicitud.textContent = 'Finalizar Solicitud';
        }
    });

    // --- Carga Inicial ---
    renderizarProductos(TODOS_LOS_PRODUCTOS);
    renderizarCarrito();
    btnConfirmarSolicitud.disabled = carrito.length === 0 || !sucursalOrigenSelector.value;
});