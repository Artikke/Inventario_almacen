/* ═══════════════════════════════════════════════════════
   PROESA – Sistema de Inventario (GitHub Pages + Firebase)
   ═══════════════════════════════════════════════════════ */

// ─── Firebase Config ───
// PEGA AQUI tu configuracion de Firebase (console.firebase.google.com)
const firebaseConfig = {
    apiKey: "AIzaSyA2TBZwWuebLhxb32BYcxr4DGb1A-iDC84",
    authDomain: "sistema-de-inventario-proesa.firebaseapp.com",
    projectId: "sistema-de-inventario-proesa",
    storageBucket: "sistema-de-inventario-proesa.firebasestorage.app",
    messagingSenderId: "788858693454",
    appId: "1:788858693454:web:e506cb5184a44f4ce6201f"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db   = firebase.firestore();

// Secondary app for creating users without logging out admin
let secondaryApp = null;
try {
    secondaryApp = firebase.app('secondary');
} catch {
    secondaryApp = firebase.initializeApp(firebaseConfig, 'secondary');
}
const secondaryAuth = secondaryApp.auth();

// ─── State ───
let currentUser = null;   // Firestore user doc
let currentUid  = null;

// ─── Data Constants ───
const AREAS = [
    'Talento Humano',
    'Mesa de Atencion al Cliente',
    'Contabilidad',
    'Finanzas',
    'Credito y Cobranza',
    'Abastecimiento y Compras',
    'Tecnologia de Informacion (TI)',
    'Business Intelligence (BI)'
];

const PRODUCTOS = {
    'Papeleria': [
        { nombre: 'Hojas blancas T/C', unidad: 'Paquete' },
        { nombre: 'Hojas blancas T/O', unidad: 'Paquete' },
        { nombre: 'Post-it 3x3', unidad: 'Paquete' },
        { nombre: 'Post-it banderitas', unidad: 'Paquete' },
        { nombre: 'Folder T/C', unidad: 'Pieza' },
        { nombre: 'Folder T/O', unidad: 'Pieza' },
        { nombre: 'Sobre manila T/C', unidad: 'Pieza' },
        { nombre: 'Sobre manila T/O', unidad: 'Pieza' }
    ],
    'Escritura': [
        { nombre: 'Boligrafo azul', unidad: 'Pieza' },
        { nombre: 'Boligrafo negro', unidad: 'Pieza' },
        { nombre: 'Boligrafo rojo', unidad: 'Pieza' },
        { nombre: 'Lapiz #2', unidad: 'Pieza' },
        { nombre: 'Marcatextos amarillo', unidad: 'Pieza' },
        { nombre: 'Marcador permanente negro', unidad: 'Pieza' },
        { nombre: 'Marcador pizarron', unidad: 'Pieza' }
    ],
    'Sujetadores': [
        { nombre: 'Clips estandar', unidad: 'Caja' },
        { nombre: 'Clips mariposa', unidad: 'Caja' },
        { nombre: 'Grapas estandar', unidad: 'Caja' },
        { nombre: 'Engrapadora', unidad: 'Pieza' },
        { nombre: 'Desengrapadora', unidad: 'Pieza' }
    ],
    'Adhesivos': [
        { nombre: 'Cinta adhesiva transparente', unidad: 'Pieza' },
        { nombre: 'Cinta canela', unidad: 'Pieza' },
        { nombre: 'Pegamento en barra', unidad: 'Pieza' },
        { nombre: 'Diurex', unidad: 'Pieza' }
    ],
    'Herramientas': [
        { nombre: 'Tijeras', unidad: 'Pieza' },
        { nombre: 'Cutter', unidad: 'Pieza' },
        { nombre: 'Regla 30cm', unidad: 'Pieza' },
        { nombre: 'Perforadora', unidad: 'Pieza' },
        { nombre: 'Goma de borrar', unidad: 'Pieza' },
        { nombre: 'Sacapuntas', unidad: 'Pieza' }
    ],
    'Pilas': [
        { nombre: 'Pilas AA', unidad: 'Par' },
        { nombre: 'Pilas AAA', unidad: 'Par' }
    ],
    'Proteccion': [
        { nombre: 'Cubrebocas', unidad: 'Caja' },
        { nombre: 'Gel antibacterial', unidad: 'Pieza' },
        { nombre: 'Toallas sanitizantes', unidad: 'Paquete' }
    ],
    'Varios': [
        { nombre: 'Toner impresora', unidad: 'Pieza' },
        { nombre: 'Mouse USB', unidad: 'Pieza' },
        { nombre: 'Teclado USB', unidad: 'Pieza' },
        { nombre: 'Cable HDMI', unidad: 'Pieza' }
    ]
};

// ═══════════════════════════════
//  AUTH
// ═══════════════════════════════

auth.onAuthStateChanged(async user => {
    if (user) {
        currentUid = user.uid;
        const doc = await db.collection('usuarios').doc(user.uid).get();
        if (doc.exists) {
            currentUser = { id: doc.id, ...doc.data() };
            showApp();
        } else {
            auth.signOut();
        }
    } else {
        currentUser = null;
        currentUid  = null;
        showLogin();
    }
});

async function login() {
    const userInput = document.getElementById('loginUser').value.trim();
    const pass      = document.getElementById('loginPass').value;
    const alert     = document.getElementById('loginAlert');
    const btn       = document.getElementById('loginBtn');

    if (!userInput || !pass) {
        alert.textContent = 'Ingresa usuario y contrasena';
        alert.classList.remove('d-none');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Entrando...';
    alert.classList.add('d-none');

    try {
        const email = userInput.includes('@') ? userInput : `${userInput}@proesa.app`;
        await auth.signInWithEmailAndPassword(email, pass);
    } catch (e) {
        alert.textContent = 'Usuario o contrasena incorrectos';
        alert.classList.remove('d-none');
        btn.disabled = false;
        btn.textContent = 'Iniciar Sesion';
    }
}

function logout() {
    auth.signOut();
}

function showLogin() {
    document.getElementById('loginView').style.display = '';
    document.getElementById('appView').style.display   = 'none';
    document.getElementById('loginUser').value = '';
    document.getElementById('loginPass').value = '';
    document.getElementById('loginAlert').classList.add('d-none');
    document.getElementById('loginBtn').disabled = false;
    document.getElementById('loginBtn').textContent = 'Iniciar Sesion';
}

function showApp() {
    document.getElementById('loginView').style.display = 'none';
    document.getElementById('appView').style.display   = '';
    renderNav();
    // Default view per role
    if (currentUser.rol === 'admin') showAdminPedidos();
    else if (currentUser.rol === 'lider') showAprobar();
    else showNuevoPedido();
}

// ─── Setup (first time) ───
async function toggleSetup(show) {
    if (show) {
        // Check if admin already exists — block setup if so
        const existing = await db.collection('usuarios').where('rol', '==', 'admin').limit(1).get();
        if (!existing.empty) {
            const alert = document.getElementById('loginAlert');
            alert.textContent = 'El sistema ya fue configurado. Inicia sesion con tu usuario.';
            alert.classList.remove('d-none');
            return;
        }
    }
    document.getElementById('setupFormDiv').classList.toggle('d-none', !show);
    document.getElementById('loginFormDiv').classList.toggle('d-none', show);
    document.getElementById('setupToggle').classList.toggle('d-none', show);
}

async function setupAdmin() {
    // Double-check no admin exists
    const existing = await db.collection('usuarios').where('rol', '==', 'admin').limit(1).get();
    if (!existing.empty) {
        const alert = document.getElementById('loginAlert');
        alert.textContent = 'El sistema ya fue configurado. No se puede crear otro admin.';
        alert.classList.remove('d-none');
        return;
    }

    const nombre = document.getElementById('setupNombre').value.trim();
    const user   = document.getElementById('setupUser').value.trim();
    const pass   = document.getElementById('setupPass').value;
    const alert  = document.getElementById('loginAlert');

    if (!nombre || !user || pass.length < 6) {
        alert.textContent = 'Completa todos los campos (contrasena min 6 caracteres)';
        alert.classList.remove('d-none');
        return;
    }

    try {
        alert.classList.add('d-none');
        const email = `${user}@proesa.app`;
        const cred  = await auth.createUserWithEmailAndPassword(email, pass);

        await db.collection('usuarios').doc(cred.user.uid).set({
            nombre: nombre,
            usuario: user,
            email: email,
            rol: 'admin',
            area: 'Administracion',
            activo: true,
            creadoEn: firebase.firestore.FieldValue.serverTimestamp()
        });

        await cargarDatosIniciales();
        showAlert('Sistema configurado correctamente', 'success');
    } catch (e) {
        alert.textContent = 'Error: ' + e.message;
        alert.classList.remove('d-none');
    }
}

async function cargarDatosIniciales() {
    const batch = db.batch();

    // Areas
    for (const area of AREAS) {
        const ref = db.collection('areas').doc();
        batch.set(ref, { nombre: area });
    }

    // Products
    for (const [categoria, items] of Object.entries(PRODUCTOS)) {
        for (const item of items) {
            const ref = db.collection('productos').doc();
            batch.set(ref, {
                nombre: item.nombre,
                categoria: categoria,
                unidad: item.unidad,
                activo: true
            });
        }
    }

    await batch.commit();
}

// ═══════════════════════════════
//  NAVIGATION
// ═══════════════════════════════

function renderNav() {
    const nav = document.getElementById('mainNav');
    const role = currentUser.rol;
    let links = '';

    // Todos pueden pedir material
    links += navLink('showNuevoPedido', 'bi-cart-plus', 'Nuevo Pedido');
    links += navLink('showMisPedidos', 'bi-list-check', 'Mis Pedidos');

    if (role === 'lider') {
        links += navLink('showAprobar', 'bi-check2-square', 'Aprobar');
    }
    if (role === 'admin') {
        links += navLink('showAdminPedidos', 'bi-clipboard-data', 'Pedidos');
        links += navLink('showExportar', 'bi-file-earmark-excel', 'Exportar');
        links += navLink('showHistorial', 'bi-bar-chart-line', 'Historial');
        links += navLink('showCatalogo', 'bi-box-seam', 'Catalogo');
        links += navLink('showUsuarios', 'bi-people', 'Usuarios');
    }

    nav.innerHTML = `
        <div class="container-fluid">
            <span class="navbar-brand"><i class="bi bi-building me-2"></i>PROESA</span>
            <button class="navbar-toggler" data-bs-toggle="collapse" data-bs-target="#navMenu">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navMenu">
                <ul class="navbar-nav me-auto">${links}</ul>
                <span class="navbar-text text-white me-3">
                    <i class="bi bi-person-circle me-1"></i>${currentUser.nombre}
                    <small class="ms-1 opacity-75">(${role})</small>
                </span>
                <button class="btn btn-outline-light btn-sm" onclick="logout()">
                    <i class="bi bi-box-arrow-right me-1"></i>Salir
                </button>
            </div>
        </div>`;
}

function navLink(fn, icon, label) {
    return `<li class="nav-item">
        <a class="nav-link" href="#" onclick="${fn}();return false" data-view="${fn}">
            <i class="bi ${icon} me-1"></i>${label}
        </a></li>`;
}

function setActiveNav(fn) {
    document.querySelectorAll('#mainNav .nav-link').forEach(a => {
        a.classList.toggle('active', a.dataset.view === fn);
    });
}

// ═══════════════════════════════
//  ALERTS
// ═══════════════════════════════

function showAlert(msg, type = 'info') {
    const c = document.getElementById('alertContainer');
    const id = 'alert-' + Date.now();
    c.innerHTML = `<div id="${id}" class="alert alert-${type} alert-dismissible fade show py-2" role="alert">
        ${msg}
        <button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>
    </div>`;
    setTimeout(() => {
        const el = document.getElementById(id);
        if (el) el.remove();
    }, 5000);
}

// ═══════════════════════════════
//  VIEW: Nuevo Pedido
// ═══════════════════════════════

async function showNuevoPedido() {
    setActiveNav('showNuevoPedido');
    const main = document.getElementById('mainContent');
    main.innerHTML = '<div class="spinner-proesa"><div class="spinner-border text-primary"></div></div>';

    const snap = await db.collection('productos').where('activo', '==', true).get();
    const productos = {};
    snap.forEach(d => {
        const p = d.data();
        if (!productos[p.categoria]) productos[p.categoria] = [];
        productos[p.categoria].push({ id: d.id, ...p });
    });
    // Sort categories alphabetically
    const sortedProductos = Object.keys(productos).sort().reduce((obj, key) => {
        obj[key] = productos[key];
        return obj;
    }, {});

    let accordionItems = '';
    let idx = 0;
    for (const [cat, items] of Object.entries(sortedProductos)) {
        const rows = items.map(p => `
            <tr>
                <td>${p.nombre}</td>
                <td class="text-center"><small class="text-muted">${p.unidad}</small></td>
                <td class="text-center">
                    <input type="number" min="0" value="0" class="form-control form-control-sm qty-input"
                           data-id="${p.id}" data-nombre="${p.nombre}" data-unidad="${p.unidad}"
                           onchange="updateSummary()" oninput="updateSummary()">
                </td>
            </tr>`).join('');

        accordionItems += `
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button ${idx > 0 ? 'collapsed' : ''}" data-bs-toggle="collapse"
                            data-bs-target="#cat${idx}">
                        <i class="bi bi-tag me-2"></i>${cat}
                        <span class="badge bg-secondary ms-2">${items.length}</span>
                    </button>
                </h2>
                <div id="cat${idx}" class="accordion-collapse collapse ${idx === 0 ? 'show' : ''}">
                    <div class="accordion-body p-0">
                        <table class="table table-sm table-hover mb-0">
                            <thead><tr>
                                <th>Producto</th><th class="text-center">Unidad</th><th class="text-center">Cant.</th>
                            </tr></thead>
                            <tbody>${rows}</tbody>
                        </table>
                    </div>
                </div>
            </div>`;
        idx++;
    }

    main.innerHTML = `
        <div class="row">
            <div class="col-lg-8">
                <div class="card card-proesa mb-3">
                    <div class="card-header card-header-proesa">
                        <i class="bi bi-cart-plus me-2"></i>Nuevo Pedido de Material
                    </div>
                    <div class="card-body">
                        <div class="search-box mb-3">
                            <i class="bi bi-search"></i>
                            <input type="text" class="form-control" placeholder="Buscar producto..."
                                   oninput="filterProducts(this.value)">
                        </div>
                        <div class="accordion accordion-proesa" id="catalogAccordion">
                            ${accordionItems}
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="order-summary" id="orderSummary">
                    <h6><i class="bi bi-receipt me-2"></i>Resumen del Pedido</h6>
                    <div id="summaryItems"><p class="text-muted small">Agrega productos...</p></div>
                    <hr>
                    <div class="d-flex justify-content-between fw-bold">
                        <span>Total de articulos:</span>
                        <span id="summaryTotal">0</span>
                    </div>
                    <button class="btn btn-proesa w-100 mt-3" onclick="submitPedido()" id="btnSubmit">
                        <i class="bi bi-send me-2"></i>Enviar Pedido
                    </button>
                </div>
            </div>
        </div>`;
}

function filterProducts(query) {
    const q = query.toLowerCase();
    document.querySelectorAll('#catalogAccordion tbody tr').forEach(row => {
        const name = row.querySelector('td').textContent.toLowerCase();
        row.style.display = name.includes(q) ? '' : 'none';
    });
}

function updateSummary() {
    const items = [];
    let total = 0;
    document.querySelectorAll('.qty-input').forEach(inp => {
        const qty = parseInt(inp.value) || 0;
        if (qty > 0) {
            items.push({ nombre: inp.dataset.nombre, cantidad: qty, unidad: inp.dataset.unidad });
            total += qty;
        }
    });

    const container = document.getElementById('summaryItems');
    if (items.length === 0) {
        container.innerHTML = '<p class="text-muted small">Agrega productos...</p>';
    } else {
        container.innerHTML = items.map(i =>
            `<div class="summary-item"><span>${i.nombre}</span><span>${i.cantidad} ${i.unidad}</span></div>`
        ).join('');
    }
    document.getElementById('summaryTotal').textContent = total;
}

async function submitPedido() {
    const detalles = [];
    document.querySelectorAll('.qty-input').forEach(inp => {
        const qty = parseInt(inp.value) || 0;
        if (qty > 0) {
            detalles.push({
                productoId: inp.dataset.id,
                nombre: inp.dataset.nombre,
                unidad: inp.dataset.unidad,
                cantidad: qty
            });
        }
    });

    if (detalles.length === 0) {
        showAlert('Agrega al menos un producto', 'warning');
        return;
    }

    const btn = document.getElementById('btnSubmit');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Enviando...';

    try {
        // Admin and lider orders skip leader approval step — go straight to admin
        const saltaLider = currentUser.rol === 'admin' || currentUser.rol === 'lider';
        await db.collection('pedidos').add({
            uid: currentUid,
            nombreEmpleado: currentUser.nombre,
            area: currentUser.area,
            detalles: detalles,
            estado: saltaLider ? 'aprobado_lider' : 'pendiente',
            fecha: firebase.firestore.FieldValue.serverTimestamp(),
            aprobadoPorLider: saltaLider ? currentUid : null,
            aprobadoPorAdmin: null,
            nombreLider: saltaLider ? currentUser.nombre : null,
            nombreAdmin: null,
            noInventario: null
        });
        showAlert('Pedido enviado correctamente', 'success');
        showMisPedidos();
    } catch (e) {
        showAlert('Error al enviar: ' + e.message, 'danger');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-send me-2"></i>Enviar Pedido';
    }
}

// ═══════════════════════════════
//  VIEW: Mis Pedidos
// ═══════════════════════════════

async function showMisPedidos() {
    setActiveNav('showMisPedidos');
    const main = document.getElementById('mainContent');
    main.innerHTML = '<div class="spinner-proesa"><div class="spinner-border text-primary"></div></div>';

    let snap;
    try {
        snap = await db.collection('pedidos')
            .where('uid', '==', currentUid)
            .get();
    } catch (e) {
        main.innerHTML = `<div class="alert alert-danger">Error al cargar pedidos: ${e.message}</div>`;
        console.error('showMisPedidos error:', e);
        return;
    }

    if (snap.empty) {
        main.innerHTML = `<div class="empty-state">
            <i class="bi bi-inbox"></i><h5>No tienes pedidos</h5>
            <p>Crea tu primer pedido de material</p>
            <button class="btn btn-proesa" onclick="showNuevoPedido()">
                <i class="bi bi-cart-plus me-2"></i>Nuevo Pedido
            </button></div>`;
        return;
    }

    // Sort by date descending in JS
    const pedidos = [];
    snap.forEach(d => pedidos.push({ id: d.id, ...d.data() }));
    pedidos.sort((a, b) => (b.fecha?.toMillis() || 0) - (a.fecha?.toMillis() || 0));

    let cards = '';
    pedidos.forEach(p => {
        const fecha = p.fecha ? p.fecha.toDate().toLocaleDateString('es-MX') : 'Pendiente';
        const items = (p.detalles || []).map(i =>
            `<li class="list-group-item d-flex justify-content-between py-1 px-2">
                <span>${i.nombre}</span>
                <span class="text-muted">${i.cantidad} ${i.unidad}</span>
            </li>`
        ).join('');

        cards += `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card card-proesa h-100">
                    <div class="card-header d-flex justify-content-between align-items-center bg-white border-bottom">
                        <strong>Pedido #${p.id.slice(-5).toUpperCase()}</strong>
                        ${badgeEstado(p.estado)}
                    </div>
                    <div class="card-body p-0">
                        <ul class="list-group list-group-flush">${items}</ul>
                    </div>
                    <div class="card-footer bg-white small text-muted">
                        <i class="bi bi-calendar me-1"></i>${fecha}
                    </div>
                </div>
            </div>`;
    });

    main.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0"><i class="bi bi-list-check me-2 text-proesa"></i>Mis Pedidos</h5>
            <button class="btn btn-proesa btn-sm" onclick="showNuevoPedido()">
                <i class="bi bi-plus-lg me-1"></i>Nuevo
            </button>
        </div>
        <div class="row">${cards}</div>`;
}

// ═══════════════════════════════
//  VIEW: Aprobar (Leader)
// ═══════════════════════════════

async function showAprobar() {
    setActiveNav('showAprobar');
    const main = document.getElementById('mainContent');
    main.innerHTML = '<div class="spinner-proesa"><div class="spinner-border text-primary"></div></div>';

    let snap;
    try {
        snap = await db.collection('pedidos')
            .where('area', '==', currentUser.area)
            .where('estado', '==', 'pendiente')
            .get();
    } catch (e) {
        main.innerHTML = `<div class="alert alert-danger">Error al cargar: ${e.message}</div>`;
        console.error('showAprobar error:', e);
        return;
    }

    if (snap.empty) {
        main.innerHTML = `<div class="empty-state">
            <i class="bi bi-check-circle"></i>
            <h5>Sin pedidos pendientes</h5>
            <p>No hay pedidos por aprobar en tu area</p></div>`;
        return;
    }

    // Sort by date descending in JS
    const pedidosAprobar = [];
    snap.forEach(d => pedidosAprobar.push({ id: d.id, ...d.data() }));
    pedidosAprobar.sort((a, b) => (b.fecha?.toMillis() || 0) - (a.fecha?.toMillis() || 0));

    let cards = '';
    pedidosAprobar.forEach(p => {
        const fecha = p.fecha ? p.fecha.toDate().toLocaleDateString('es-MX') : '';
        const items = (p.detalles || []).map(i =>
            `<tr><td>${i.nombre}</td><td class="text-center">${i.unidad}</td><td class="text-center">${i.cantidad}</td></tr>`
        ).join('');

        cards += `
            <div class="col-lg-6 mb-3">
                <div class="card card-proesa">
                    <div class="card-header card-header-proesa d-flex justify-content-between">
                        <span><i class="bi bi-person me-1"></i>${p.nombreEmpleado}</span>
                        <small>${fecha}</small>
                    </div>
                    <div class="card-body p-0">
                        <table class="table table-sm mb-0">
                            <thead><tr><th>Producto</th><th class="text-center">UM</th><th class="text-center">Cant.</th></tr></thead>
                            <tbody>${items}</tbody>
                        </table>
                    </div>
                    <div class="card-footer bg-white d-flex gap-2">
                        <button class="btn btn-success btn-sm flex-fill" onclick="aprobarPedido('${p.id}','aprobado_lider')">
                            <i class="bi bi-check-lg me-1"></i>Aprobar
                        </button>
                        <button class="btn btn-danger btn-sm flex-fill" onclick="aprobarPedido('${p.id}','rechazado')">
                            <i class="bi bi-x-lg me-1"></i>Rechazar
                        </button>
                    </div>
                </div>
            </div>`;
    });

    main.innerHTML = `
        <h5 class="mb-3"><i class="bi bi-check2-square me-2 text-proesa"></i>Pedidos por Aprobar - ${currentUser.area}</h5>
        <div class="row">${cards}</div>`;
}

async function aprobarPedido(pedidoId, nuevoEstado) {
    try {
        const updates = { estado: nuevoEstado };
        if (nuevoEstado === 'aprobado_lider') {
            updates.aprobadoPorLider = currentUid;
            updates.nombreLider = currentUser.nombre;
            updates.fechaAprobacionLider = firebase.firestore.FieldValue.serverTimestamp();
        } else if (nuevoEstado === 'aprobado') {
            updates.aprobadoPorAdmin = currentUid;
            updates.nombreAdmin = currentUser.nombre;
            updates.fechaAprobacionAdmin = firebase.firestore.FieldValue.serverTimestamp();
        } else if (nuevoEstado === 'rechazado') {
            if (currentUser.rol === 'lider') {
                updates.aprobadoPorLider = currentUid;
                updates.nombreLider = currentUser.nombre;
            } else {
                updates.aprobadoPorAdmin = currentUid;
                updates.nombreAdmin = currentUser.nombre;
            }
        } else if (nuevoEstado === 'entregado') {
            updates.fechaEntrega = firebase.firestore.FieldValue.serverTimestamp();
        }

        await db.collection('pedidos').doc(pedidoId).update(updates);
        showAlert(nuevoEstado === 'rechazado' ? 'Pedido rechazado' : 'Pedido actualizado', nuevoEstado === 'rechazado' ? 'warning' : 'success');

        // Refresh the current view
        if (currentUser.rol === 'lider') showAprobar();
        else showAdminPedidos();
    } catch (e) {
        showAlert('Error: ' + e.message, 'danger');
    }
}

async function eliminarPedido(pedidoId) {
    if (!confirm('Eliminar este pedido? Esta accion no se puede deshacer.')) return;
    try {
        await db.collection('pedidos').doc(pedidoId).delete();
        showAlert('Pedido eliminado', 'warning');
        showAdminPedidos();
    } catch (e) {
        showAlert('Error: ' + e.message, 'danger');
    }
}

// ═══════════════════════════════
//  VIEW: Admin Pedidos
// ═══════════════════════════════

async function showAdminPedidos(filtro) {
    filtro = filtro || 'por_aprobar';
    setActiveNav('showAdminPedidos');
    const main = document.getElementById('mainContent');
    main.innerHTML = '<div class="spinner-proesa"><div class="spinner-border text-primary"></div></div>';

    let snap;
    try {
        if (filtro === 'por_aprobar') {
            // Admin sees both pendiente and aprobado_lider
            snap = await db.collection('pedidos')
                .where('estado', 'in', ['pendiente', 'aprobado_lider'])
                .get();
        } else if (filtro === 'todos') {
            snap = await db.collection('pedidos').get();
        } else {
            snap = await db.collection('pedidos')
                .where('estado', '==', filtro)
                .get();
        }
    } catch (e) {
        main.innerHTML = `<div class="alert alert-danger">Error al cargar pedidos: ${e.message}</div>`;
        console.error('showAdminPedidos error:', e);
        return;
    }
    // Sort by date descending in JS
    const adminPedidos = [];
    snap.forEach(d => adminPedidos.push({ id: d.id, ...d.data() }));
    adminPedidos.sort((a, b) => (b.fecha?.toMillis() || 0) - (a.fecha?.toMillis() || 0));

    const filters = [
        { key: 'por_aprobar', label: 'Por Aprobar', icon: 'bi-hourglass-split' },
        { key: 'aprobado', label: 'Aprobados', icon: 'bi-check-circle' },
        { key: 'entregado', label: 'Entregados', icon: 'bi-truck' },
        { key: 'rechazado', label: 'Rechazados', icon: 'bi-x-circle' },
        { key: 'todos', label: 'Todos', icon: 'bi-grid' }
    ];

    const filterBtns = filters.map(f =>
        `<button class="btn btn-sm ${f.key === filtro ? 'btn-proesa' : 'btn-outline-secondary'}"
                 onclick="showAdminPedidos('${f.key}')">
            <i class="bi ${f.icon} me-1"></i>${f.label}
        </button>`
    ).join('');

    if (adminPedidos.length === 0) {
        main.innerHTML = `
            <h5 class="mb-3"><i class="bi bi-clipboard-data me-2 text-proesa"></i>Gestion de Pedidos</h5>
            <div class="filter-tabs d-flex flex-wrap gap-2 mb-3">${filterBtns}</div>
            <div class="empty-state"><i class="bi bi-inbox"></i><h5>Sin pedidos</h5></div>`;
        return;
    }

    let rows = '';
    adminPedidos.forEach(p => {
        const fecha = p.fecha ? p.fecha.toDate().toLocaleDateString('es-MX') : '';
        const totalItems = (p.detalles || []).reduce((s, i) => s + i.cantidad, 0);
        const itemsList = (p.detalles || []).map(i => `${i.nombre} (${i.cantidad})`).join(', ');

        let actions = '';
        if (p.estado === 'pendiente' || p.estado === 'aprobado_lider') {
            actions = `
                <button class="btn btn-success btn-sm me-1" onclick="aprobarPedido('${p.id}','aprobado')" title="Aprobar">
                    <i class="bi bi-check-lg"></i>
                </button>
                <button class="btn btn-danger btn-sm me-1" onclick="aprobarPedido('${p.id}','rechazado')" title="Rechazar">
                    <i class="bi bi-x-lg"></i>
                </button>`;
        } else if (p.estado === 'aprobado') {
            actions = `
                <button class="btn btn-primary btn-sm me-1" onclick="aprobarPedido('${p.id}','entregado')" title="Marcar Entregado">
                    <i class="bi bi-truck"></i>
                </button>`;
        }
        // Admin can always delete any order
        actions += `
            <button class="btn btn-outline-danger btn-sm" onclick="eliminarPedido('${p.id}')" title="Eliminar">
                <i class="bi bi-trash"></i>
            </button>`;

        rows += `
            <tr>
                <td><strong>#${p.id.slice(-5).toUpperCase()}</strong></td>
                <td>${p.nombreEmpleado}</td>
                <td>${p.area}</td>
                <td><small>${itemsList}</small></td>
                <td class="text-center">${totalItems}</td>
                <td class="text-center">${badgeEstado(p.estado)}</td>
                <td>${fecha}</td>
                <td class="text-center">${actions}</td>
            </tr>`;
    });

    main.innerHTML = `
        <h5 class="mb-3"><i class="bi bi-clipboard-data me-2 text-proesa"></i>Gestion de Pedidos</h5>
        <div class="filter-tabs d-flex flex-wrap gap-2 mb-3">${filterBtns}</div>
        <div class="card card-proesa">
            <div class="table-responsive">
                <table class="table table-proesa table-hover mb-0">
                    <thead><tr>
                        <th>ID</th><th>Empleado</th><th>Area</th><th>Productos</th>
                        <th class="text-center">Cant.</th><th class="text-center">Estado</th>
                        <th>Fecha</th><th class="text-center">Acciones</th>
                    </tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </div>`;
}

// ═══════════════════════════════
//  VIEW: Exportar Excel
// ═══════════════════════════════

async function showExportar() {
    setActiveNav('showExportar');
    const main = document.getElementById('mainContent');
    main.innerHTML = '<div class="spinner-proesa"><div class="spinner-border text-primary"></div></div>';

    let snap;
    try {
        snap = await db.collection('pedidos')
            .where('estado', '==', 'aprobado')
            .get();
    } catch (e) {
        main.innerHTML = `<div class="alert alert-danger">Error al cargar: ${e.message}</div>`;
        console.error('showExportar error:', e);
        return;
    }

    // Sort by date descending in JS
    const exportPedidos = [];
    snap.forEach(d => exportPedidos.push({ id: d.id, ...d.data() }));
    exportPedidos.sort((a, b) => (b.fecha?.toMillis() || 0) - (a.fecha?.toMillis() || 0));

    if (exportPedidos.length === 0) {
        main.innerHTML = `<div class="empty-state">
            <i class="bi bi-file-earmark-excel"></i>
            <h5>Sin pedidos aprobados</h5>
            <p>No hay pedidos listos para exportar</p></div>`;
        return;
    }

    let rows = '';
    exportPedidos.forEach(p => {
        const fecha = p.fecha ? p.fecha.toDate().toLocaleDateString('es-MX') : '';
        const items = (p.detalles || []).map(i => `${i.nombre} (${i.cantidad})`).join(', ');

        rows += `
            <tr>
                <td class="text-center">
                    <input type="checkbox" class="form-check-input export-check" value="${p.id}"
                           data-detalles='${JSON.stringify(p.detalles || [])}'>
                </td>
                <td><strong>#${p.id.slice(-5).toUpperCase()}</strong></td>
                <td>${p.nombreEmpleado}</td>
                <td>${p.area}</td>
                <td><small>${items}</small></td>
                <td>${fecha}</td>
            </tr>`;
    });

    main.innerHTML = `
        <h5 class="mb-3"><i class="bi bi-file-earmark-excel me-2 text-proesa"></i>Exportar a Excel</h5>
        <div class="card card-proesa mb-3">
            <div class="card-body">
                <div class="row align-items-end">
                    <div class="col-md-6 mb-2">
                        <label class="form-label fw-bold">No. Inventario</label>
                        <input type="text" id="noInventario" class="form-control"
                               placeholder="Ej: GA-GE-OF-00008" value="GA-GE-OF-00008">
                    </div>
                    <div class="col-md-6 mb-2">
                        <button class="btn btn-proesa" onclick="descargarExcel()">
                            <i class="bi bi-download me-2"></i>Descargar Excel
                        </button>
                        <button class="btn btn-outline-secondary ms-2" onclick="toggleAllExport()">
                            <i class="bi bi-check2-all me-1"></i>Seleccionar Todos
                        </button>
                    </div>
                </div>
            </div>
        </div>
        <div class="card card-proesa">
            <div class="table-responsive">
                <table class="table table-proesa table-hover mb-0">
                    <thead><tr>
                        <th class="text-center"><input type="checkbox" class="form-check-input" onchange="toggleAllExport(this.checked)"></th>
                        <th>ID</th><th>Empleado</th><th>Area</th><th>Productos</th><th>Fecha</th>
                    </tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </div>`;
}

function toggleAllExport(checked) {
    const state = checked !== undefined ? checked : true;
    document.querySelectorAll('.export-check').forEach(cb => cb.checked = state);
}

async function descargarExcel() {
    const noInv = document.getElementById('noInventario').value.trim() || 'SIN-NUMERO';
    const checked = document.querySelectorAll('.export-check:checked');

    if (checked.length === 0) {
        showAlert('Selecciona al menos un pedido', 'warning');
        return;
    }

    // Consolidate items across selected orders
    const consolidated = {};
    checked.forEach(cb => {
        const detalles = JSON.parse(cb.dataset.detalles);
        detalles.forEach(item => {
            const key = item.nombre;
            if (!consolidated[key]) {
                consolidated[key] = { nombre: item.nombre, unidad: item.unidad, cantidad: 0 };
            }
            consolidated[key].cantidad += item.cantidad;
        });
    });

    // Create workbook with ExcelJS (supports styling)
    const wb = new ExcelJS.Workbook();
    const ws = wb.addWorksheet('Pedido Proveedor');

    // Column widths
    ws.columns = [
        { header: 'No. Inventario', key: 'inv', width: 20 },
        { header: 'Descripcion de Linea', key: 'desc', width: 38 },
        { header: 'UM', key: 'um', width: 14 },
        { header: 'Cant. Orden', key: 'cant', width: 14 }
    ];

    // Style header row — blue background (#1A5276), white bold text
    const headerRow = ws.getRow(1);
    headerRow.eachCell(cell => {
        cell.fill = {
            type: 'pattern',
            pattern: 'solid',
            fgColor: { argb: 'FF1A5276' }
        };
        cell.font = {
            color: { argb: 'FFFFFFFF' },
            bold: true,
            size: 11
        };
        cell.alignment = { horizontal: 'center', vertical: 'middle' };
        cell.border = {
            top:    { style: 'thin', color: { argb: 'FF0E3650' } },
            bottom: { style: 'thin', color: { argb: 'FF0E3650' } },
            left:   { style: 'thin', color: { argb: 'FF0E3650' } },
            right:  { style: 'thin', color: { argb: 'FF0E3650' } }
        };
    });
    headerRow.height = 22;

    // Add data rows
    Object.values(consolidated).forEach(item => {
        const row = ws.addRow({
            inv: noInv,
            desc: item.nombre,
            um: item.unidad,
            cant: item.cantidad
        });
        row.eachCell(cell => {
            cell.border = {
                top:    { style: 'thin', color: { argb: 'FFD4D4D4' } },
                bottom: { style: 'thin', color: { argb: 'FFD4D4D4' } },
                left:   { style: 'thin', color: { argb: 'FFD4D4D4' } },
                right:  { style: 'thin', color: { argb: 'FFD4D4D4' } }
            };
            cell.alignment = { vertical: 'middle' };
        });
    });

    // Download
    const buffer = await wb.xlsx.writeBuffer();
    const fecha = new Date().toISOString().slice(0, 10);
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    saveAs(blob, `PROESA_Pedido_${fecha}.xlsx`);

    showAlert(`Excel descargado con ${Object.keys(consolidated).length} productos`, 'success');

    // Mark as exported (entregado)
    checked.forEach(async cb => {
        await db.collection('pedidos').doc(cb.value).update({
            estado: 'entregado',
            noInventario: noInv,
            fechaEntrega: firebase.firestore.FieldValue.serverTimestamp()
        });
    });
}

// ═══════════════════════════════
//  VIEW: Historial por Area
// ═══════════════════════════════

async function showHistorial() {
    setActiveNav('showHistorial');
    const main = document.getElementById('mainContent');
    main.innerHTML = '<div class="spinner-proesa"><div class="spinner-border text-primary"></div></div>';

    let snap;
    try {
        snap = await db.collection('pedidos').get();
    } catch (e) {
        main.innerHTML = `<div class="alert alert-danger">Error al cargar historial: ${e.message}</div>`;
        return;
    }

    const pedidos = [];
    snap.forEach(d => pedidos.push({ id: d.id, ...d.data() }));

    // ── Stats by area ──
    const porArea = {};
    AREAS.forEach(a => {
        porArea[a] = { total: 0, aprobados: 0, rechazados: 0, pendientes: 0, entregados: 0, articulos: 0, productos: {} };
    });

    pedidos.forEach(p => {
        const area = p.area;
        if (!porArea[area]) {
            porArea[area] = { total: 0, aprobados: 0, rechazados: 0, pendientes: 0, entregados: 0, articulos: 0, productos: {} };
        }
        porArea[area].total++;
        if (p.estado === 'aprobado' || p.estado === 'entregado') porArea[area].aprobados++;
        if (p.estado === 'rechazado') porArea[area].rechazados++;
        if (p.estado === 'pendiente' || p.estado === 'aprobado_lider') porArea[area].pendientes++;
        if (p.estado === 'entregado') porArea[area].entregados++;

        (p.detalles || []).forEach(item => {
            porArea[area].articulos += item.cantidad;
            if (!porArea[area].productos[item.nombre]) {
                porArea[area].productos[item.nombre] = 0;
            }
            porArea[area].productos[item.nombre] += item.cantidad;
        });
    });

    // ── Global stats ──
    const totalPedidos = pedidos.length;
    const totalArticulos = pedidos.reduce((s, p) => s + (p.detalles || []).reduce((ss, i) => ss + i.cantidad, 0), 0);
    const totalEntregados = pedidos.filter(p => p.estado === 'entregado').length;
    const totalPendientes = pedidos.filter(p => p.estado === 'pendiente' || p.estado === 'aprobado_lider').length;

    // ── KPI cards ──
    const kpis = `
        <div class="row mb-4">
            <div class="col-6 col-md-3 mb-2">
                <div class="card card-proesa text-center p-3">
                    <div class="fs-2 fw-bold text-proesa">${totalPedidos}</div>
                    <small class="text-muted">Total Pedidos</small>
                </div>
            </div>
            <div class="col-6 col-md-3 mb-2">
                <div class="card card-proesa text-center p-3">
                    <div class="fs-2 fw-bold" style="color:var(--proesa-success)">${totalEntregados}</div>
                    <small class="text-muted">Entregados</small>
                </div>
            </div>
            <div class="col-6 col-md-3 mb-2">
                <div class="card card-proesa text-center p-3">
                    <div class="fs-2 fw-bold" style="color:var(--proesa-warning)">${totalPendientes}</div>
                    <small class="text-muted">Pendientes</small>
                </div>
            </div>
            <div class="col-6 col-md-3 mb-2">
                <div class="card card-proesa text-center p-3">
                    <div class="fs-2 fw-bold text-proesa">${totalArticulos}</div>
                    <small class="text-muted">Total Articulos</small>
                </div>
            </div>
        </div>`;

    // ── Area cards ──
    let areaCards = '';
    for (const [area, stats] of Object.entries(porArea)) {
        if (stats.total === 0) continue;

        // Top 5 products for this area
        const topProds = Object.entries(stats.productos)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5);

        const topList = topProds.map(([nombre, cant]) =>
            `<div class="d-flex justify-content-between py-1 border-bottom" style="border-color:#eee!important">
                <span class="small">${nombre}</span>
                <span class="badge bg-secondary">${cant}</span>
            </div>`
        ).join('');

        // Bar widths for visual
        const maxPedidos = Math.max(...Object.values(porArea).map(s => s.total));
        const barWidth = Math.round((stats.total / maxPedidos) * 100);

        areaCards += `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card card-proesa h-100">
                    <div class="card-header card-header-proesa">
                        <i class="bi bi-building me-2"></i>${area}
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <span class="fw-bold">${stats.total} pedidos</span>
                            <span class="small text-muted">${stats.articulos} articulos</span>
                        </div>
                        <div class="progress mb-3" style="height:8px">
                            <div class="progress-bar" style="width:${barWidth}%;background:var(--proesa-blue)"></div>
                        </div>
                        <div class="d-flex gap-2 mb-3 flex-wrap">
                            <span class="badge badge-aprobado"><i class="bi bi-check me-1"></i>${stats.aprobados}</span>
                            <span class="badge badge-pendiente"><i class="bi bi-clock me-1"></i>${stats.pendientes}</span>
                            <span class="badge badge-rechazado"><i class="bi bi-x me-1"></i>${stats.rechazados}</span>
                            <span class="badge badge-entregado"><i class="bi bi-truck me-1"></i>${stats.entregados}</span>
                        </div>
                        <h6 class="small fw-bold text-muted mb-1">Mas solicitados:</h6>
                        ${topList || '<span class="small text-muted">Sin productos</span>'}
                    </div>
                </div>
            </div>`;
    }

    if (!areaCards) {
        areaCards = `<div class="col-12">
            <div class="empty-state">
                <i class="bi bi-bar-chart-line"></i>
                <h5>Sin historial</h5>
                <p>Aun no hay pedidos registrados</p>
            </div>
        </div>`;
    }

    // ── Top products global ──
    const globalProds = {};
    pedidos.forEach(p => {
        (p.detalles || []).forEach(item => {
            if (!globalProds[item.nombre]) globalProds[item.nombre] = 0;
            globalProds[item.nombre] += item.cantidad;
        });
    });
    const topGlobal = Object.entries(globalProds)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    let topGlobalRows = '';
    if (topGlobal.length > 0) {
        const maxCant = topGlobal[0][1];
        topGlobalRows = topGlobal.map(([nombre, cant], i) => {
            const pct = Math.round((cant / maxCant) * 100);
            return `
                <tr>
                    <td class="text-center">${i + 1}</td>
                    <td>${nombre}</td>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <div class="progress flex-fill" style="height:6px">
                                <div class="progress-bar" style="width:${pct}%;background:var(--proesa-blue)"></div>
                            </div>
                            <strong>${cant}</strong>
                        </div>
                    </td>
                </tr>`;
        }).join('');
    }

    main.innerHTML = `
        <h5 class="mb-3"><i class="bi bi-bar-chart-line me-2 text-proesa"></i>Historial por Area</h5>
        ${kpis}
        <div class="row">${areaCards}</div>
        ${topGlobal.length > 0 ? `
        <div class="card card-proesa mt-3">
            <div class="card-header card-header-proesa">
                <i class="bi bi-trophy me-2"></i>Top 10 Productos Mas Solicitados
            </div>
            <div class="table-responsive">
                <table class="table table-hover mb-0">
                    <thead><tr><th class="text-center" style="width:50px">#</th><th>Producto</th><th style="width:40%">Cantidad</th></tr></thead>
                    <tbody>${topGlobalRows}</tbody>
                </table>
            </div>
        </div>` : ''}`;
}

// ═══════════════════════════════
//  VIEW: Catalogo (Admin)
// ═══════════════════════════════

async function showCatalogo() {
    setActiveNav('showCatalogo');
    const main = document.getElementById('mainContent');
    main.innerHTML = '<div class="spinner-proesa"><div class="spinner-border text-primary"></div></div>';

    const snap = await db.collection('productos').get();
    const productos = {};
    snap.forEach(d => {
        const p = { id: d.id, ...d.data() };
        if (!productos[p.categoria]) productos[p.categoria] = [];
        productos[p.categoria].push(p);
    });

    let tables = '';
    for (const [cat, items] of Object.entries(productos)) {
        const rows = items.map(p => `
            <tr class="${!p.activo ? 'table-secondary text-muted' : ''}">
                <td>${p.nombre}</td>
                <td class="text-center">${p.unidad}</td>
                <td class="text-center">
                    <span class="badge ${p.activo ? 'bg-success' : 'bg-secondary'}">
                        ${p.activo ? 'Activo' : 'Inactivo'}
                    </span>
                </td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-${p.activo ? 'warning' : 'success'}"
                            onclick="toggleProducto('${p.id}', ${!p.activo})">
                        <i class="bi bi-${p.activo ? 'pause' : 'play'}"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger ms-1"
                            onclick="deleteProducto('${p.id}', '${p.nombre}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>`).join('');

        tables += `
            <div class="card card-proesa mb-3">
                <div class="card-header bg-white fw-bold">
                    <i class="bi bi-tag me-2 text-proesa"></i>${cat}
                    <span class="badge bg-secondary ms-1">${items.length}</span>
                </div>
                <div class="table-responsive">
                    <table class="table table-sm table-hover mb-0">
                        <thead><tr><th>Producto</th><th class="text-center">Unidad</th><th class="text-center">Estado</th><th class="text-center">Acciones</th></tr></thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>
            </div>`;
    }

    main.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0"><i class="bi bi-box-seam me-2 text-proesa"></i>Catalogo de Productos</h5>
            <button class="btn btn-proesa btn-sm" onclick="showAddProductForm()">
                <i class="bi bi-plus-lg me-1"></i>Agregar Producto
            </button>
        </div>
        <div id="addProductForm" class="d-none"></div>
        ${tables}`;
}

function showAddProductForm() {
    const form = document.getElementById('addProductForm');
    const cats = Object.keys(PRODUCTOS);
    const options = cats.map(c => `<option value="${c}">${c}</option>`).join('');

    form.classList.remove('d-none');
    form.innerHTML = `
        <div class="card card-proesa mb-3">
            <div class="card-body">
                <div class="row g-2 align-items-end">
                    <div class="col-md-4">
                        <label class="form-label small fw-bold">Nombre</label>
                        <input type="text" id="newProdNombre" class="form-control form-control-sm" placeholder="Ej: Boligrafo verde">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small fw-bold">Categoria</label>
                        <select id="newProdCat" class="form-select form-select-sm">${options}</select>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small fw-bold">Unidad</label>
                        <select id="newProdUM" class="form-select form-select-sm">
                            <option>Pieza</option><option>Caja</option><option>Paquete</option><option>Par</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <button class="btn btn-success btn-sm w-100" onclick="agregarProducto()">
                            <i class="bi bi-plus-lg me-1"></i>Agregar
                        </button>
                    </div>
                </div>
            </div>
        </div>`;
}

async function agregarProducto() {
    const nombre = document.getElementById('newProdNombre').value.trim();
    const cat    = document.getElementById('newProdCat').value;
    const um     = document.getElementById('newProdUM').value;

    if (!nombre) { showAlert('Ingresa el nombre del producto', 'warning'); return; }

    await db.collection('productos').add({
        nombre: nombre, categoria: cat, unidad: um, activo: true
    });
    showAlert(`${nombre} agregado al catalogo`, 'success');
    showCatalogo();
}

async function toggleProducto(id, newState) {
    await db.collection('productos').doc(id).update({ activo: newState });
    showCatalogo();
}

async function deleteProducto(id, nombre) {
    if (!confirm(`Eliminar "${nombre}" del catalogo?`)) return;
    await db.collection('productos').doc(id).delete();
    showAlert(`${nombre} eliminado`, 'warning');
    showCatalogo();
}

// ═══════════════════════════════
//  VIEW: Usuarios (Admin)
// ═══════════════════════════════

async function showUsuarios() {
    setActiveNav('showUsuarios');
    const main = document.getElementById('mainContent');
    main.innerHTML = '<div class="spinner-proesa"><div class="spinner-border text-primary"></div></div>';

    const snap = await db.collection('usuarios').orderBy('nombre').get();

    let cards = '';
    snap.forEach(d => {
        const u = d.data();
        const rolBadge = u.rol === 'admin' ? 'bg-danger' : u.rol === 'lider' ? 'bg-primary' : 'bg-secondary';

        cards += `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card card-proesa user-card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="mb-1">${u.nombre}</h6>
                                <small class="text-muted">${u.usuario || u.email}</small>
                            </div>
                            <span class="badge ${rolBadge}">${u.rol}</span>
                        </div>
                        <div class="mt-2">
                            <small><i class="bi bi-building me-1"></i>${u.area}</small>
                        </div>
                    </div>
                    ${u.rol !== 'admin' ? `
                    <div class="card-footer bg-white">
                        <button class="btn btn-outline-danger btn-sm" onclick="deleteUsuario('${d.id}', '${u.nombre}')">
                            <i class="bi bi-trash me-1"></i>Eliminar
                        </button>
                    </div>` : ''}
                </div>
            </div>`;
    });

    // Area options
    const areaOpts = AREAS.map(a => `<option value="${a}">${a}</option>`).join('');

    main.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0"><i class="bi bi-people me-2 text-proesa"></i>Usuarios del Sistema</h5>
            <button class="btn btn-proesa btn-sm" onclick="toggleUserForm()">
                <i class="bi bi-person-plus me-1"></i>Nuevo Usuario
            </button>
        </div>

        <div id="userFormDiv" class="d-none mb-3">
            <div class="card card-proesa">
                <div class="card-header card-header-proesa">
                    <i class="bi bi-person-plus me-2"></i>Crear Usuario
                </div>
                <div class="card-body">
                    <div class="row g-2">
                        <div class="col-md-3">
                            <label class="form-label small fw-bold">Nombre completo</label>
                            <input type="text" id="newUserNombre" class="form-control form-control-sm" placeholder="Maria Garcia">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label small fw-bold">Usuario</label>
                            <input type="text" id="newUserUser" class="form-control form-control-sm" placeholder="mgarcia">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label small fw-bold">Contrasena</label>
                            <input type="password" id="newUserPass" class="form-control form-control-sm" placeholder="Min 6 chars">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label small fw-bold">Rol</label>
                            <select id="newUserRol" class="form-select form-select-sm">
                                <option value="empleado">Empleado</option>
                                <option value="lider">Lider</option>
                                <option value="admin">Admin</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label small fw-bold">Area</label>
                            <select id="newUserArea" class="form-select form-select-sm">${areaOpts}</select>
                        </div>
                    </div>
                    <button class="btn btn-success btn-sm mt-3" onclick="crearUsuario()">
                        <i class="bi bi-check-lg me-1"></i>Crear Usuario
                    </button>
                    <button class="btn btn-outline-secondary btn-sm mt-3 ms-2" onclick="toggleUserForm()">Cancelar</button>
                </div>
            </div>
        </div>

        <div class="row">${cards}</div>`;
}

function toggleUserForm() {
    document.getElementById('userFormDiv').classList.toggle('d-none');
}

async function crearUsuario() {
    const nombre = document.getElementById('newUserNombre').value.trim();
    const user   = document.getElementById('newUserUser').value.trim();
    const pass   = document.getElementById('newUserPass').value;
    const rol    = document.getElementById('newUserRol').value;
    const area   = document.getElementById('newUserArea').value;

    if (!nombre || !user || pass.length < 6) {
        showAlert('Completa todos los campos (contrasena min 6 caracteres)', 'warning');
        return;
    }

    try {
        const email = `${user}@proesa.app`;
        // Use secondary app to create user without logging out admin
        const cred = await secondaryAuth.createUserWithEmailAndPassword(email, pass);

        await db.collection('usuarios').doc(cred.user.uid).set({
            nombre: nombre,
            usuario: user,
            email: email,
            rol: rol,
            area: area,
            activo: true,
            creadoEn: firebase.firestore.FieldValue.serverTimestamp()
        });

        // Sign out from secondary app
        await secondaryAuth.signOut();

        showAlert(`Usuario "${nombre}" creado como ${rol}`, 'success');
        showUsuarios();
    } catch (e) {
        showAlert('Error al crear usuario: ' + e.message, 'danger');
    }
}

async function deleteUsuario(uid, nombre) {
    if (!confirm(`Eliminar usuario "${nombre}"? El usuario ya no podra acceder al sistema.`)) return;

    await db.collection('usuarios').doc(uid).delete();
    showAlert(`Usuario ${nombre} eliminado del sistema`, 'warning');
    showUsuarios();
}

// ═══════════════════════════════
//  HELPERS
// ═══════════════════════════════

function badgeEstado(estado) {
    const map = {
        pendiente:      { clase: 'badge-pendiente',      texto: 'Pendiente' },
        aprobado_lider: { clase: 'badge-aprobado-lider',  texto: 'Aprobado Lider' },
        aprobado:       { clase: 'badge-aprobado',        texto: 'Aprobado' },
        rechazado:      { clase: 'badge-rechazado',       texto: 'Rechazado' },
        entregado:      { clase: 'badge-entregado',       texto: 'Entregado' }
    };
    const b = map[estado] || { clase: 'bg-secondary', texto: estado };
    return `<span class="badge ${b.clase}">${b.texto}</span>`;
}

// Text helper for PROESA blue
document.addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style');
    style.textContent = '.text-proesa { color: #1a5276 !important; }';
    document.head.appendChild(style);
});
