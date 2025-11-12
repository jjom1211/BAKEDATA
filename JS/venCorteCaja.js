// Archivo: JS/venCorteCaja.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Selección de Elementos ---
    const cajaSelector = document.getElementById('caja_selector');
    const tipoCorteContainer = document.getElementById('tipo-corte-container');
    const corteTurnoContainer = document.getElementById('corte-turno-container');
    const corteDiaContainer = document.getElementById('corte-dia-container');
    const tipoCorteRadios = document.querySelectorAll('input[name="tipo_corte"]');

    // Elementos de Corte de Turno
    const formTurno = document.getElementById('form-corte-turno');
    const efectivoDisplayTurno = corteTurnoContainer.querySelector('.efectivo-actual');
    const cajaIdHiddenTurno = document.getElementById('caja_id_hidden_turno');
    const totalRetirarSpan = document.getElementById('total-retirar');
    const denominacionInputs = formTurno.querySelectorAll('.denominaciones input[type="number"]');
    let efectivoActualTurno = 0;

    // Elementos de Corte de Día
    const formDia = document.getElementById('form-corte-dia');
    const cajaIdHiddenDia = document.getElementById('caja_id_hidden_dia');
    const resumenEfectivo = document.getElementById('resumen-efectivo');
    const resumenTarjeta = document.getElementById('resumen-tarjeta');
    const resumenRetirosAjuste = document.getElementById('resumen-retiros-ajuste');
    const resumenCortesTurno = document.getElementById('resumen-cortes-turno');
    const resumenTotalDia = document.getElementById('resumen-total-dia');
    const resumenTotalAcumulado = document.getElementById('resumen-total-acumulado');

    /**
     * Formatea un número como moneda mexicana (MXN).
     */
    const formatearMoneda = (valor) => {
        let numValor = parseFloat(valor);
        if (isNaN(numValor)) { numValor = 0; }
        return numValor.toLocaleString('es-MX', { style: 'currency', currency: 'MXN' });
    };

    /**
     * Lógica de Carga de Saldo (para Corte de Turno)
     */
    const cargarSaldoCaja = async (cajaId) => {
        efectivoDisplayTurno.textContent = 'Cargando...';
        try {
            const response = await fetch(`/api/caja_detalle/${cajaId}`);
            if (!response.ok) throw new Error('No se pudo cargar el saldo.');
            const data = await response.json();
            efectivoActualTurno = data.caja_efectivo;
            efectivoDisplayTurno.textContent = formatearMoneda(efectivoActualTurno);
            cajaIdHiddenTurno.value = cajaId;
        } catch (error) {
            alert(error.message);
            efectivoDisplayTurno.textContent = '$--.--';
            efectivoActualTurno = 0;
        }
    };

    /**
     * Lógica de Carga de Resumen (para Corte de Día)
     */
    const cargarResumenDia = async (cajaId) => {
        resumenEfectivo.textContent = 'Cargando...';
        resumenTarjeta.textContent = 'Cargando...';
        resumenRetirosAjuste.textContent = 'Cargando...';
        resumenCortesTurno.textContent = 'Cargando...';
        resumenTotalDia.textContent = 'Cargando...';
        resumenTotalAcumulado.textContent = 'Cargando...'; // NUEVO
        
        try {
            const response = await fetch(`/api/resumen_caja_dia/${cajaId}`);
            if (!response.ok) throw new Error('No se pudo cargar el resumen.');
            const data = await response.json();
            
            resumenEfectivo.textContent = formatearMoneda(data.caja_efectivo);
            resumenTarjeta.textContent = formatearMoneda(data.caja_tarjeta);
            resumenTotalDia.textContent = formatearMoneda(data.caja_total_dia);
            resumenRetirosAjuste.textContent = formatearMoneda(data.total_retiros_ajuste);
            resumenCortesTurno.textContent = formatearMoneda(data.total_retiros_corte_turno);
            resumenTotalAcumulado.textContent = formatearMoneda(data.total_acumulado_dia); // NUEVO
            cajaIdHiddenDia.value = cajaId;
        } catch (error) {
            alert(error.message);
            // resetear textos a $0.00
            resumenEfectivo.textContent = '$0.00';
            resumenTarjeta.textContent = '$0.00';
            resumenRetirosAjuste.textContent = '$0.00';
            resumenCortesTurno.textContent = '$0.00';
            resumenTotalDia.textContent = '$0.00';
            resumenTotalAcumulado.textContent = '$0.00'; // NUEVO
        }
    };
    
    /**
     * Lógica de Selección de Caja
     */
    cajaSelector.addEventListener('change', () => {
        const cajaId = cajaSelector.value;
        if (!cajaId) {
            tipoCorteContainer.style.display = 'none';
            corteTurnoContainer.style.display = 'none';
            corteDiaContainer.style.display = 'none';
            tipoCorteRadios.forEach(radio => radio.checked = false);
            return;
        }
        tipoCorteContainer.style.display = 'block';
        corteTurnoContainer.style.display = 'none';
        corteDiaContainer.style.display = 'none';
        tipoCorteRadios.forEach(radio => radio.checked = false);
    });

    /**
     * Lógica de Selección de Tipo de Corte
     */
    tipoCorteRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const tipo = e.target.value;
            const cajaId = cajaSelector.value;
            if (tipo === 'turno') {
                cargarSaldoCaja(cajaId);
                corteTurnoContainer.style.display = 'block';
                corteDiaContainer.style.display = 'none';
            } else if (tipo === 'dia') {
                cargarResumenDia(cajaId);
                corteTurnoContainer.style.display = 'none';
                corteDiaContainer.style.display = 'block';
            }
        });
    });

    /**
     * Lógica de Calcular Total (Corte de Turno)
     */
    const calcularTotal = () => {
        let total = 0;
        denominacionInputs.forEach(input => {
            const valor = parseFloat(input.id.replace(/[bm]/, ''));
            const cantidad = parseInt(input.value) || 0;
            if (!isNaN(valor) && cantidad >= 0) {
                total += valor * cantidad;
            } else {
                input.value = 0;
            }
        });
        totalRetirarSpan.textContent = formatearMoneda(total);
        return total;
    };
    denominacionInputs.forEach(input => input.addEventListener('input', calcularTotal));
    calcularTotal(); // Llama al inicio para poner $0.00

    /**
     * Lógica de Envío de Formulario (Corte de Turno)
     */
    formTurno.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(formTurno);
        const totalRetirar = calcularTotal();
        
        if (totalRetirar <= 0) {
            alert('El total a retirar debe ser mayor a cero.');
            return;
        }
        if (totalRetirar > efectivoActualTurno) {
            alert(`Error: No se puede retirar ${formatearMoneda(totalRetirar)}. El efectivo actual es ${formatearMoneda(efectivoActualTurno)}.`);
            return;
        }
        if (!confirm(`Se retirarán ${formatearMoneda(totalRetirar)}. ¿Continuar?`)) return;
        
        const submitButton = formTurno.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        
        try {
            const response = await fetch(formTurno.dataset.action, { method: 'POST', body: formData });
            const data = await response.json();
            alert(data.message);
            if (response.ok) window.history.back();
            else submitButton.disabled = false;
        } catch (error) {
            alert('Error de comunicación.');
            submitButton.disabled = false;
        }
    });

    /**
     * Lógica de Envío de Formulario (Corte de Día)
     */
    formDia.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (!confirm("¿Estás seguro de que deseas realizar el CIERRE FINAL del día? Esta acción reseteará la caja a cero.")) return;

        const submitButton = formDia.querySelector('button[type="submit"]');
        const formData = new FormData(formDia);
        submitButton.disabled = true;

        try {
            const response = await fetch(formDia.dataset.action, { method: 'POST', body: formData });
            const data = await response.json();
            alert(data.message);
            if (response.ok) window.history.back();
            else submitButton.disabled = false;
        } catch (error) {
            alert('Error de comunicación.');
            submitButton.disabled = false;
        }
    });
});