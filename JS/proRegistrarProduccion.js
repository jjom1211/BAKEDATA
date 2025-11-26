// Variable global
let productosSeleccionados = {};

// --- GESTIÓN DE PESTAÑAS ---
function cambiarTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(div => div.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`seccion-${tabName}`).classList.add('active');
    
    const idx = tabName === 'manual' ? 0 : 1;
    document.querySelectorAll('.tab-btn')[idx].classList.add('active');

    if(tabName === 'pedidos') cargarPedidosPendientes();
}

// --- LÓGICA NUEVA: PEDIDOS PARA PRODUCCIÓN ---
async function cargarPedidosPendientes() {
    const tbody = document.getElementById('tbody-pedidos-produccion');
    // Cambio de mensaje: ya no dice "para hoy"
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center">Cargando todos los pedidos pendientes...</td></tr>';

    try {
        const res = await fetch('/api/pedidos_para_produccion');
        const data = await res.json();
        tbody.innerHTML = '';

        if(data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px;">No hay pedidos pendientes por surtir.</td></tr>';
            return;
        }

        data.forEach(p => {
            const row = `
                <tr>
                    <td><strong>#${p.ped_id}</strong></td>
                    <td>${p.origen}</td>
                    <td>${p.destino}</td>
                    <td>${p.ped_asunto}</td>
                    <td style="color:#2a9d8f; font-weight:bold;">${p.ped_fecha_entrega || 'Pendiente'} <small>${p.ped_hora_entrega || ''}</small></td>
                    <td>
                        <button class="btn-cargar-prod" onclick="cargarPedidoAProduccion(${p.ped_id})">
                            <i class="fas fa-plus-circle"></i> Cargar
                        </button>
                    </td>
                </tr>
            `;
            tbody.insertAdjacentHTML('beforeend', row);
        });
    } catch (e) { tbody.innerHTML = '<tr><td colspan="6" style="color:red">Error de conexión</td></tr>'; }
}

async function cargarPedidoAProduccion(idPedido) {
    if(!confirm(`¿Agregar los productos del Pedido #${idPedido} a la lista de producción?`)) return;

    try {
        const res = await fetch(`/api/items_pedido_produccion/${idPedido}`);
        const items = await res.json();

        if(items.length === 0) { alert("Este pedido no contiene productos."); return; }

        let count = 0;
        items.forEach(item => {
            const idStr = item.id.toString();
            if (productosSeleccionados[idStr]) {
                // Si ya existe, SUMAMOS la cantidad
                let actual = parseFloat(productosSeleccionados[idStr].cantidad);
                let nueva = actual + parseFloat(item.cantidad);
                productosSeleccionados[idStr].cantidad = nueva;
            } else {
                // Si no existe, lo creamos
                productosSeleccionados[idStr] = {
                    id: item.id,
                    nombre: item.nombre,
                    unidad: item.unidad,
                    cantidad: item.cantidad
                };
            }
            count++;
        });

        renderizarListaSeleccionados();
        alert(`${count} productos agregados a tu lista de producción.`);
        cambiarTab('manual'); // Regresamos a la lista principal

    } catch (e) { alert("Error al cargar detalles del pedido."); }
}

// --- RESTO DE LA LÓGICA (Buscador, Sugerencias, Enviar) ---
// (Se mantiene idéntica a la versión anterior, pero la incluyo completa para evitar errores)

