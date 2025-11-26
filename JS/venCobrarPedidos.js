let pedidosCargados = [];
let pedidoActual = null;

document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('grid-pedidos');
    const loading = document.getElementById('loading-msg');
    
    // Modal
    const modal = document.getElementById('modal-cobro');
    const montoInput = document.getElementById('monto-recibido');
    const cambioText = document.getElementById('cambio-text');
    const radios = document.querySelectorAll('input[name="metodo"]');
    const seccionEfectivo = document.getElementById('seccion-efectivo');
    const btnPagar = document.getElementById('btn-finalizar-cobro');

    // --- CARGAR PEDIDOS ---
    const cargarPedidos = async () => {
        try {
            const res = await fetch('/api/pedidos_por_cobrar');
            const data = await res.json();
            pedidosCargados = data;
            
            loading.style.display = 'none';
            grid.innerHTML = '';

            if (data.length === 0) {
                grid.innerHTML = '<div class="empty-state">No hay pedidos listos para cobro (Estado C).</div>';
                return;
            }

            data.forEach(p => {
                const card = document.createElement('div');
                // Estado C = Ready (Listo en tienda)
                card.className = 'pedido-card ready'; 
                
                // Etiqueta visual
                const estadoLabel = '<span class="badge badge-blue">Listo en Tienda</span>';

                card.innerHTML = `
                    <div class="card-header">
                        <span class="ped-id">#${p.ped_id}</span>
                        ${estadoLabel}
                    </div>
                    <div class="card-body">
                        <h4 class="cliente">${p.cliente_nombre}</h4>
                        <p class="asunto">${p.ped_asunto}</p>
                        <p class="fecha"><i class="far fa-calendar-alt"></i> Entrega: ${p.ped_fecha_entrega}</p>
                    </div>
                    <div class="card-footer">
                        <span class="monto">$${p.ped_monto_total.toFixed(2)}</span>
                        <button class="btn-cobrar" onclick="abrirModalCobro(${p.ped_id})">
                            <i class="fas fa-cash-register"></i> Cobrar
                        </button>
                    </div>
                `;
                grid.appendChild(card);
            });

        } catch (e) {
            console.error(e);
            loading.textContent = "Error al cargar pedidos.";
        }
    };

    // --- ABRIR MODAL ---
    window.abrirModalCobro = (id) => {
        pedidoActual = pedidosCargados.find(p => p.ped_id === id);
        if (!pedidoActual) return;

        document.getElementById('modal-ped-id').textContent = id;
        document.getElementById('modal-cliente').textContent = pedidoActual.cliente_nombre;
        document.getElementById('modal-total').textContent = `$${pedidoActual.ped_monto_total.toFixed(2)}`;
        
        // Reset Form
        montoInput.value = '';
        cambioText.textContent = '$0.00';
        radios[0].checked = true; // Efectivo por defecto
        seccionEfectivo.style.display = 'block';
        btnPagar.disabled = false;
        btnPagar.textContent = "Confirmar Pago y Entrega";
        
        modal.style.display = 'flex';
        setTimeout(() => montoInput.focus(), 100);
    };

    // --- EVENTOS MODAL ---
    
    radios.forEach(r => {
        r.addEventListener('change', (e) => {
            if(e.target.value === 'efectivo') seccionEfectivo.style.display = 'block';
            else seccionEfectivo.style.display = 'none';
        });
    });

    montoInput.addEventListener('input', () => {
        if (!pedidoActual) return;
        const recibido = parseFloat(montoInput.value) || 0;
        const total = pedidoActual.ped_monto_total;
        const cambio = recibido - total;
        
        if (cambio >= 0) {
            cambioText.textContent = `$${cambio.toFixed(2)}`;
            cambioText.style.color = '#28a745';
        } else {
            cambioText.textContent = "Faltante";
            cambioText.style.color = '#dc3545';
        }
    });

    btnPagar.addEventListener('click', async () => {
        const cajaId = document.getElementById('caja_activa').value;
        if (!cajaId) return alert("Error: No hay caja seleccionada.");

        const metodo = document.querySelector('input[name="metodo"]:checked').value;
        let montoRecibido = 0;

        if (metodo === 'efectivo') {
            montoRecibido = parseFloat(montoInput.value);
            if (!montoRecibido || montoRecibido < pedidoActual.ped_monto_total) {
                return alert("El monto recibido es insuficiente.");
            }
        } else {
            montoRecibido = pedidoActual.ped_monto_total;
        }

        if(!confirm(`¿Confirmar cobro de $${pedidoActual.ped_monto_total.toFixed(2)} y entregar producto?`)) return;

        btnPagar.disabled = true;
        btnPagar.textContent = "Procesando...";

        try {
            const res = await fetch('/api/procesar_cobro_pedido', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    pedido_id: pedidoActual.ped_id,
                    caja_id: cajaId,
                    metodo_pago: metodo,
                    monto_recibido: montoRecibido
                })
            });
            const data = await res.json();
            
            if (data.success) {
                alert("✅ " + data.message);
                modal.style.display = 'none';
                cargarPedidos(); // Refrescar lista
            } else {
                alert("Error: " + data.message);
                btnPagar.disabled = false;
                btnPagar.textContent = "Confirmar Pago";
            }
        } catch (e) {
            alert("Error de conexión");
            btnPagar.disabled = false;
        }
    });

    document.getElementById('cerrar-modal').onclick = () => modal.style.display = 'none';
    
    // Iniciar
    cargarPedidos();
});