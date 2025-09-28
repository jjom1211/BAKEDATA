// Objeto de datos que define toda la estructura de la barra lateral
const menuData = [
    { name: "Almacén", url: "/almacen", roles: ["A", "EA", "E", "G"], icon: "https://i.imgur.com/vp9A1f3.png", submenu: [
        { name: "Registrar Entradas", url: "/almacen/entradas", roles: ["A"] },
        { name: "Actualizar Materia Prima", url: "/actualizarMateriaPrima", roles: ["A"] },
        { name: "Registrar Salidas", url: "/registrarSalidas", roles: ["A"] },
        { name: "Actualizar Productos", url: "/actualizarProductos", roles: ["A"] },
        { name: "Ver Productos", url: "/verProductos", roles: ["A"] },
        { name: "Ver Materias Primas", url: "/verMateriasPrimas", roles: ["A"] },
        { name: "Solicitar Productos", url: "/solicitarProductos", roles: ["EA", "E", "G"] },
        { name: "Solicitar Materia Prima", url: "/solicitarMateriaPrima", roles: ["EA", "E", "G"] },
        { name: "Enviar Productos a Tienda", url: "/enviarProductos", roles: ["EA", "E", "G"] }
    ]},
    { name: "Reparto", url: "/reparto", roles: ["R", "ER", "E", "G"], icon: "https://i.imgur.com/dZdUNal.png", submenu: [
        { name: "Calendario", url: "/CalendarioReparto", roles: ["R"] },
        { name: "Pedidos", url: "/Pedidos", roles: ["R"] },
        { name: "Actualizar Entrega", url: "/actualizarEntrega", roles: ["ER", "E", "G"]},
        { name: "Confirmar entrega", url: "/confirmarEntrega", roles: ["ER", "E", "G"]},
        { name: "Agregar entrega", url: "/agregarEntrega", roles: ["ER", "E", "G"] }
    ]},
    { name: "Usuario", url: "/usuario", roles: ["U", "E", "G"], icon: "https://i.imgur.com/WLyck1q.png", submenu: [
        { name: "Catálogo", url: "/verCatalogo", roles: ["U"] },
        { name: "Realizar Pedido", url: "/realizarPedido", roles: ["U"] },
        { name: "Ver sucursales", url: "/verSucursales", roles: ["U"] },
    ]},
    { name: "Producción", url: "/produccion", roles: ["P", "EP", "E", "G"], icon: "https://i.imgur.com/3cO5Fks.png", submenu: [
        { name: "Ver Materia Prima", url: "/verMateriaPrima", roles: ["P"] },
        { name: "Producción de hoy", url: "/produccionDeHoy", roles: ["P"] },
        { name: "Registrar producción", url: "/registrarProduccion", roles: ["EP", "E", "G"] },
        { name: "Solicitar Materia Prima", url: "/solicitarMateriaPrima", roles: ["EP", "E", "G"] }
    ]},
    { name: "Ventas", url: "/ventas", roles: ["V", "EV", "E", "G"], icon: "https://i.imgur.com/aUIJoQt.png", submenu: [
        { name: "Registrar Cliente", url: "/registrarCliente", roles: ["V"] },
        { name: "Registrar Venta", url: "/registrarVenta", roles: ["V"] },
        { name: "Realizar Pedido", url: "/realizarPedidoVenta", roles: ["V"] },
        { name: "Actualizar Caja", url: "/actualizarCaja", roles: ["V"] },
        { name: "Ver Caja", url: "/verCaja", roles: ["V"] },
        { name: "Ver Productos", url: "/verProductosVenta", roles: ["V"] },
        { name: "Solicitar Productos", url: "/solicitarProductosVenta", roles: ["EV", "E", "G"] },
        { name: "Corte de Caja", url: "/corteDeCaja", roles: ["E", "G"] },
        { name: "Reporte del Día", url: "/reporteDelDia", roles: ["E", "G"] },
        { name: "Reporte Mensual", url: "/reporteMensual", roles: ["E", "G"] }
    ]},
    { name: "Limpieza", url: "/limpieza", roles: ["L", "EL", "E", "G"], icon: "https://i.imgur.com/75aCNcB.png", submenu: [
        { name: "Calendario", url: "/limCalendario", roles: ["L"] },
        { name: "Limpieza del Dia", url: "/limDia", roles: ["L"] },
        { name: "Registrar Limpieza", url: "/limRegistrarLimpieza", roles: ["EL", "E", "G"] },
        { name: "Actualizar fecha de limpieza", url: "/limActualizarFechaLimpieza", roles: ["EL", "E", "G"] },
    ]},
    { name: "Encargado", url: "/encargado", roles: ["E", "G"], icon: "https://i.imgur.com/AU09egm.png", submenu: [
        { name: "Gestión de permisos", url: "/gestionPermisos", roles: ["E", "G"] },
        { name: "Crear Cuenta de empleado", url: "/crearCuentaEmpleado", roles: ["E", "G"] },
        { name: "Gestión de empleados", url: "/gestionEmpleados", roles: ["E", "G"] }
    ]},
    { name: "Reportes", url: "/reportes", roles: ["G"], icon: "https://i.imgur.com/8b2Igfw.png", submenu: [
        { name: "Reporte del Día", url: "/reporteDelDia", roles: ["G"] },
        { name: "Reporte Semanal", url: "/reporteDelDia", roles: ["G"] },
        { name: "Reportes Mensuales", url: "/reportes/mensuales", roles: ["G"] },
        { name: "Reportes Trimestrales", url: "/reportes/trimestrales", roles: ["G"] },
        { name: "Reportes Anuales", url: "/reportes/anuales", roles: ["G"] }
    ]},
    { name: "Gerente", url: "/gerente", roles: ["G"], icon: "https://i.imgur.com/AU09egm.png", submenu: []}
];

const roleToClassMap = {
    "A": "slide-button-almacen",
    "R": "slide-button-reparto",
    "U": "slide-button-usuario",
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
    const roles = JSON.parse(sessionStorage.getItem("roles") || "[]").map(r => r.toUpperCase());
    
    if (!roles.length) {
        window.location.href = "/";
        return;
    }

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