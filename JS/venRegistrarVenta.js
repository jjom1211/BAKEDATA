// Archivo: JS/venRegistrarVenta.js

// --- FUNCIONES AUXILIARES (Definidas primero) ---

/**
 * Formatea un número como moneda mexicana (MXN).
 * @param {number | string} valor - El número a formatear.
 * @returns {string} - El valor formateado como moneda.
 */
const formatearMoneda = (valor) => {
    let numValor = parseFloat(valor);
    if (isNaN(numValor)) {
        numValor = 0;
    }
    return numValor.toLocaleString('es-MX', { style: 'currency', currency: 'MXN' });
};

/**
 * Muestra el paso 2 (Resumen) del modal, adaptándolo al método de pago.
 * @param {string} metodo - 'efectivo' o 'tarjeta'.
 */


/**
 * Renderiza la lista de productos disponibles en la columna izquierda.
 * @param {Array} productosFiltrados - La lista de productos a mostrar.
 * @param {HTMLElement} listaDiv - El elemento donde se renderizará la lista.
 * @param {Array} carritoActual - El carrito actual para saber qué botones deshabilitar.
 */
const renderizarProductos = (productosFiltrados, listaDiv, carritoActual) => {
    if (!listaDiv) {
        console.error("Error: listaProductosDiv no encontrado para renderizarProductos.");
        return;
    }
    listaDiv.innerHTML = ''; // Limpiamos antes de renderizar
    if (!productosFiltrados || productosFiltrados.length === 0) {
        listaDiv.innerHTML = '<p>No se encontraron productos.</p>';
        return;
    }
    productosFiltrados.forEach(prod => {
        // Asegurarse de que el producto tenga las propiedades necesarias
        const id = prod.id || 'N/A';
        const nombre = prod.nombre || 'Producto sin nombre';
        const stock = prod.stock !== undefined ? prod.stock : 0;
        const unidad = prod.unidad || 'PZA';
        const precio = prod.precio !== undefined ? prod.precio : 0;

        const enCarrito = carritoActual.find(item => item.id === id);
        const botonDeshabilitado = enCarrito ? 'disabled' : '';
        const textoBoton = enCarrito ? 'En Carrito' : 'Añadir';
        const divProducto = document.createElement('div');
        divProducto.classList.add('item-producto');
        divProducto.innerHTML = `
            <span>#${id} - ${nombre} (${stock} ${unidad}) - ${formatearMoneda(precio)}</span>
            <button data-id="${id}" class="btn-add" ${botonDeshabilitado}>${textoBoton}</button>
        `;
        listaDiv.appendChild(divProducto);
    });
};

/**
 * Renderiza el contenido del carrito de compras.
 * @param {Array} carritoActual - El carrito a renderizar.
 * @param {HTMLElement} listaDiv - El elemento donde se renderizará el carrito.
 * @param {HTMLElement} totalSpan - El span donde se mostrará el total.
 * @param {HTMLElement} botonPago - El botón para proceder al pago.
 * @param {HTMLElement} selectorCaja - El selector de caja.
 */
const renderizarCarrito = (carritoActual, listaDiv, totalSpan, botonPago, selectorCaja) => {
    if (!listaDiv || !totalSpan || !botonPago || !selectorCaja) {
         console.error("Error: Faltan elementos del DOM para renderizarCarrito.");
         return;
    }
    listaDiv.innerHTML = '';
    let total = 0;
    if (!Array.isArray(carritoActual) || carritoActual.length === 0) {
        listaDiv.innerHTML = '<p>Añade productos desde la lista.</p>';
        botonPago.disabled = true;
    } else {
        carritoActual.forEach((item, index) => {
            const itemTotal = (item.precio || 0) * (item.cantidad || 0);
            total += itemTotal;
            const divItem = document.createElement('div');
            divItem.classList.add('item-carrito');
            divItem.innerHTML = `
                <span>${item.nombre || 'N/A'}</span>
                <input type="number" value="${item.cantidad || 1}" min="1" max="${item.stockMax || 1}" data-index="${index}" class="input-cantidad">
                <span>${formatearMoneda(itemTotal)}</span>
                <button data-index="${index}" class="btn-remove">X</button>
            `;
            listaDiv.appendChild(divItem);
        });
        // Habilita el pago solo si hay items Y se seleccionó una caja
        botonPago.disabled = !selectorCaja.value;
    }
    totalSpan.textContent = formatearMoneda(total);
};