async function buscarProductos() {
    const buscador = document.getElementById('buscador');
    const sugerenciasUl = document.getElementById('sugerenciasProducto');
    const contenedor = document.getElementById('contenedor-sugerencias-producto');
    const query = buscador.value.trim();
    sugerenciasUl.innerHTML = "";

    if (query === "") { contenedor.style.display = "none"; return; }
    contenedor.style.display = "block";

    try {
        const response = await fetch(`/api/buscar_productos?q=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data.length === 0) {
            sugerenciasUl.innerHTML = "<div style='padding: 10px;'>No se encontraron productos.</div>";
        } else {
            data.forEach(producto => {
                if(producto.tipo && producto.tipo !== 'producto') return; 
                const div = document.createElement("div");
                div.textContent = `${producto.nombre} (${producto.unidad})`;
                const encoded = encodeURIComponent(JSON.stringify(producto));
                div.onclick = () => agregarProductoASeleccionados(encoded);
                sugerenciasUl.appendChild(div);
            });
        }
    } catch (err) { console.error(err); contenedor.style.display = "none"; }
}

function agregarProductoASeleccionados(encodedData) {
    const producto = JSON.parse(decodeURIComponent(encodedData));
    const id = producto.id.toString();
    
    if (productosSeleccionados[id]) {
        alert(`El producto "${producto.nombre}" ya está en la lista.`);
    } else {
        productosSeleccionados[id] = {
            id: producto.id,
            nombre: producto.nombre,
            unidad: producto.unidad,
            cantidad: "1"
        };
        renderizarListaSeleccionados();
    }
    document.getElementById('buscador').value = '';
    document.getElementById('contenedor-sugerencias-producto').style.display = "none";
}

function renderizarListaSeleccionados() {
    const lista = document.getElementById("listaSeleccionadas");
    lista.innerHTML = "";
    const ids = Object.keys(productosSeleccionados);

    if (ids.length === 0) {
        lista.innerHTML = "<p style='text-align:center; color:#777;'>No hay productos seleccionados.</p>";
        return;
    }

    ids.forEach(id => {
        const item = productosSeleccionados[id];
        const li = document.createElement("li");
        li.id = `item-prod-${id}`;
        li.innerHTML = `
            <div class="confirm-header" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                <span><strong>${item.nombre}</strong> <small>(${item.unidad})</small></span>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <input type="number" id="cantidad-prod-${id}" min="0.01" step="0.01" value="${item.cantidad}" 
                           onchange="actualizarCantidad('${id}', this.value)" 
                           style="width: 70px; text-align: center; padding:5px; border-radius:4px; border:1px solid #ccc;">
                    <button onclick="eliminarProducto('${id}')" class="btn-delete-item"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `;
        lista.appendChild(li);
    });
    document.getElementById("seleccionadasContainerProducto").style.display = "block";
}

function actualizarCantidad(id, valor) {
    if (productosSeleccionados[id]) {
        if (parseFloat(valor) <= 0) {
            alert("La cantidad debe ser mayor a 0");
            document.getElementById(`cantidad-prod-${id}`).value = productosSeleccionados[id].cantidad;
            return;
        }
        productosSeleccionados[id].cantidad = valor;
    }
}

function eliminarProducto(id) {
    delete productosSeleccionados[id];
    renderizarListaSeleccionados();
}

async function cargarSugerenciasDelDia() {
    const btn = document.getElementById('btn-sugerencia-dia');
    btn.disabled = true;
    btn.textContent = "Cargando...";

    try {
        const response = await fetch('/api/sugerencias_produccion_dia');
        const sugerencias = await response.json();

        if (sugerencias.length === 0) {
            alert("No hay historial suficiente para sugerencias hoy.");
            return;
        }

        if (Object.keys(productosSeleccionados).length > 0) {
            if (!confirm("Se agregarán productos sugeridos a tu lista actual. ¿Seguir?")) return;
        }

        sugerencias.forEach(item => {
            const idStr = item.id.toString();
            if (!productosSeleccionados[idStr]) {
                productosSeleccionados[idStr] = {
                    id: item.id, nombre: item.nombre, unidad: item.unidad, cantidad: item.cantidad
                };
            }
        });
        renderizarListaSeleccionados();
        cambiarTab('manual');
    } catch (error) { alert("Error cargando sugerencias."); } 
    finally { btn.disabled = false; btn.textContent = "✨ Cargar Producción Sugerida (Histórico)"; }
}

async function enviarRegistroProduccion() {
    const seleccionados = Object.values(productosSeleccionados);
    if (seleccionados.length === 0) return alert("Lista vacía.");

    const productosParaDB = seleccionados.map(prod => ({
        id: prod.id,
        pro_dia_nombre: prod.nombre,
        pro_dia_cantidad: parseFloat(prod.cantidad)
    }));

    const selectorAdmin = document.getElementById('sucursal_admin_prod');
    let dataToSend = selectorAdmin 
        ? { sucursal_id: selectorAdmin.value, productos: productosParaDB }
        : productosParaDB;

    const btn = document.getElementById('botonEnviar');
    btn.disabled = true;
    btn.textContent = "Registrando...";

    try {
        const res = await fetch("/api/registrar_produccion", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dataToSend)
        });
        const data = await res.json();

        if (data.success) {
            alert(data.message);
            productosSeleccionados = {};
            renderizarListaSeleccionados();
        } else {
            alert("Error: " + data.message);
        }
    } catch (err) { alert("Error de conexión."); } 
    finally { btn.disabled = false; btn.textContent = "Confirmar y Registrar Producción"; }
}