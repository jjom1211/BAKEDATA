// produccion.js

// Función para redirigir a la página de materias primas
function verMateriaPrima() {
    window.location.href = "/materias_primas.html";
}

// Carga desde localStorage el registro de producción del día, o crea un array vacío si no hay datos
let produccionDelDia = JSON.parse(localStorage.getItem('produccionDelDia')) || [];

// Nota: La función registrarProduccion con window.location.href es obsoleta, 
// se mantiene la función que usa Fetch más abajo.

// Funciones básicas con alert para pruebas
function verPan() { alert("Mostrando lista de pan..."); }
function actualizarPan() { alert("Actualizando pan..."); }
function eliminarPan() { alert("Eliminando pan..."); }
function agregarPan() { alert("Agregando pan al inventario..."); }
function reservarProductos() {
    alert("Reservando productos para pedido (Solo Admin)...");
}

// Redirige a la página de solicitar materia prima
function solicitarMateriaPrima() {
    window.location.href = "/solicitarMateriaPrima.html";
}

// Abre o cierra la barra lateral
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('active');
}

// Abre o cierra un submenú dentro de la sidebar
function toggleSubmenu(button) {
    const submenu = button.closest('.menu-item').querySelector('.submenu');
    if (submenu) {
        submenu.style.display = submenu.style.display === 'flex' ? 'none' : 'flex';
        button.textContent = submenu.style.display === 'flex' ? '▾' : '▸';
    }
}

// Objeto global donde se guardan las materias seleccionadas para la solicitud
let materiasSeleccionadas = {};

// ---------------------------------------------
// FUNCIÓN 1: Búsqueda y Autocompletado (Estilo Google)
// ---------------------------------------------
async function buscarMaterias() {
    const sugerenciasUl = document.getElementById('sugerencias');
    const sugerenciasContainer = document.getElementById('contenedor-sugerencias');
    const query = document.getElementById('buscador').value;
    
    sugerenciasUl.innerHTML = "";
    sugerenciasUl.style.display = "block";
    sugerenciasContainer.style.display = "block";


    // 1. Ocultar si está vacío
    if (query.trim() === "") {
        sugerenciasContainer.style.display = "inline";
        return;
    }

    try {
        const response = await fetch(`/buscar_materias?query=${encodeURIComponent(query)}`);
        const data = await response.json();

        sugerenciasUl.innerHTML = ""; // Limpiar contenido antes de añadir
        
        if (data.length === 0) {
            sugerenciasUl.innerHTML = "<div style='padding: 10px;'>No se encontraron resultados.</div>";
        } else {
             data.forEach(materia => {
                 const div = document.createElement("div");
                 div.textContent = `${materia.nombre} (${materia.unidad}) - ${materia.descripcion || 'Sin descripción'}`;
                 
                 // ✅ CORRECCIÓN: Asignar el evento onclick para seleccionar la materia
                 const materiaData = encodeURIComponent(JSON.stringify(materia));
                 div.onclick = () => {
                     agregarMateriaASeleccionados(materiaData);
                 };
                 
                 sugerenciasUl.appendChild(div);
             });
        }
        
        // 3. CLAVE: Mostrar el contenedor después de procesar los datos
        sugerenciasContainer.style.display = "block";

    } catch (error) {
        console.error("Error buscando materias primas:", error);
        sugerenciasContainer.style.display = "none";
    }
}

// ---------------------------------------------
// FUNCIÓN 2: Agrega la materia seleccionada al contenedor de confirmación
// ---------------------------------------------
function agregarMateriaASeleccionados(encodedData) {
    const jsonString = decodeURIComponent(encodedData);
    const materia = JSON.parse(jsonString);
    const id = materia.id.toString();
    
    const buscador = document.getElementById('buscador');
    //const sugerenciasUl = document.getElementById('sugerencias'); 
    const listaSeleccionadas = document.getElementById("listaSeleccionadas");
    
    // 1. Limpiar UI
    buscador.value = "";

    if (materiasSeleccionadas[id]) {
        alert(`La materia prima "${materia.nombre}" ya está en la lista.`);
        return;
    }
    
    // 2. Crear la entrada inicial en el objeto de selección
    materiasSeleccionadas[id] = { 
        nombre: materia.nombre, 
        unidad: materia.unidad, 
        cantidad: "1" 
    };

    // 3. Crear el elemento LI con el checkbox y la cantidad 
    const li = document.createElement("li");
    li.id = `item-confirm-${id}`;
    
    li.innerHTML = `
        <div class="confirm-header">
            <input type="checkbox" class="check-materia" id="check-${id}" checked 
                data-id="${id}" data-nombre="${materia.nombre}" data-unidad="${materia.unidad}">
            <strong>${materia.nombre} (${materia.unidad})</strong>
        </div>
        <div class="confirm-quantity">
            <label>Cantidad:</label>
            <input type="number" id="cantidad-input-${id}" min="1" value="1">
        </div>
    `;

    listaSeleccionadas.appendChild(li);

    // 4. Agregar listeners para este NUEVO elemento
    agregarListenersAItem(id, materia.nombre, materia.unidad);

    // 5. Actualizar el contenedor general (mostrarlo si estaba oculto)
    actualizarListaSeleccionadas(true);
}

