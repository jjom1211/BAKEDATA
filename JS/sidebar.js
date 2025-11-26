// Objeto de datos que define toda la estructura de la barra lateral
const menuData = [
    { name: "Almacén", url: "/almacen", roles: ["A", "EA", "E", "G"], icon: "https://i.imgur.com/vp9A1f3.png", submenu: [
        { name: "Registrar Entradas", url: "/registrarEntradas", roles: ["A"] },
        { name: "Registrar Salidas", url: "/registrarSalidas", roles: ["A"] },
        { name: "Ver Productos", url: "/almacen/verProductos", roles: ["A"] },
        { name: "Ver Materias Primas", url: "/almacen/verMateriasPrimas", roles: ["A"] },
        { name: "Actualizar Materia Prima", url: "/actualizarMateriaPrima", roles: ["G"]},
        { name: "Actualizar Productos", url: "/actualizarProductos", roles: ["G"] },
        { name: "Solicitar Productos", url: "/almacen/solicitarProductos", roles: ["EA", "E", "G"] },
        { name: "Solicitar Materia Prima", url: "/almacen/solicitarMateriaPrima", roles: ["EA", "E", "G"] },
    ]},
    { name: "Reparto", url: "/reparto", roles: ["R", "ER", "E", "G"], icon: "https://i.imgur.com/dZdUNal.png", submenu: [
        { name: "Calendario", url: "/CalendarioReparto", roles: ["R"] },
        { name: "Pedidos", url: "/Pedidos", roles: ["R"] },
        { name: "Repartos del dia", url: "/repDia", roles: ["R"] },
        {name: "Gestion Logistica", url: "/gestionLogistica", roles: ["ER", "E", "G"]},
    ]},
    { name: "Producción", url: "/produccion", roles: ["P", "EP", "E", "G"], icon: "https://i.imgur.com/3cO5Fks.png", submenu: [
        { name: "Ver Materia Prima", url: "/verMateriaPrima", roles: ["P"] },
        { name: "Producción de hoy", url: "/produccionDeHoy", roles: ["P"] },
        { name: "Registrar producción", url: "/registrarProduccion", roles: ["EP", "E", "G"] },
        { name: "Solicitar Materia Prima", url: "/solicitarMateriaPrima", roles: ["EP", "E", "G"] }
    ]},
    { name: "Ventas", url: "/ventas", roles: ["V", "EV", "E", "G"], icon: "https://i.imgur.com/aUIJoQt.png", submenu: [
        { name: "Registrar Cliente", url: "/ventas/registrarCliente", roles: ["V"] },
        { name: "Registrar Venta", url: "/registrarVenta", roles: ["V"] },
        { name: "Entregar Pedidos", url: "/cobrarPedidos", roles: ["V"] },
        { name: "Ver Caja", url: "/verCaja", roles: ["V"] },
        { name: "Movmientos de efectivo", url: "/movimientosEfectivo", roles: ["V"] },
        { name: "Ver Productos", url: "/verProductosVenta", roles: ["V"] },
        { name: "Actualizar Caja", url: "/actualizarCaja", roles:  ["EV", "E", "G"]},
        { name: "Solicitar Productos", url: "/solicitarProductos", roles: ["EV", "E", "G"] },
        { name: "Corte de Caja", url: "/corteDeCaja", roles: ["E", "G"] },
    ]},
    { name: "Limpieza", url: "/limpieza", roles: ["L", "EL", "E", "G"], icon: "https://i.imgur.com/75aCNcB.png", submenu: [
        { name: "Calendario", url: "/limCalendario", roles: ["L"] },
        { name: "Limpieza del Dia", url: "/limDia", roles: ["L"] },
        { name: "Registrar Limpieza", url: "/limRegistrarLimpieza", roles: ["EL", "E", "G"] },
        { name: "Actualizar fecha de limpieza", url: "/limActualizarFechaLimpieza", roles: ["EL", "E", "G"] },
    ]},
    { name: "Encargado", url: "/encargado", roles: ["E", "G"], icon: "https://i.imgur.com/AU09egm.png", submenu: [
        { name: "Crear Cuenta de empleado", url: "/crearCuentaEmpleado", roles: ["E", "G"] },
        { name: "Gestión de empleados", url: "/gestionEmpleados", roles: ["E", "G"] },
    ]},
    { name: "Reportes", url: "/reportes", roles: ["G"], icon: "https://i.imgur.com/8b2Igfw.png", submenu: [
        { name: "Reportes de Ventas", url: "/reporteDeVentas", roles: ["G"] },
        { name: "Reporte de caja", url: "/reporteDeCaja", roles: ["G"] },
        { name: "Reporte de inventario", url: "/reporteDeInventario", roles: ["G"] },
    ]},
    { name: "Gerente", url: "/gerente", roles: ["G"], icon: "https://i.imgur.com/AU09egm.png", submenu: []}
];

const roleHierarchy = {
    "EA": ["A"],  // Encargado de Almacén hereda de Almacenista
    "ER": ["R"],  // Encargado de Reparto hereda de Repartidor
    "EP": ["P"],  // Encargado de Producción hereda de Productor
    "EV": ["V"],  // Encargado de Ventas hereda de Vendedor
    "EL": ["L"]   // Encargado de Limpieza hereda de Limpiador
};

const roleToClassMap = {
    "A": "slide-button-almacen",
    "R": "slide-button-reparto",
    "P": "slide-button-produccion",
    "V": "slide-button-ventas",
    "L": "slide-button-limpieza",
};