/**
 * Calcula el cambio a devolver.
 * @param {Array} carritoActual - El carrito actual.
 * @param {HTMLElement} inputRecibido - El input del monto recibido.
 * @param {HTMLElement} spanCambio - El span donde mostrar el cambio.
 * @returns {number} - El monto del cambio.
 */
const calcularCambio = (carritoActual, inputRecibido, spanCambio) => {
    if (!inputRecibido || !spanCambio) return 0; // Verifica elementos
    const total = carritoActual.reduce((sum, item) => sum + (item.precio || 0) * (item.cantidad || 0), 0);
    const recibido = parseFloat(inputRecibido.value) || 0;
    const cambio = recibido - total;
    spanCambio.textContent = (cambio >= 0) ? formatearMoneda(cambio) : formatearMoneda(0);
    return cambio;
};

// --- LÓGICA PRINCIPAL (Dentro de DOMContentLoaded) ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM Cargado. Buscando elementos...");

    // --- Referencias a Elementos del DOM ---
    const ventaContainer = document.querySelector('.venta-container');
    const buscador = document.getElementById('buscador-productos');
    const listaProductosDiv = document.getElementById('lista-productos');
    const listaCarritoDiv = document.getElementById('lista-carrito');
    const carritoTotalMonto = document.getElementById('carrito-total-monto');
    const btnProcederPago = document.getElementById('btn-proceder-pago');
    const cajaSelector = document.getElementById('caja_selector_venta');
    const modalPago = document.getElementById('modal-pago');
    const cerrarModalBtn = document.getElementById('cerrar-modal-pago');
    const paso1Cobro = document.getElementById('paso1-cobro');
    const paso2Resumen = document.getElementById('paso2-resumen');
    const modalTotalPagar = document.getElementById('modal-total-pagar');
    const montoRecibidoInput = document.getElementById('monto-recibido');
    const modalCambio = document.getElementById('modal-cambio');
    const btnCalcularCambio = document.getElementById('btn-calcular-cambio');
    const modalResumenItems = document.getElementById('modal-resumen-items');
    const resumenTotal = document.getElementById('resumen-total');
    const resumenRecibido = document.getElementById('resumen-recibido');
    const resumenCambio = document.getElementById('resumen-cambio');
    const btnConfirmarVenta = document.getElementById('btn-confirmar-venta');
    const btnVolverCobro = document.getElementById('btn-volver-cobro');
    const metodoPagoRadios = document.querySelectorAll('input[name="metodo_pago"]'); // <-- NUEVO


    // --- Verificación de Elementos Esenciales ---
    if (!ventaContainer || !listaProductosDiv || !listaCarritoDiv || !carritoTotalMonto || !btnProcederPago || !cajaSelector || !modalPago
        || !cerrarModalBtn || !paso1Cobro || !paso2Resumen || !modalTotalPagar || !montoRecibidoInput || !modalCambio
        || !btnCalcularCambio || !modalResumenItems || !resumenTotal || !resumenRecibido || !resumenCambio
        || !btnConfirmarVenta || !btnVolverCobro)
    {
        console.error("Error crítico: Faltan uno o más elementos HTML esenciales para la interfaz (listas, botones, modal, etc.). Verifica los IDs.");
        alert("Error al cargar la interfaz. Faltan componentes. Revisa la consola (F12).");
        return; // Detiene la ejecución
    }

    // --- Variables de Estado ---
    let productosDisponibles = [];
    let carrito = [];
    const SUCURSAL_ID = ventaContainer.dataset.sucursalId;

    if (!SUCURSAL_ID) {
         console.error("Error crítico: No se encontró 'data-sucursal-id' en '.venta-container'.");
         alert("Error al cargar la página. No se pudo identificar la sucursal.");
         // Podríamos detener aquí si es absolutamente necesario
    }
    /**
 * Muestra el paso 2 (Resumen) del modal, adaptándolo al método de pago.
 * @param {string} metodo - 'efectivo' o 'tarjeta'.
 */
