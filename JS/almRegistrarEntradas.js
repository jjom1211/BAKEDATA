let listaManual = [];
let searchTimeout = null;

// --- GESTIÓN DE PESTAÑAS ---
function cambiarTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(div => div.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    
    const seccion = document.getElementById(`seccion-${tabName}`);
    if (seccion) seccion.classList.add('active');
    
    const idx = tabName === 'pedidos' ? 0 : 1;
    const btns = document.querySelectorAll('.tab-btn');
    if(btns[idx]) btns[idx].classList.add('active');
}

document.addEventListener('DOMContentLoaded', () => {
    // ==========================================
    // LÓGICA SECCIÓN 1: RECEPCIÓN DE PEDIDOS
    // ==========================================
    const tablaBody = document.getElementById('pedidos-tbody');
    const modal = document.getElementById('modal-recepcion');
    const detallesBody = document.getElementById('detalles-tbody');
    const btnConfirmar = document.getElementById('btn-confirmar-recepcion');
    let pedidoActualId = null;

    const cargarPedidos = async () => {
        try {
            const res = await fetch('/api/pedidos_por_recibir');
            const data = await res.json();
            
            if (tablaBody) {
                tablaBody.innerHTML = '';
                if (!data.length) {
                    tablaBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px;">Sin pedidos pendientes.</td></tr>';
                    return;
                }
                data.forEach(p => {
                    const row = `<tr>
                        <td><strong>#${p.ped_id}</strong></td>
                        <td style="color:#2a9d8f; font-weight:bold;">${p.fecha_formateada}</td>
                        <td>${p.origen}</td>
                        <td>${p.ped_asunto}</td>
                        <td><button class="btn-ver-detalles" data-id="${p.ped_id}">Recepcionar</button></td>
                    </tr>`;
                    tablaBody.insertAdjacentHTML('beforeend', row);
                });
            }
        } catch (e) { console.error(e); }
    };

    // Eventos Tabla Pedidos
    if (tablaBody) {
        tablaBody.addEventListener('click', async (e) => {
            if (e.target.classList.contains('btn-ver-detalles')) {
                pedidoActualId = e.target.dataset.id;
                const modalIdSpan = document.getElementById('modal-pedido-id');
                if(modalIdSpan) modalIdSpan.textContent = pedidoActualId;
                
                if(detallesBody) detallesBody.innerHTML = '<tr><td colspan="4">Cargando...</td></tr>';
                if(modal) modal.style.display = 'flex';
                
                try {
                    const res = await fetch(`/api/obtener_detalles_pedido/${pedidoActualId}`);
                    const items = await res.json();
                    if(detallesBody) {
                        detallesBody.innerHTML = '';
                        items.forEach(item => {
                            const row = `<tr data-id="${item.id}" data-tipo="${item.tipo}" data-esperado="${item.cantidad_esperada}">
                                <td>${item.nombre} <small style="color:#777">(${item.tipo})</small></td>
                                <td class="cant-esperada">${item.cantidad_esperada}</td>
                                <td><input type="number" class="input-recibido" value="${item.cantidad_esperada}" min="0" step="0.5"></td>
                                <td>${item.unidad}</td>
                            </tr>`;
                            detallesBody.insertAdjacentHTML('beforeend', row);
                        });
                    }
                } catch (err) {
                    if(detallesBody) detallesBody.innerHTML = '<tr><td colspan="4">Error al cargar detalles</td></tr>';
                }
            }
        });
    }

    // Confirmar Recepción
    if (btnConfirmar) {
        btnConfirmar.addEventListener('click', async () => {
            const filas = detallesBody.querySelectorAll('tr');
            const itemsEnviar = [];
            let hayFaltante = false;
            let hayExcedente = false;
            let msgExcedente = "";

            filas.forEach(tr => {
                const inp = tr.querySelector('.input-recibido');
                const esp = parseFloat(tr.dataset.esperado);
                const rec = parseFloat(inp.value) || 0;
                const nom = tr.cells[0].textContent;

                if (rec < esp) hayFaltante = true;
                if (rec > esp) {
                    hayExcedente = true;
                    msgExcedente += `- ${nom}: Esperado ${esp}, Recibido ${rec}\n`;
                }
                itemsEnviar.push({ id: tr.dataset.id, tipo: tr.dataset.tipo, cantidad_esperada: esp, cantidad_recibida: rec });
            });

            let accion = 'CERRAR';
            if (hayExcedente && !confirm(`⚠️ EXCEDENTE DETECTADO:\n${msgExcedente}\n¿Ingresar cantidades extra al inventario?`)) return;
            
            if (hayFaltante) {
                const opcion = confirm("⚠️ FALTANTES:\n\n[Aceptar] = Generar NUEVO PEDIDO con lo faltante (Backorder).\n[Cancelar] = Cerrar pedido así (Se pierde lo faltante).");
                accion = opcion ? 'BACKORDER' : 'CERRAR';
                if (!opcion && !confirm("¿Seguro? Lo que no llegó se marcará como perdido.")) return;
            } else if (!hayExcedente && !confirm("¿Confirmar recepción exacta?")) return;

            btnConfirmar.disabled = true;
            btnConfirmar.textContent = "Procesando...";

            try {
                const res = await fetch('/api/confirmar_recepcion', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ pedido_id: pedidoActualId, items: itemsEnviar, accion_faltante: accion })
                });
                const r = await res.json();
                alert(r.message);
                if (r.success) {
                    modal.style.display = 'none';
                    cargarPedidos();
                }
            } catch (e) { alert("Error de conexión"); }
            finally { 
                btnConfirmar.disabled = false; 
                btnConfirmar.textContent = "Confirmar Entrada";
            }
        });
    }

    // Cerrar Modales
    const btnCerrar = document.getElementById('cerrar-modal');
    if(btnCerrar) btnCerrar.onclick = () => modal.style.display = 'none';
    const btnCancelar = document.getElementById('btn-cancelar-modal');
    if(btnCancelar) btnCancelar.onclick = () => modal.style.display = 'none';

    cargarPedidos();


    // ==========================================
    // LÓGICA SECCIÓN 2: ENTRADA MANUAL
    // ==========================================
    const searchInput = document.getElementById('search-input');
    const resultsBox = document.getElementById('search-results');

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const q = this.value.trim();
            clearTimeout(searchTimeout);
            
            if (q.length < 1) { 
                if(resultsBox) resultsBox.style.display = 'none'; 
                return; 
            }

            searchTimeout = setTimeout(async () => {
                try {
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

// --- FUNCIONES AUXILIARES MANUAL ---

function renderResultadosBusqueda(items) {
    const box = document.getElementById('search-results');
    if (!box) return;

    box.innerHTML = '';
    if (items.length === 0) {
        box.innerHTML = '<div class="no-results">Sin resultados</div>';
        box.style.display = 'block';
        return;
    }

    items.forEach(p => {
        const div = document.createElement('div');
        div.className = 'search-result-item';
        const badge = p.tipo === 'materia' 
            ? '<span style="color:#e67e22; font-weight:bold;">[MP]</span>' 
            : '<span style="color:#2ecc71; font-weight:bold;">[P]</span>';
            
        div.innerHTML = `
            <span class="res-name">${badge} ${p.nombre}</span>
            <span class="res-info">ID: ${p.id} | ${p.unidad}</span>
        `;
        div.onclick = () => seleccionarProducto(p);
        box.appendChild(div);
    });
    box.style.display = 'block';
}

function seleccionarProducto(item) {
    document.getElementById('search-input').value = item.nombre;
    const hiddenInput = document.getElementById('selected-prod-id');
    hiddenInput.value = item.id;
    hiddenInput.dataset.tipo = item.tipo;
    hiddenInput.dataset.unidad = item.unidad;
    hiddenInput.dataset.nombre = item.nombre;
    
    const resultsBox = document.getElementById('search-results');
    if(resultsBox) resultsBox.style.display = 'none';
    document.getElementById('manual-cantidad').focus();
}

function agregarItemManual() {
    const hiddenInput = document.getElementById('selected-prod-id');
    const id = hiddenInput.value;
    const tipo = hiddenInput.dataset.tipo;
    const nombre = hiddenInput.dataset.nombre;
    const unidad = hiddenInput.dataset.unidad;
    const cant = document.getElementById('manual-cantidad').value;

    if (!id || !cant || parseFloat(cant) <= 0) {
        alert("Por favor busca un producto válido e ingresa una cantidad.");
        return;
    }

    listaManual.push({ id: id, tipo: tipo, nombre: nombre, cantidad: cant, unidad: unidad });
    renderManual();
    
    // Limpiar
    document.getElementById('search-input').value = '';
    hiddenInput.value = '';
    document.getElementById('manual-cantidad').value = '';
    document.getElementById('search-input').focus();
}

function renderManual() {
    const tb = document.getElementById('manual-tbody');
    const msg = document.getElementById('empty-msg');
    
    if (tb) tb.innerHTML = '';
    
    if (listaManual.length === 0) {
        // CORRECCIÓN DE SEGURIDAD: Verificar si msg existe
        if (msg) msg.style.display = 'block';
    } else {
        if (msg) msg.style.display = 'none';
        
        listaManual.forEach((item, idx) => {
            const labelTipo = item.tipo === 'materia' ? '(MP)' : '(P)';
            if (tb) {
                tb.insertAdjacentHTML('beforeend', `
                    <tr>
                        <td>${item.id}</td>
                        <td><strong>${item.nombre}</strong> <small>${labelTipo}</small></td>
                        <td>${item.cantidad}</td>
                        <td>${item.unidad}</td>
                        <td>
                            <button class="btn-delete-row" onclick="eliminarItemManual(${idx})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>`);
            }
        });
    }
}

function eliminarItemManual(index) {
    listaManual.splice(index, 1);
    renderManual();
}

async function confirmarEntradaManual() {
    if (!listaManual.length) return alert("La lista está vacía");
    const mot = document.getElementById('manual-motivo').value;
    
    if (!confirm(`¿Registrar entrada de ${listaManual.length} ítems?\nMotivo: ${mot}`)) return;
    
    try {
        const res = await fetch('/api/registrar_entrada_manual', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ items: listaManual, motivo: mot })
        });
        const r = await res.json();
        if (r.success) {
            alert("✅ Entrada registrada");
            listaManual = [];
            renderManual();
        } else {
            alert("Error: " + r.message);
        }
    } catch (e) { alert("Error de conexión"); }
}