// Funciones globales
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}

function toggleSubmenu(button) {
    const submenu = button.closest('.menu-item').querySelector('.submenu');
    if (submenu) {
        submenu.style.display = submenu.style.display === "flex" ? "none" : "flex";
        button.textContent = submenu.style.display === "flex" ? "▾" : "▸";
    }
}

function Salir() {
    sessionStorage.clear();
    window.location.href = "/";
}

document.addEventListener("DOMContentLoaded", () => {
       // Obtenemos los roles base del usuario desde sessionStorage
    const baseRoles = JSON.parse(sessionStorage.getItem("roles") || "[]").map(r => r.toUpperCase());
    // si no tiene permisos, lo enviamos al login
    if (!baseRoles.length) {
        window.location.href = "/";
        return;
    }
    // ---CALCULAR ROLES EFECTIVOS ---
    const effectiveRoles = new Set(baseRoles); // Usamos un Set para evitar duplicados
    baseRoles.forEach(role => {
        // Si el rol del usuario está en nuestro mapa de jerarquía (ej. "ER")
        if (roleHierarchy[role]) {
            // Agregamos los roles que hereda (ej. "R") al set
            roleHierarchy[role].forEach(inheritedRole => effectiveRoles.add(inheritedRole));
        }
    });
    const roles = Array.from(effectiveRoles); // Convertimos el Set de nuevo a un Array
    const esGerente = roles.includes("G");
    const esEncargado = roles.includes("E");
    const sidebarContent = document.querySelector(".sidebar-content");

    menuData.forEach(menuItem => {
        // La condición para mostrar el menú principal es que el usuario tenga un rol que coincida con los roles del menú, o que sea un Gerente.
        const showMenu = esGerente || menuItem.roles.some(r => roles.includes(r));
        
        if (showMenu) {
            const menuDiv = document.createElement("div");
            menuDiv.classList.add("menu-item");
            if (menuItem.submenu && menuItem.submenu.length > 0) {
                menuDiv.classList.add("doble-opcion");
            }
            
            const wrapperDiv = document.createElement("div");
            wrapperDiv.classList.add("ir-item-wrapper");

            if (menuItem.submenu && menuItem.submenu.length > 0) {
                const toggleBtn = document.createElement("button");
                toggleBtn.classList.add("toggle-submenu");
                toggleBtn.textContent = "▸";
                toggleBtn.addEventListener("click", () => {
                    const submenu = menuDiv.querySelector(".submenu");
                    submenu.style.display = submenu.style.display === "flex" ? "none" : "flex";
                    toggleBtn.textContent = submenu.style.display === "flex" ? "▾" : "▸";
                });
                wrapperDiv.appendChild(toggleBtn);
            }
            
            const iconImg = document.createElement("img");
            iconImg.src = menuItem.icon;
            iconImg.alt = `${menuItem.name} Icon`;
            iconImg.classList.add("icono-sidebar");
            wrapperDiv.appendChild(iconImg);

            const mainButton = document.createElement("button");
            mainButton.classList.add("button", "ir-item");
            mainButton.textContent = menuItem.name;
            mainButton.dataset.url = menuItem.url;

            wrapperDiv.appendChild(mainButton);
            menuDiv.appendChild(wrapperDiv);

            if (menuItem.submenu && menuItem.submenu.length > 0) {
                const submenuDiv = document.createElement("div");
                submenuDiv.classList.add("submenu");
                menuItem.submenu.forEach(subItem => {
                    const subItemRoles = Array.isArray(subItem.roles) ? subItem.roles : [subItem.roles];
                    const showSubmenu = esGerente || esEncargado || subItemRoles.some(r => roles.includes(r));
                    
                    if (showSubmenu) {
                        const subButton = document.createElement("button");
                        subButton.classList.add("button");
                        
                        // Añadir la clase de departamento correspondiente al rol
                        const departmentRole = menuItem.roles[0];
                        if (roleToClassMap[departmentRole]) {
                            subButton.classList.add(roleToClassMap[departmentRole]);
                        }
                        
                        // Si el botón tiene roles de administrador, aplicar también esa clase
                        if (subItemRoles.some(r => r === "E" || r === "G")) {
                            subButton.classList.add("slide-button-admin");
                        }
                        
                        subButton.textContent = subItem.name;
                        subButton.dataset.url = subItem.url;
                        submenuDiv.appendChild(subButton);
                    }
                });
                menuDiv.appendChild(submenuDiv);
            }
            sidebarContent.appendChild(menuDiv);
        }
    });

    const returnDiv = document.createElement("div");
    returnDiv.classList.add("menu-item");
    const returnImg = document.createElement("img");
    returnImg.src = "https://i.imgur.com/ft5fWsY.png";
    returnImg.alt = "Regresar Icon";
    returnImg.classList.add("icono-sidebar");
    const returnBtn = document.createElement("button");
    returnBtn.classList.add("button", "return-login");
    returnBtn.textContent = "Salir";
    returnBtn.addEventListener("click", Salir);
    returnDiv.appendChild(returnImg);
    returnDiv.appendChild(returnBtn);
    sidebarContent.appendChild(returnDiv);


    sidebarContent.addEventListener("click", (event) => {
        const clickedButton = event.target.closest("button");
        if (clickedButton && clickedButton.dataset.url) {
            window.location.href = clickedButton.dataset.url;
        }
    });
});