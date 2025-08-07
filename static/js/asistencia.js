// Variables globales
let carrerasData = [];

// Cuando el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', async () => {
  try {
    // Configurar fecha actual
    document.getElementById('fecha').valueAsDate = new Date();
    
    // Cargar datos del usuario
    await cargarInfoUsuario();
    
    // Cargar carreras desde la API
    await cargarCarreras();
    
    // Configurar eventos
    configurarEventos();
    
  } catch (error) {
    console.error('Error inicial:', error);
    mostrarError('Error al cargar la página');
  }
});

// Configura todos los eventos
function configurarEventos() {
  // Búsqueda de carreras
  document.getElementById('busqueda-carrera').addEventListener('input', filtrarCarreras);
  
  // Botón de ayuda
  document.getElementById('btn-ayuda').addEventListener('click', mostrarAyuda);
  
  // Cerrar modal al hacer clic en la X
  document.querySelector('.cerrar-modal').addEventListener('click', cerrarModal);
}

// Cargar información del usuario
async function cargarInfoUsuario() {
  try {
    const response = await fetch('/api/user-info');
    if (!response.ok) throw new Error('Error al cargar usuario');
    
    const user = await response.json();
    document.getElementById('user-info').textContent = user.nombre || user.username;
  } catch (error) {
    console.error('Error al cargar usuario:', error);
    document.getElementById('user-info').textContent = 'Usuario';
  }
}

// Cargar carreras desde la API
async function cargarCarreras() {
  try {
    const response = await fetch('/api/carreras');
    if (!response.ok) throw new Error('Error al cargar carreras');
    
    carrerasData = await response.json();
    renderizarCarreras(carrerasData);
  } catch (error) {
    console.error('Error al cargar carreras:', error);
    mostrarError('No se pudieron cargar las carreras');
    // Datos de ejemplo en caso de error
    renderizarCarreras([
      {
        id: 'software',
        nombre: 'Ingeniería en Software',
        icono: 'fa-laptop-code',
        grupos: ["1925° IS - INGENIERÍA DE SOFTWARE"]
      }
    ]);
  }
}

// Renderizar las carreras en el DOM
function renderizarCarreras(carreras) {
  const container = document.getElementById('carreras-container');
  container.innerHTML = '';

  if (carreras.length === 0) {
    container.innerHTML = '<p class="no-resultados">No hay carreras disponibles</p>';
    return;
  }

  carreras.forEach(carrera => {
    const card = document.createElement('div');
    card.className = `carrera-card carrera-${carrera.id}`;
    card.innerHTML = `
      <div class="carrera-header" onclick="toggleGrupos('${carrera.id}')">
        <div class="carrera-icon">
          <i class="fas ${carrera.icono}"></i>
        </div>
        <h3 class="carrera-title">${carrera.nombre}</h3>
        <i class="fas fa-chevron-down toggle-icon"></i>
      </div>
      <div class="grupos-container" id="grupos-${carrera.id}"></div>
    `;
    
    container.appendChild(card);
    renderizarGrupos(carrera);
  });
}

// Renderizar los grupos de cada carrera
function renderizarGrupos(carrera) {
  const gruposContainer = document.getElementById(`grupos-${carrera.id}`);
  gruposContainer.innerHTML = '';
  
  carrera.grupos.forEach(grupo => {
    const grupoItem = document.createElement('div');
    grupoItem.className = 'grupo-item';
    grupoItem.innerHTML = `
      <span class="grupo-name">${grupo}</span>
      <button class="grupo-action" 
              onclick="tomarAsistencia('${carrera.id}', '${grupo.replace(/'/g, "\\'")}')">
        Tomar lista
      </button>
    `;
    gruposContainer.appendChild(grupoItem);
  });
}

// Filtrar carreras según búsqueda
function filtrarCarreras() {
  const searchTerm = document.getElementById('busqueda-carrera').value.toLowerCase();
  const filtered = carrerasData.filter(carrera => 
    carrera.nombre.toLowerCase().includes(searchTerm)
  );
  renderizarCarreras(filtered);
}

// Mostrar/ocultar grupos de una carrera
function toggleGrupos(carreraId) {
  const gruposContainer = document.getElementById(`grupos-${carreraId}`);
  const icon = gruposContainer.previousElementSibling.querySelector('.toggle-icon');
  
  gruposContainer.classList.toggle('mostrar');
  icon.classList.toggle('fa-chevron-down');
  icon.classList.toggle('fa-chevron-up');
}

// Función para tomar asistencia
function tomarAsistencia(carreraId, grupo) {
  const fecha = document.getElementById('fecha').value;
  if (!fecha) {
    alert('Por favor selecciona una fecha');
    return;
  }
  
  // Codificar parámetros para URL
  const params = new URLSearchParams({
    carrera: carreraId,
    grupo: grupo,
    fecha: fecha
  });
  
  window.location.href = `/lista-asistencia?${params.toString()}`;
}

// Mostrar modal de ayuda
function mostrarAyuda() {
  document.getElementById('modal-ayuda').style.display = 'block';
}

// Cerrar modal
function cerrarModal() {
  document.getElementById('modal-ayuda').style.display = 'none';
}

// Mostrar mensaje de error
function mostrarError(mensaje) {
  const container = document.getElementById('carreras-container');
  container.innerHTML = `<p class="error-mensaje">${mensaje}</p>`;
}

// Cerrar modal al hacer clic fuera
window.addEventListener('click', (event) => {
  const modal = document.getElementById('modal-ayuda');
  if (event.target === modal) {
    cerrarModal();
  }
});