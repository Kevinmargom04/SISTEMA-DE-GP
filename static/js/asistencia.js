document.addEventListener('DOMContentLoaded', async () => {
  try {
    // Configurar fecha actual
    document.getElementById('fecha').valueAsDate = new Date();
    
    // Cargar carreras desde la API
    const response = await fetch('/api/carreras');
    
    if (!response.ok) {
      throw new Error('Error al cargar carreras');
    }
    
    const carreras = await response.json();
    renderizarCarreras(carreras);
    
    // Configurar eventos
    document.getElementById('busqueda-carrera').addEventListener('input', filtrarCarreras);
    document.getElementById('btn-ayuda').addEventListener('click', mostrarAyuda);
    
  } catch (error) {
    console.error('Error:', error);
    mostrarError('Error al cargar las carreras');
  }
});

function renderizarCarreras(carreras) {
  const container = document.getElementById('carreras-container');
  
  if (!carreras || carreras.length === 0) {
    container.innerHTML = '<p class="no-data">No hay carreras disponibles</p>';
    return;
  }

  container.innerHTML = '';
  
  carreras.forEach(carrera => {
    const section = document.createElement('div');
    section.className = 'carrera-section';
    section.innerHTML = `
      <h3 class="carrera-title">
        <i class="fas ${obtenerIconoCarrera(carrera.id)}"></i>
        ${carrera.nombre}
      </h3>
    `;
    
    // Cargar grupos para esta carrera
    cargarGrupos(carrera.id, section);
    
    container.appendChild(section);
  });
}

async function cargarGrupos(carreraId, contenedor) {
  try {
    const response = await fetch(`/api/carreras/${carreraId}/grupos`);
    
    if (!response.ok) {
      throw new Error('Error al cargar grupos');
    }
    
    const grupos = await response.json();
    
    if (grupos.length === 0) {
      contenedor.innerHTML += '<p class="no-groups">No hay grupos para esta carrera</p>';
      return;
    }
    
    grupos.forEach(grupo => {
      const grupoElement = document.createElement('div');
      grupoElement.className = 'grupo-item';
      grupoElement.innerHTML = `
        <span class="grupo-nombre">${grupo.nombre}</span>
        <button class="grupo-action" 
                onclick="window.location.href='/lista-asistencia?grupo_id=${grupo.id}&fecha=${document.getElementById('fecha').value}'">
          Tomar lista
        </button>
      `;
      contenedor.appendChild(grupoElement);
    });
    
  } catch (error) {
    console.error(`Error al cargar grupos para carrera ${carreraId}:`, error);
    contenedor.innerHTML += '<p class="error-grupos">Error al cargar grupos</p>';
  }
}

function obtenerIconoCarrera(carreraId) {
  const iconos = {
    1: 'fa-laptop-code',    // Software
    2: 'fa-industry',       // Manufactura
    3: 'fa-cogs'            // Mecánica
  };
  return iconos[carreraId] || 'fa-graduation-cap';
}

function filtrarCarreras() {
  const termino = document.getElementById('busqueda-carrera').value.toLowerCase();
  const secciones = document.querySelectorAll('.carrera-section');
  
  secciones.forEach(seccion => {
    const titulo = seccion.querySelector('.carrera-title').textContent.toLowerCase();
    seccion.style.display = titulo.includes(termino) ? 'block' : 'none';
  });
}

function mostrarAyuda() {
  alert('Selecciona una carrera y luego un grupo para tomar asistencia. Usa el campo de búsqueda para filtrar carreras.');
}

function mostrarError(mensaje) {
  const container = document.getElementById('carreras-container');
  container.innerHTML = `<p class="error-message">${mensaje}</p>`;
}

function tomarAsistencia(grupo_id) {  // Ahora recibe solo grupo_id
  const fecha = document.getElementById('fecha').value;
  if (!fecha) {
    alert("Por favor selecciona una fecha");
    return;
  }
  window.location.href = `/lista-asistencia?grupo_id=${grupo_id}&fecha=${fecha}`;
}