const mostrarResumen = (metodo) => {
    // --- Referencias a elementos (Asegúrate de que estas variables estén definidas en un ámbito superior o pásalas como argumentos) ---
    // Ejemplo: const carrito = window.carrito || []; // Accede a una variable global o pasada
    const modalResumenItems = document.getElementById('modal-resumen-items');
    const resumenMetodo = document.getElementById('resumen-metodo');
    const resumenTotal = document.getElementById('resumen-total');
    const resumenRecibido = document.getElementById('resumen-recibido');
    const resumenCambio = document.getElementById('resumen-cambio');
    const resumenEfectivoCampos = document.getElementById('resumen-efectivo-campos');
    const paso1Cobro = document.getElementById('paso1-cobro');
    const paso2Resumen = document.getElementById('paso2-resumen');
    const montoRecibidoInput = document.getElementById('monto-recibido');
    const modalCambio = document.getElementById('modal-cambio'); // Necesario para calcular en efectivo

    // Verifica que los elementos necesarios existan
    if (!modalResumenItems || !resumenMetodo || !resumenTotal || !resumenRecibido || !resumenCambio || !resumenEfectivoCampos || !paso1Cobro || !paso2Resumen || !montoRecibidoInput || !modalCambio) {
        console.error("Error en mostrarResumen: Faltan elementos del DOM.");
        alert("Error interno al mostrar el resumen. Revisa la consola.");
        return;
    }

    // --- VERIFICACIÓN DEL CARRITO ---
    console.log("Contenido del carrito ANTES de calcular total en mostrarResumen:", carrito); // Log para ver el carrito
    // --- FIN VERIFICACIÓN ---

    // Calcula el total A PARTIR de la variable 'carrito' actual
    const total = carrito.reduce((sum, item) => {
        const precio = parseFloat(item.precio) || 0;
        const cantidad = parseInt(item.cantidad) || 0;
        return sum + (precio * cantidad);
    }, 0); // Asegúrate de inicializar la suma en 0
    console.log(`Total calculado DENTRO de mostrarResumen: ${total}`); // Log para ver el total

    // Llena la lista de items en el resumen
    modalResumenItems.innerHTML = '<ul>' + carrito.map(item => `<li>${item.cantidad} x ${item.nombre}</li>`).join('') + '</ul>';
    // Muestra el método de pago
    resumenMetodo.textContent = metodo === 'efectivo' ? 'Efectivo' : 'Tarjeta';

    // --- Verificación Clave ---
    const totalFormateado = formatearMoneda(total); // Asume que formatearMoneda está definida
    console.log(`Total formateado: ${totalFormateado}`); // Log para ver el formato
    if (resumenTotal) {
        resumenTotal.textContent = totalFormateado;
        console.log("Elemento resumenTotal encontrado y actualizado."); // Log de confirmación
    } else {
        console.error("¡ERROR! Elemento resumenTotal NO encontrado."); // Log de error
    }
    // --- Fin Verificación ---

    // Muestra u oculta los campos de efectivo según el método
    if (metodo === 'efectivo') {
        const recibido = parseFloat(montoRecibidoInput.value) || 0;
        // Calcula el cambio aquí mismo
        const cambio = Math.max(0, recibido - total);
        resumenRecibido.textContent = formatearMoneda(recibido);
        resumenCambio.textContent = formatearMoneda(cambio);
        resumenEfectivoCampos.style.display = 'block'; // Muestra campos de efectivo
    } else {
        resumenEfectivoCampos.style.display = 'none'; // Oculta campos de efectivo
    }

    // Cambia la visibilidad de los pasos del modal
    paso1Cobro.style.display = 'none';
    paso2Resumen.style.display = 'block';
};
    /**
     * Actualiza la cantidad de un producto en el carrito.
     */
    const actualizarCantidad = (index, nuevaCantidad) => {
        const item = carrito[index];
        if (!item) return;
        if (nuevaCantidad > 0 && nuevaCantidad <= item.stockMax) {
            carrito[index].cantidad = nuevaCantidad;
        } else if (nuevaCantidad > item.stockMax) {
             alert(`Stock máximo para ${item.nombre} es ${item.stockMax}`);
             carrito[index].cantidad = item.stockMax;
             const inputVisual = listaCarritoDiv.querySelector(`input[data-index="${index}"]`);
             if(inputVisual) inputVisual.value = item.stockMax;
        } else {
             carrito.splice(index, 1);
        }
        renderizarCarrito(carrito, listaCarritoDiv, carritoTotalMonto, btnProcederPago, cajaSelector);
        // Volvemos a renderizar la lista filtrada actual
        const termino = buscador ? buscador.value.toLowerCase().trim() : '';
        const filtrados = Array.isArray(productosDisponibles) ? productosDisponibles.filter(p =>
            (p.nombre && p.nombre.toLowerCase().includes(termino)) ||
            (p.id && p.id.toString().includes(termino))
        ) : [];
        renderizarProductos(filtrados, listaProductosDiv, carrito);
    };

    /**
     * Obtiene la lista de productos disponibles de la API y los renderiza.
     */
    const cargarProductos = async () => {
        if (!SUCURSAL_ID) {
            listaProductosDiv.innerHTML = '<p style="color:red;">Error: No se pudo identificar la sucursal.</p>';
            return;
        }
        listaProductosDiv.innerHTML = '<p>Cargando productos...</p>';
        try {
            const response = await fetch(`/api/productos_venta/${SUCURSAL_ID}`);
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`No se pudieron cargar los productos (HTTP ${response.status}) ${errorText}`);
            }
            productosDisponibles = await response.json();
            if (!Array.isArray(productosDisponibles)) {
                 throw new Error("La respuesta de la API de productos no es válida.");
            }
            renderizarProductos(productosDisponibles, listaProductosDiv, carrito);
        } catch (error) {
            console.error('Error en cargarProductos:', error);
            listaProductosDiv.innerHTML = `<p style="color:red;">Error al cargar: ${error.message}</p>`;
        }
    };

    // --- Lógica del Buscador ---
    if (buscador) {
        buscador.addEventListener('input', () => {
            const termino = buscador.value.toLowerCase().trim();
            const filtrados = Array.isArray(productosDisponibles) ? productosDisponibles.filter(prod =>
                (prod.nombre && prod.nombre.toLowerCase().includes(termino)) ||
                (prod.id && prod.id.toString().includes(termino))
            ) : [];
            renderizarProductos(filtrados, listaProductosDiv, carrito);
        });
    }

