function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    if (input) {
        input.type = (input.type === "password") ? "text" : "password";
    }
}
document.addEventListener('DOMContentLoaded', () => {
    const sucursalSelector = document.getElementById('sucursal_selector');
    const tablaBody = document.getElementById('empleados_tbody');
    // --- Referencias a Modales ---
    const modalEditar = document.getElementById('modal-editar-empleado');
    const modalPassword = document.getElementById('modal-password');
    const closeButtons = document.querySelectorAll('.modal-close');
    const cancelButtons = document.querySelectorAll('.modal-cancel-btn');
    // --- Referencias a Formularios de Modales ---
    const formEditar = document.getElementById('form-editar-empleado');
    const formPassword = document.getElementById('form-password');
    /**
     * Carga los empleados de la sucursal seleccionada
     */
    const cargarEmpleados = async () => {
        const sucursalId = sucursalSelector.value;
        if (!sucursalId) {
            tablaBody.innerHTML = '<tr><td colspan="5">Selecciona una sucursal para ver los empleados.</td></tr>';
            return;
        }
        tablaBody.innerHTML = '<tr><td colspan="5">Cargando...</td></tr>';

        try {
            const response = await fetch(`/api/empleados_por_sucursal/${sucursalId}`);
            const empleados = await response.json();

            if (!response.ok) {
                throw new Error(empleados.error || 'Error al cargar empleados.');
            }
            
            tablaBody.innerHTML = ''; // Limpia la tabla
            if (empleados.length === 0) {
                tablaBody.innerHTML = '<tr><td colspan="5">No se encontraron empleados en esta sucursal.</td></tr>';
                return;
            }

            empleados.forEach(emp => {
                // Lógica para mostrar los roles
                let rolesHtml = `<span class="rol-principal">${emp.rol_principal || 'N/A'}</span>`;
                if (emp.roles_adicionales) {
                    // Divide la cadena "RolA, RolB" en un array y crea un span para cada uno
                    const adicionales = emp.roles_adicionales.split(', ').map(rol => 
                        `<span class="rol-adicional">${rol}</span>`
                    ).join('');
                    rolesHtml += adicionales;
                }

                // Lógica para el estado
                const estadoClase = emp.emp_activo ? 'estado-activo' : 'estado-inactivo';
                const estadoTexto = emp.emp_activo ? 'Activo' : 'Inactivo';
                const accionTexto = emp.emp_activo ? 'Desactivar' : 'Activar';
                const accionClase = emp.emp_activo ? 'btn-desactivar' : 'btn-activar';

                const row = `
                    <tr>
                        <td>${emp.emp_id}</td>
                        <td>${emp.emp_nombre} ${emp.emp_apellido}</td>
                        <td><div class="roles-container">${rolesHtml}</div></td>
                        <td><span class="estado ${estadoClase}">${estadoTexto}</span></td>
                        <td class="acciones">
                            <button class="btn-accion btn-editar" data-id="${emp.emp_id}" title="Editar Roles/Info">Editar</button>
                            <button class="btn-accion btn-password" data-id="${emp.emp_id}" title="Cambiar Contraseña">Contraseña</button>
                            <button class="btn-accion ${accionClase}" data-id="${emp.emp_id}" data-estado="${emp.emp_activo}">
                                ${accionTexto}
                            </button>
                        </td>
                    </tr>
                `;
                tablaBody.insertAdjacentHTML('beforeend', row);
            });
        } catch (error) {
            tablaBody.innerHTML = `<tr><td colspan="5" style="color: red;">Error: ${error.message}</td></tr>`;
        }
    };


    // --- FUNCIONES DE MODALES ---

    const abrirModal = (modalId) => {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'flex';
    };
    const cerrarModal = (modalId) => {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'none';
    };

    // --- Lógica para abrir/cerrar modales ---
    closeButtons.forEach(btn => btn.addEventListener('click', () => cerrarModal(btn.dataset.modalId)));
    cancelButtons.forEach(btn => btn.addEventListener('click', () => cerrarModal(btn.dataset.modalId)));

    // --- Lógica de Acciones de la Tabla ---
    tablaBody.addEventListener('click', async (event) => {
        const boton = event.target;
        const id = boton.dataset.id;
        
        if (!id) return;

        // --- Lógica del botón EDITAR ---
        if (boton.classList.contains('btn-editar')) {
            // 1. Mostrar modal con "Cargando..."
            abrirModal('modal-editar-empleado');
            document.getElementById('edit-roles-adicionales').innerHTML = '<p>Cargando roles...</p>';
            
            // 2. Pedir datos al API de detalle
            try {
                const response = await fetch(`/api/empleado_detalle/${id}`);
                const data = await response.json();
                if (!response.ok) throw new Error(data.error);

                // 3. Llenar el formulario del modal
                document.getElementById('edit-emp-id').value = id;
                document.getElementById('edit-nombre').value = data.info_basica.emp_nombre;
                document.getElementById('edit-apellido').value = data.info_basica.emp_apellido;
                document.getElementById('edit-correo').value = data.info_basica.emp_correo;
                document.getElementById('edit-telefono').value = data.info_basica.emp_telefono;

                // 4. Llenar los selects de roles
                const rolPrincipalSelect = document.getElementById('edit-rol-principal');
                const rolesAdicionalesDiv = document.getElementById('edit-roles-adicionales');
                
                rolPrincipalSelect.innerHTML = '';
                rolesAdicionalesDiv.innerHTML = '';

                data.roles_posibles.forEach(rol => {
                    // Añadir al select de Rol Principal
                    const esPrincipal = rol.rol_id === data.info_basica.emp_rol_principal;
                    rolPrincipalSelect.innerHTML += `<option value="${rol.rol_id}" ${esPrincipal ? 'selected' : ''}>${rol.rol_nombre}</option>`;
                    
                    // Añadir como checkbox de Rol Adicional (si NO es el principal)
                    if (rol.rol_id !== data.info_basica.emp_rol_principal) {
                        const esAdicional = data.roles_actuales.includes(rol.rol_id);
                        rolesAdicionalesDiv.innerHTML += `
                            <label>
                                <input type="checkbox" name="roles_adicionales" value="${rol.rol_id}" ${esAdicional ? 'checked' : ''}>
                                ${rol.rol_nombre}
                            </label>
                        `;
                    }
                });
            } catch (error) {
                alert(error.message);
                cerrarModal('modal-editar-empleado');
            }
        }
        // --- Lógica del botón CONTRASEÑA ---
        if (boton.classList.contains('btn-password')) {
            document.getElementById('password-emp-id').value = id;
            document.getElementById('password-emp-nombre').textContent = boton.dataset.nombre; // Usamos el nombre guardado en el botón
            document.getElementById('nueva-password').value = '';
            abrirModal('modal-password');
        }
        // --- Lógica del botón ACTIVAR/DESACTIVAR ---
        if (boton.classList.contains('btn-activar') || boton.classList.contains('btn-desactivar')) {
            const estadoActual = boton.dataset.estado === '1' || boton.dataset.estado === 'true';
            const nuevoEstado = !estadoActual;
            const accion = nuevoEstado ? 'ACTIVAR' : 'DESACTIVAR';
            if (confirm(`¿Estás seguro de que deseas ${accion} al empleado ${id}?`)) {
                try {
                    const response = await fetch('/api/empleado/actualizar_estado', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ emp_id: id, nuevo_estado: nuevoEstado })
                    });
                    const data = await response.json();
                    alert(data.message);
                    if (response.ok) {
                        cargarEmpleados(); // Recargar la tabla para ver el cambio
                    }
                } catch (error) {
                    alert('Error de conexión: ' + error.message);
                }
            }
        }
    });
    // --- Lógica para GUARDAR cambios del modal EDITAR ---
    formEditar.addEventListener('submit', async (event) => {
        event.preventDefault();
        const submitButton = formEditar.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        // Recolectar datos
        const formData = new FormData(formEditar);
        const rolesAdicionales = [];
        document.querySelectorAll('#edit-roles-adicionales input[type="checkbox"]:checked').forEach(checkbox => {
            rolesAdicionales.push(checkbox.value);
        });
        const dataToSend = {
            emp_id: formData.get('emp_id'),
            nombre: formData.get('nombre'),
            apellido: formData.get('apellido'),
            correo: formData.get('correo'),
            telefono: formData.get('telefono'),
            rol_principal: formData.get('rol_principal'),
            roles_adicionales: rolesAdicionales
        };
        try {
            const response = await fetch('/api/empleado/actualizar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dataToSend)
            });
            const data = await response.json();
            alert(data.message);
            if (response.ok) {
                cerrarModal('modal-editar-empleado');
                cargarEmpleados(); // Recargar la tabla
            }
        } catch (error) {
            alert('Error de conexión: ' + error.message);
        } finally {
            submitButton.disabled = false;
        }
    });
    // --- Lógica para GUARDAR nueva CONTRASEÑA ---
    formPassword.addEventListener('submit', async (event) => {
        event.preventDefault();
        const submitButton = formPassword.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        
        const dataToSend = {
            emp_id: document.getElementById('password-emp-id').value,
            nueva_password: document.getElementById('nueva-password').value
        };
        try {
            const response = await fetch('/api/empleado/cambiar_password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dataToSend)
            });
            const data = await response.json();
            alert(data.message);
            if (response.ok) {
                cerrarModal('modal-password');
            }
        } catch (error) {
            alert('Error de conexión: ' + error.message);
        } finally {
            submitButton.disabled = false;
        }
    });
    // --- Asignar Eventos ---
    sucursalSelector.addEventListener('change', cargarEmpleados);
    cargarEmpleados();
});