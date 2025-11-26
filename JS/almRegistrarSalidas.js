let listaManual = [];
let searchTimeout = null;

function cambiarTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(div => div.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    
    document.getElementById(`seccion-${tabName}`).classList.add('active');
    const idx = tabName === 'surtir' ? 0 : 1;
    document.querySelectorAll('.tab-btn')[idx].classList.add('active');
}

document.addEventListener('DOMContentLoaded', () => {
    // --- SECCIÓN 1: PEDIDOS POR SURTIR ---
    const tbodyPedidos = document.getElementById('tbody-pedidos-surtir');

    const cargarPedidosPorSurtir = async () => {
        try {
            const res = await fetch('/api/pedidos_por_surtir');
            const data = await res.json();
            if (!tbodyPedidos) return;
            tbodyPedidos.innerHTML = '';
            
            if (data.length === 0) {
                tbodyPedidos.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px;">No hay pedidos pendientes por surtir.</td></tr>';
                return;
            }

            data.forEach(p => {
                const row = `<tr>
                    <td><strong>#${p.ped_id}</strong></td>
                    <td>${p.destino}</td>
                    <td>${p.ped_asunto}</td>
                    <td style="color:#2a9d8f; font-weight:bold;">${p.ped_fecha_entrega || '-'}</td>
                    <td><button class="btn-surtir" data-id="${p.ped_id}">Surtir</button></td>
                </tr>`;
                tbodyPedidos.insertAdjacentHTML('beforeend', row);
            });
        } catch (e) { 
            console.error(e);
            if(tbodyPedidos) tbodyPedidos.innerHTML = '<tr><td colspan="5" style="color:red;">Error al cargar.</td></tr>';
        }
    };

    if(tbodyPedidos) {
        tbodyPedidos.addEventListener('click', async (e) => {
            if (e.target.classList.contains('btn-surtir')) {
                const id = e.target.dataset.id;
                if (!confirm(`¿Confirmar salida de inventario para el Pedido #${id}?`)) return;

                e.target.disabled = true;
                e.target.textContent = "Procesando...";

                try {
                    const res = await fetch('/api/surtir_pedido', {
                        method: 'POST', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ pedido_id: id })
                    });
                    const r = await res.json();
                    alert(r.message);
                    if (r.success) cargarPedidosPorSurtir();
                    else { e.target.disabled = false; e.target.textContent = "Surtir"; }
                } catch (err) {
                    alert("Error de conexión");
                    e.target.disabled = false;
                }
            }
        });
    }

    cargarPedidosPorSurtir();

    // --- SECCIÓN 2: SALIDA MANUAL (BUSCADOR) ---
    const searchInput = document.getElementById('search-input');
    const resultsBox = document.getElementById('search-results');

    if(searchInput) {
        searchInput.addEventListener('input', function() {
            const q = this.value.trim();
            clearTimeout(searchTimeout);
            if (q.length < 1) { 
                if(resultsBox) resultsBox.style.display = 'none'; 
                return; 
            }

            searchTimeout = setTimeout(async () => {
                try {
                    // Usamos la MISMA API de búsqueda que en Entradas (reutilización)
                    const res = await fetch(`/api/buscar_productos?q=${q}`);
                    const items = await res.json();
                    renderResultadosBusqueda(items);
                } catch (e) { console.error(e); }
            }, 300);
        });
    }

    document.addEventListener('click', (e) => {
        if (resultsBox && !e.target.closest('.search-wrapper')) resultsBox.style.display = 'none';
    });
});

// Funciones Manuales
function renderResultadosBusqueda(items) {
    const box = document.getElementById('search-results');
    if(!box) return;
    box.innerHTML = '';
    
    if (!items.length) { 
        box.innerHTML = '<div class="no-results">Sin resultados</div>'; 
        box.style.display = 'block'; 
        return; 
    }

    items.forEach(p => {
        const div = document.createElement('div');
        div.className = 'search-result-item';
        const badge = p.tipo === 'materia' ? '<span style="color:#e67e22">[MP]</span>' : '<span style="color:#2ecc71">[P]</span>';
        div.innerHTML = `<span class="res-name">${badge} ${p.nombre}</span><span class="res-info">ID: ${p.id} | ${p.unidad}</span>`;
        div.onclick = () => seleccionarItem(p);
        box.appendChild(div);
    });
    box.style.display = 'block';
}

function seleccionarItem(item) {
    document.getElementById('search-input').value = item.nombre;
    const hidden = document.getElementById('selected-item-id');
    hidden.value = item.id;
    hidden.dataset.tipo = item.tipo;
    hidden.dataset.unidad = item.unidad;
    hidden.dataset.nombre = item.nombre;
    
    const resultsBox = document.getElementById('search-results');
    if(resultsBox) resultsBox.style.display = 'none';
    document.getElementById('manual-cantidad').focus();
}

function agregarItemManual() {
    const hidden = document.getElementById('selected-item-id');
    const id = hidden.value;
    const cant = document.getElementById('manual-cantidad').value;

    if (!id || !cant || parseFloat(cant) <= 0) return alert("Selecciona un ítem válido y cantidad mayor a 0");

    listaManual.push({
        id: id,
        tipo: hidden.dataset.tipo,
        nombre: hidden.dataset.nombre,
        unidad: hidden.dataset.unidad,
        cantidad: cant
    });
    renderManual();
    
    document.getElementById('search-input').value = '';
    hidden.value = '';
    document.getElementById('manual-cantidad').value = '';
    document.getElementById('search-input').focus();
}

function renderManual() {
    const tb = document.getElementById('manual-tbody');
    const msg = document.getElementById('empty-msg');
    if(tb) tb.innerHTML = '';
    
    if (listaManual.length === 0) { 
        if(msg) msg.style.display = 'block'; 
    } else {
        if(msg) msg.style.display = 'none';
        listaManual.forEach((item, idx) => {
            const label = item.tipo === 'materia' ? '(MP)' : '(P)';
            if(tb) {
                tb.insertAdjacentHTML('beforeend', `
                    <tr>
                        <td><strong>${item.nombre}</strong> <small>${label}</small></td>
                        <td>${item.cantidad}</td>
                        <td>${item.unidad}</td>
                        <td><button class="btn-delete-row" onclick="listaManual.splice(${idx},1);renderManual()"><i class="fas fa-trash"></i></button></td>
                    </tr>`);
            }
        });
    }
}

async function confirmarSalidaManual() {
    if (!listaManual.length) return alert("Lista vacía");
    const mot = document.getElementById('manual-motivo').value;
    
    if (!confirm(`¿Registrar salida de ${listaManual.length} ítems por ${mot}?`)) return;

    try {
        const res = await fetch('/api/registrar_salida_manual', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ items: listaManual, motivo: mot })
        });
        const r = await res.json();
        if (r.success) {
            alert("✅ Salida registrada.");
            listaManual = [];
            renderManual();
        } else {
            alert("Error: " + r.message);
        }
    } catch (e) { alert("Error de conexión"); }
}