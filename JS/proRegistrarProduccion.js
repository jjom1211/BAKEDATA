
let productosSeleccionados = {};

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
            window.location.href = '/produccionDeHoy';
        } else {
            alert(`❌ Error al registrar producción: ${data.message || 'Error desconocido del servidor.'}`);
        }
    } catch (err) {
        console.error("Error de conexión al registrar producción:", err);
        alert("❌ Error de conexión con el servidor. Revisa tu consola.");
    }
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

function actualizarListaProductos() {
    const container = document.getElementById("seleccionadasContainerProducto");
    container.style.display = "block";
}