// --- Lógica de Añadir al Carrito ---
    // Asegúrate de que 'listaProductosDiv' es la referencia correcta al DIV que contiene la lista de productos
    if (listaProductosDiv) {
        listaProductosDiv.addEventListener('click', (e) => {
            // Verifica si el elemento clickeado tiene la clase 'btn-add' Y no está deshabilitado
            if (e.target.classList.contains('btn-add') && !e.target.disabled) {
                
                // --- PUNTO CRÍTICO 1: Confirmar que el clic se detecta ---
                console.log("Botón Añadir clickeado! ID:", e.target.dataset.id); 

                const productoId = parseInt(e.target.dataset.id);
                // Busca el producto correspondiente en la lista de productos disponibles
                const producto = productosDisponibles.find(p => parseInt(p.id) === productoId); // Asegura que ambos sean números
                if (producto) {
                    // --- PUNTO CRÍTICO 2: Confirmar que el producto se encontró ---
                    console.log("Producto encontrado:", producto); 

                    // Añade el producto al array 'carrito'
                    carrito.push({
                        id: producto.id, 
                        nombre: producto.nombre, 
                        precio: producto.precio,
                        cantidad: 1, // Cantidad inicial siempre es 1
                        stockMax: producto.stock // Guarda el stock máximo para validaciones
                    });

                    // Vuelve a dibujar el carrito y la lista de productos (para actualizar botones)
                    renderizarCarrito(carrito, listaCarritoDiv, carritoTotalMonto, btnProcederPago, cajaSelector); 
                    renderizarProductos(productosDisponibles, listaProductosDiv, carrito); 
                    
                    // --- PUNTO CRÍTICO 3: Verificar si el botón se deshabilita (esto ya lo hacía antes) ---
                    // e.target.disabled = true; 
                    // e.target.textContent = 'En Carrito';
                    
                    console.log("Producto añadido al carrito. Carrito actual:", carrito); // Log final
                } else {
                     // Si el producto no se encuentra (esto sería raro)
                     console.warn("Producto no encontrado en la lista 'productosDisponibles' con ID:", productoId);
                }
            }
        });
    } else {
        console.error("No se encontró el elemento '#lista-productos' para añadir el listener.");
    }
    // --- Lógica del Carrito ---
    if (listaCarritoDiv) {
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
                if (carrito[index]) {
                    carrito.splice(index, 1);
                    renderizarCarrito(carrito, listaCarritoDiv, carritoTotalMonto, btnProcederPago, cajaSelector);
                    const termino = buscador ? buscador.value.toLowerCase().trim() : '';
                    const filtrados = Array.isArray(productosDisponibles) ? productosDisponibles.filter(p =>
                        (p.nombre && p.nombre.toLowerCase().includes(termino)) ||
                        (p.id && p.id.toString().includes(termino))
                    ) : [];
                     renderizarProductos(filtrados, listaProductosDiv, carrito);
                }
            }
        });
    }

    // --- Lógica del Selector de Caja ---
    if (cajaSelector && btnProcederPago) {
        cajaSelector.addEventListener('change', () => {
            btnProcederPago.disabled = carrito.length === 0 || !cajaSelector.value;
        });
    }

    // --- Lógica del Modal de Pago ---
    if (btnProcederPago) {
        btnProcederPago.addEventListener('click', () => {
            if (!cajaSelector || !cajaSelector.value) {
                alert('Por favor, selecciona una caja para continuar.');
                return;
            }
             const total = carrito.reduce((sum, item) => sum + item.precio * item.cantidad, 0);
            modalTotalPagar.textContent = formatearMoneda(total);
            document.querySelector('input[name="metodo_pago"][value="efectivo"]').checked = true;
            paso1Cobro.style.display = 'block'; // Muestra cobro (efectivo) por defecto
            paso2Resumen.style.display = 'none';
            montoRecibidoInput.value = '';
            modalCambio.textContent = formatearMoneda(0);
            if (btnConfirmarVenta) {
             btnConfirmarVenta.disabled = false;
             btnConfirmarVenta.textContent = 'Confirmar Venta';
            }
            modalPago.style.display = 'flex';
        });
    }

    metodoPagoRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.value === 'efectivo') {
                    paso1Cobro.style.display = 'block'; // Muestra campos de efectivo
                    // Si ya estábamos en el resumen, volvemos al paso 1
                    if(paso2Resumen.style.display === 'block'){
                        paso2Resumen.style.display = 'none';
                    }
                } else { // Tarjeta
                    paso1Cobro.style.display = 'none'; // Oculta campos de efectivo
                    // Si es tarjeta, podemos ir directo al resumen
                    mostrarResumen('tarjeta'); // Llama a la función de resumen
                }
            });
        });

    if (cerrarModalBtn) {
        cerrarModalBtn.addEventListener('click', () => modalPago.style.display = 'none');
    }
    if (modalPago) {
        modalPago.addEventListener('click', (e) => { if (e.target === modalPago) modalPago.style.display = 'none'; });
    }
    if (montoRecibidoInput) {
        montoRecibidoInput.addEventListener('input', () => calcularCambio(carrito, montoRecibidoInput, modalCambio));
    }
    if (btnCalcularCambio) {
        btnCalcularCambio.addEventListener('click', () => {
            const total = carrito.reduce((sum, item) => sum + item.precio * item.cantidad, 0);
            const recibido = parseFloat(montoRecibidoInput.value) || 0;
            if (recibido < total) {
                alert('El monto recibido es menor al total a pagar.');
                return;
            }
            mostrarResumen('efectivo');
        });
    }
    if (btnVolverCobro) {
        btnVolverCobro.addEventListener('click', () => {
// Revisa cuál radio está seleccionado actualmente
            const metodoSeleccionado = document.querySelector('input[name="metodo_pago"]:checked').value;
            if (metodoSeleccionado === 'efectivo') {
                 // Si era efectivo, regresa al paso 1
                paso1Cobro.style.display = 'block';
                paso2Resumen.style.display = 'none';
            } else {
                 // Si era tarjeta y quiere volver, cierra el modal
                modalPago.style.display = 'none'; 
            }
        });
    }

    // --- Lógica para Finalizar Venta ---
    if (btnConfirmarVenta) {
        btnConfirmarVenta.addEventListener('click', async () => {
            console.log("Iniciando finalización de venta..."); // LOG 1
            const metodoPago = document.querySelector('input[name="metodo_pago"]:checked').value;
            const totalVenta = carrito.reduce((sum, item) => sum + item.precio * item.cantidad, 0);
            let montoRecibido = parseFloat(montoRecibidoInput.value) || 0;
            let cambioDevuelto = Math.max(0, montoRecibido - totalVenta);
            const selectedCajaId = cajaSelector.value;
            if (metodoPago === 'efectivo') {
                            montoRecibido = parseFloat(montoRecibidoInput.value) || 0;
                            // Asegura que el cambio no sea negativo
                            cambioDevuelto = Math.max(0, montoRecibido - totalVenta); 
                        } else { // Tarjeta
                            montoRecibido = totalVenta; 
                            cambioDevuelto = 0;
                        }
                        if (!selectedCajaId) {
                            alert('Error: No se ha seleccionado una caja.');
                            return;
                        }

            const ventaData = {
                carrito: carrito.map(item => ({ id: item.id, cantidad: item.cantidad, precio: item.precio, nombre: item.nombre })),
                monto_recibido: montoRecibido,
                cambio_devuelto: cambioDevuelto,
                caja_id: selectedCajaId,
                metodo_pago: metodoPago
            };
console.log("Datos a enviar:", ventaData); // LOG 2

            // Deshabilitar botón
            btnConfirmarVenta.disabled = true;
            btnConfirmarVenta.textContent = 'Registrando...';
            let fueExitoso = false; // Variable para controlar si rehabilitar el botón

            try {
                console.log("Enviando fetch a /api/finalizar_venta..."); // LOG 3
                const response = await fetch('/api/finalizar_venta', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(ventaData)
                });
                console.log("Respuesta fetch recibida. Status:", response.status, "OK:", response.ok); // LOG 4

                // Intenta obtener el JSON SIEMPRE para ver si hay un error en el cuerpo
                let result = {};
                try {
                    result = await response.json();
                    console.log("Respuesta JSON:", result); // LOG 5
                } catch (jsonError) {
                     console.error("Error al parsear JSON:", jsonError); // LOG si falla el JSON
                     try {
                         // Intenta obtener el texto plano si el JSON falla
                         const textResponse = await response.text();
                         console.error("Respuesta como texto:", textResponse);
                         // Lanza un error más descriptivo
                         throw new Error(`La respuesta del servidor no es JSON válido. Contenido: ${textResponse}`); 
                     } catch (textError) {
                          throw new Error("La respuesta del servidor no es JSON válido y tampoco se pudo leer como texto.");
                     }
                }

                alert(result.message || "Operación procesada."); // Muestra mensaje del backend o uno genérico

                if (response.ok) { // Si el status es 2xx
                    fueExitoso = true; // Marca como exitoso
                    console.log("Venta exitosa. Limpiando interfaz..."); // LOG 6
                    carrito = []; // Limpia el carrito local
                    renderizarCarrito(carrito, listaCarritoDiv, carritoTotalMonto, btnProcederPago, cajaSelector); // Actualiza la vista del carrito
                    modalPago.style.display = 'none'; // Cierra el modal
                    cargarProductos(); // Vuelve a cargar los productos (actualiza stock)
                } else {
                    // Si el status es 4xx o 5xx
                    console.log("La respuesta del servidor indica un error (no OK)."); // LOG 7
                    // Lanza un error para que sea capturado por el bloque catch
                     throw new Error(result.message || `Error del servidor: ${response.status}`); 
                }
            } catch (error) {
                console.error('Error durante el fetch o procesamiento:', error); // LOG 8 (Error de red o lanzado arriba)
                alert('Error al registrar la venta: ' + error.message);
                // No es necesario rehabilitar aquí, lo hace el finally
            } finally {
                 // Este bloque SIEMPRE se ejecuta
                 if (!fueExitoso) { // Solo rehabilita si NO fue exitoso
                     btnConfirmarVenta.disabled = false;
                     btnConfirmarVenta.textContent = 'Confirmar Venta';
                     console.log("Botón Confirmar Venta rehabilitado debido a error."); // LOG 9
                 }
                 // Si fue exitoso, el botón queda deshabilitado y con texto "Registrando...", 
                 // lo cual está bien porque la interfaz se limpia/recarga.
            }
        });
    }

    // --- Carga Inicial ---
    cargarProductos();
    renderizarCarrito(carrito, listaCarritoDiv, carritoTotalMonto, btnProcederPago, cajaSelector);
});