const categories = [
    "Panes", "Gelatinas y flanes", "Galletas", "Pasteles", "Postres", "Pan de temporada"
];

document.write(categories.map(category => `
    <div class="product-section">
        <h2 class="title-black">${category}</h2>
        <button class="view-all-btn">Ver todo</button>
    </div>
    <div class="carousel-container">
        <button class="arrow left-arrow" onclick="moveSlide(-1, '${category}')">&#10094;</button>
        <div class="carousel" id="carousel-${category.replace(/\s/g, '')}">
            <div>
                <img src="https://via.placeholder.com/200" alt="${category} 1">
                <p class="product-name">Producto 1</p>
                <p class="product-price">Precio por unidad: $5</p>
            </div>
        </div>
        <button class="arrow right-arrow" onclick="moveSlide(1, '${category}')">&#10095;</button>
    </div>
`).join(''));


function realizarPedido() {
    window.location.href = "usurealizapedido.html";
}
function sucursales() {
    window.location.href = "ususucursales.html";
}
function conocenos() {
    window.location.href = "usuconocenos.html";
}

function promocionesycupones() {
    window.location.href = "usupromocionesycupones.html";
}