// ---------------------------------------------
// FUNCIÓN 3: Agregar Listeners a un ÚNICO ítem
// ---------------------------------------------
function agregarListenersAItem(id, nombre, unidad) {
    const check = document.getElementById(`check-${id}`);
    const cantidadInput = document.getElementById(`cantidad-input-${id}`);

    // Si el elemento no existe (error raro), salimos.
    if (!check || !cantidadInput) {
         console.error(`Fallo al encontrar check o input para ID: ${id}`);
         return;
    } 

    // Evento cuando se marca o desmarca un checkbox
    check.addEventListener('change', () => {
        if (check.checked) {
            let cantidad = cantidadInput.value.trim() || "1";
            if (parseInt(cantidad) < 1) cantidad = "1";
            cantidadInput.value = cantidad;
            
            materiasSeleccionadas[id] = { nombre, unidad, cantidad };
            cantidadInput.disabled = false;
        } else {
            delete materiasSeleccionadas[id];
            cantidadInput.disabled = true;
            // Opcional: itemContainer.remove(); 
        }
        actualizarListaSeleccionadas();
    });

    // Evento cuando cambia la cantidad
    cantidadInput.addEventListener('input', () => {
        let cantidad = cantidadInput.value.trim();
        if (check.checked) {
            if (cantidad === "" || parseInt(cantidad) < 1) {
                cantidad = "1";
                cantidadInput.value = cantidad;
            }
            materiasSeleccionadas[id].cantidad = cantidad;
        }
        actualizarListaSeleccionadas();
    });
}


// ---------------------------------------------
// FUNCIÓN 4: Actualiza la lista de confirmación y el botón
// ---------------------------------------------
function actualizarListaSeleccionadas() {
    const container = document.getElementById("seleccionadasContainer");
    const boton = document.getElementById("botonEnviar");
    const seleccionadas = Object.values(materiasSeleccionadas);

    // Siempre mostramos el contenedor y el botón
    container.style.display = "block";
    boton.style.display = "inline-block";

    // Si no hay seleccionadas, solo limpiamos la lista
    if (seleccionadas.length === 0) {
        document.getElementById("listaSeleccionadas").innerHTML = "";
    }
}

// Envía la solicitud final de materias seleccionadas
function enviarSolicitud() {
    const seleccionadas = Object.values(materiasSeleccionadas);

    if (seleccionadas.length === 0) {
        alert("No has seleccionado ninguna materia prima.");
        return;
    }

    let resumen = "Se confirmó la solicitud de:\n\n";
    seleccionadas.forEach(m => {
        resumen += `- ${m.nombre}: ${m.cantidad} ${m.unidad}\n`;
    });
    
    alert(resumen + "\n\n(Solicitud enviada al área de Producción/Almacén.)");

    // Limpia la UI después de "enviar"
    materiasSeleccionadas = {};
    document.getElementById('buscador').value = "";
    document.getElementById('sugerencias').innerHTML = "";
    actualizarListaSeleccionadas();
}


// ---------------------------------------------
// Lógica para registrar-produccion.html (Encapsulada)
// ---------------------------------------------
const searchBox = document.getElementById("search-box");
const resultsDiv = document.getElementById("results");

if (searchBox && resultsDiv) {
    searchBox.addEventListener("input", function () {
        let query = this.value;

        resultsDiv.innerHTML = "";

        if (query.length > 1) {
            fetch(`/buscar_productos?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(item => {
                        const div = document.createElement("div");
                        div.textContent = `${item.nombre} (${item.unidad})`;
                        div.onclick = function () {
                            document.getElementById("search-box").value = item.nombre;
                            document.getElementById("producto_id").value = item.id;
                            resultsDiv.innerHTML = "";
                        };
                        resultsDiv.appendChild(div);
                    });
                })
                .catch(err => console.error("Error en búsqueda:", err));
        }
    });
}

// === Registrar producción (Fetch) ===
// Carga proveedores desde el backend al cargar la página
async function cargarProveedores() {
    const select = document.getElementById('proveedorSelect');

    try {
        const response = await fetch('/obtener_proveedores');
        const proveedores = await response.json();

        proveedores.forEach(prov => {
            const option = document.createElement('option');
            option.value = prov.id;
            option.textContent = prov.nombre;
            option.setAttribute('data-nombre', prov.nombre); // Guarda el nombre de la empresa
            select.appendChild(option);
        });

    } catch (error) {
        console.error("Error al cargar proveedores:", error);
        // Opcional: mostrar un mensaje de error en la UI
    }
}

// ----------------------------
// Lógica de búsqueda de productos (como materias)
// ----------------------------
let productosSeleccionados = {};

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
    const lista = document.getElementById("listaSeleccionadasProducto");

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

// ----------------------------
// Registrar producción final
// ----------------------------
async function registrarProduccion() {
    window.location.href = "/registrar-produccion.html";
    const seleccionados = Object.values(productosSeleccionados);


    for (const prod of seleccionados) {
        await fetch("/registrar_produccion", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                producto_id: prod.id,
                cantidad: prod.cantidad
            })
        })
        .then(r => r.json())
        .then(data => console.log(data))
        .catch(err => console.error("Error al registrar producción:", err));
    }
}
