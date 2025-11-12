let productosSeleccionados = {};
let materiasSeleccionadas = {};
function verMateriaPrima() {
    window.location.href = "/materias_primas.html";
}
function solicitarMateriaPrima() {
    window.location.href = "/solicitarMateriaPrima.html";
}
function irARegistrarProduccion() {
    window.location.href = "/registrar-produccion.html";
}
async function enviarRegistroProduccion() {
    const seleccionados = Object.values(productosSeleccionados);
    if (seleccionados.length === 0) {
        alert("No has seleccionado ningún producto para registrar.");
        return;
    }
    const productosParaDB = seleccionados.map(prod => ({
        pro_dia_nombre: prod.nombre,
        pro_dia_cantidad: parseFloat(prod.cantidad),
        pro_dia_estado: 'P'
    }));
    try {
        const response = await fetch("/api/registrar_produccion", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(productosParaDB)
        });
        const data = await response.json();
        if (response.ok && data.success) {
            alert("✅ Producción registrada exitosamente.");
            productosSeleccionados = {};
            window.location.href = '/produccion-hoy.html';
        } else {
            alert(`❌ Error al registrar producción: ${data.message || 'Error desconocido del servidor.'}`);
        }
    } catch (err) {
        console.error("Error de conexión al registrar producción:", err);
        alert("❌ Error de conexión con el servidor. Revisa tu consola.");
    }
}
async function buscarMaterias() {
    const sugerenciasUl = document.getElementById('sugerencias');
    const contenedor = document.getElementById('contenedor-sugerencias-MatPri');
    const query = document.getElementById('buscador').value;
    sugerenciasUl.innerHTML = "";
    contenedor.style.display = "block";
    if (query.trim() === "") return;
    try {
        const response = await fetch(`/buscar_materias?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        if (data.length === 0) {
            sugerenciasUl.innerHTML = "<div style='padding: 10px;'>No se encontraron productos.</div>";
        } else {
            data.forEach(materia => {
                const div = document.createElement("div");
                div.textContent = `${materia.nombre} (${materia.unidad}) - ${materia.descripcion || ''}`;
                const encoded = encodeURIComponent(JSON.stringify(materia));
                div.onclick = () => agregarMateriaASeleccionados(encoded);
                sugerenciasUl.appendChild(div);
            });
        }
    } catch (err) {
        console.error("Error al buscar productos:", err);
        contenedor.style.display = "none";
    }
}
function agregarMateriaASeleccionados(encodedData) {
    const materia = JSON.parse(decodeURIComponent(encodedData));
    const id = materia.id.toString();
    const lista = document.getElementById("listaSeleccionadas");
    if (materiasSeleccionadas[id]) {
        alert(`La materia "${materia.nombre}" ya está en la lista.`);
        return;
    }
    materiasSeleccionadas[id] = {
        nombre: materia.nombre,
        unidad: materia.unidad,
        cantidad: "1"
    };

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
    agregarListenersAProducto(id);
    actualizarListaProductos();
}

async function buscarProductos() {
    const sugerenciasUl = document.getElementById('sugerenciasProducto');
    const contenedor = document.getElementById('contenedor-sugerencias-producto');
    const query = document.getElementById('buscador').value;
    sugerenciasUl.innerHTML = "";
    contenedor.style.display = "block";
    if (query.trim() === "") return;
    try {
        const response = await fetch(`/buscar_productos?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        if (data.length === 0) {
            sugerenciasUl.innerHTML = "<div style='padding: 10px;'>No se encontraron productos.</div>";
        } else {
            data.forEach(producto => {
                const div = document.createElement("div");
                div.textContent = `${producto.nombre} (${producto.unidad}) - ${producto.descripcion || ''}`;
                const encoded = encodeURIComponent(JSON.stringify(producto));
                div.onclick = () => agregarProductoASeleccionados(encoded);
                sugerenciasUl.appendChild(div);
            });
        }
    } catch (err) {
        console.error("Error al buscar productos:", err);
        contenedor.style.display = "none";
    }
}
function agregarProductoASeleccionados(encodedData) {
    const producto = JSON.parse(decodeURIComponent(encodedData));
    const id = producto.id.toString();
    const lista = document.getElementById("listaSeleccionadas");
    if (productosSeleccionados[id]) {
        alert(`El producto "${producto.nombre}" ya está en la lista.`);
        return;
    }
    productosSeleccionados[id] = {
        nombre: producto.nombre,
        unidad: producto.unidad,
        cantidad: "1"
    };

    const li = document.createElement("li");
    li.id = `item-prod-${id}`;
    li.innerHTML = `
    <div class="confirm-header">
        <input type="checkbox" class="check-prod" id="check-prod-${id}" checked
            data-id="${id}" data-nombre="${producto.nombre}" data-unidad="${producto.unidad}">
            <strong>${producto.nombre} (${producto.unidad})</strong>
    </div>
    <div class="confirm-quantity">
        <label>Charolas:</label>
            <input type="number" id="cantidad-prod-${id}" min="1" value="1">
    </div>
                    `;
    lista.appendChild(li);
    agregarListenersAProducto(id);
    actualizarListaProductos();
}

function agregarListenersAProducto(id) {
    const check = document.getElementById(`check-prod-${id}`);
    const cantidadInput = document.getElementById(`cantidad-prod-${id}`);
    check.addEventListener('change', () => {
        if (check.checked) {
            productosSeleccionados[id].cantidad = cantidadInput.value;
            cantidadInput.disabled = false;
        } else {
            delete productosSeleccionados[id];
            cantidadInput.disabled = true;
        }
        actualizarListaProductos();
    });
    cantidadInput.addEventListener('input', () => {
        if (check.checked) {
            let val = cantidadInput.value || "1";
            if (parseFloat(val) < 1) val = "1";
            cantidadInput.value = val;
            productosSeleccionados[id].cantidad = val;
        }
    });
}
function actualizarListaProductos() {
    const container = document.getElementById("seleccionadasContainerProducto");
    container.style.display = "block";
}
