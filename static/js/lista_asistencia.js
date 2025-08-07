// Variables globales
let alumnos = [];
let historial = [];
const params = new URLSearchParams(window.location.search);
const carreraId = params.get('carrera');
const grupoNombre = params.get('grupo');
const fechaAsistencia = params.get('fecha');

// Cuando el DOM esté cargado
document.addEventListener('DOMContentLoaded', () => {
  // Configurar información del grupo
  document.getElementById('carrera-nombre').textContent = obtenerNombreCarrera(carreraId);
  document.getElementById('grupo-nombre').textContent = decodeURIComponent(grupoNombre);
  document.getElementById('fecha-asistencia').textContent = fechaAsistencia;
  document.getElementById('titulo-asistencia').textContent = `Asistencia - ${decodeURIComponent(grupoNombre)}`;

  // Cargar datos iniciales
  cargarAlumnos();
  cargarHistorial();

  // Configurar eventos
  configurarEventos();
});

function configurarEventos() {
  // Botón agregar alumno
  document.getElementById('btn-agregar-alumno').addEventListener('click', mostrarModalAlumno);
  
  // Formulario alumno
  document.getElementById('form-alumno').addEventListener('submit', agregarAlumno);
  
  // Botón guardar asistencia
  document.getElementById('btn-guardar').addEventListener('click', guardarAsistencia);
  
  // Botón ver historial
  document.getElementById('btn-ver-historial').addEventListener('click', mostrarHistorial);
  
  // Botón filtrar historial
  document.getElementById('btn-filtrar-historial').addEventListener('click', filtrarHistorial);
  
  // Cerrar modales
  document.querySelectorAll('.cerrar-modal').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
      });
    });
  });
  
  // Cerrar al hacer clic fuera del modal
  window.addEventListener('click', (event) => {
    if (event.target.classList.contains('modal')) {
      event.target.style.display = 'none';
    }
  });
}

function obtenerNombreCarrera(id) {
  const carreras = {
    'software': 'Ingeniería en Software',
    'manufactura': 'Ingeniería en Manufactura',
    'mecanica': 'Ingeniería Mecánica'
  };
  return carreras[id] || id;
}

async function cargarAlumnos() {
  try {

    alumnos = [
      { id: 1, matricula: 'A12345', nombre: 'Juan Pérez', asistencia: false },
      { id: 2, matricula: 'A67890', nombre: 'María García', asistencia: true }
    ];
    
    renderizarAlumnos();
  } catch (error) {
    console.error('Error al cargar alumnos:', error);
    alert('Error al cargar la lista de alumnos');
  }
}

function renderizarAlumnos() {
  const tbody = document.getElementById('alumnos-lista');
  tbody.innerHTML = '';

  if (alumnos.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="no-alumnos">
          No hay alumnos registrados. Agrega alumnos usando el botón superior.
        </td>
      </tr>
    `;
    return;
  }

  alumnos.forEach((alumno, index) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${alumno.matricula}</td>
      <td>${alumno.nombre}</td>
      <td>
        <label class="switch">
          <input type="checkbox" ${alumno.asistencia ? 'checked' : ''} 
                 data-id="${alumno.id}">
          <span class="slider round"></span>
        </label>
      </td>
      <td>
        <button class="btn-eliminar" data-id="${alumno.id}">
          <i class="fas fa-trash"></i>
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Agregar eventos a los checkboxes
  document.querySelectorAll('#tabla-asistencia input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
      const id = parseInt(e.target.dataset.id);
      const alumno = alumnos.find(a => a.id === id);
      if (alumno) {
        alumno.asistencia = e.target.checked;
      }
    });
  });

  // Agregar eventos a los botones de eliminar
  document.querySelectorAll('.btn-eliminar').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = parseInt(e.currentTarget.dataset.id);
      eliminarAlumno(id);
    });
  });
}

function mostrarModalAlumno() {
  document.getElementById('modal-alumno').style.display = 'block';
  document.getElementById('matricula').focus();
}

function agregarAlumno(e) {
  e.preventDefault();
  
  const matricula = document.getElementById('matricula').value.trim();
  const nombre = document.getElementById('nombre').value.trim();
  
  if (!matricula || !nombre) {
    alert('Por favor completa todos los campos');
    return;
  }

  // Crear nuevo alumno
  const nuevoAlumno = {
    id: alumnos.length > 0 ? Math.max(...alumnos.map(a => a.id)) + 1 : 1,
    matricula,
    nombre,
    asistencia: false
  };

  alumnos.push(nuevoAlumno);
  renderizarAlumnos();
  
  // Limpiar y cerrar modal
  document.getElementById('form-alumno').reset();
  document.getElementById('modal-alumno').style.display = 'none';
  
  alert('Alumno agregado correctamente');
}

function eliminarAlumno(id) {
  if (confirm('¿Estás seguro de eliminar este alumno?')) {
    alumnos = alumnos.filter(a => a.id !== id);
    renderizarAlumnos();
  }
}

async function guardarAsistencia() {
  try {
    // Calcular resumen
    const presentes = alumnos.filter(a => a.asistencia).length;
    const total = alumnos.length;
    const porcentaje = total > 0 ? Math.round((presentes / total) * 100) : 0;
    
    // En una app real, aquí enviarías los datos al servidor
    console.log('Guardando asistencia:', {
      carreraId,
      grupoNombre,
      fechaAsistencia,
      alumnos,
      resumen: { presentes, total, porcentaje }
    });
    
    // Actualizar historial local
    const nuevaAsistencia = {
      id: Date.now(),
      fecha: fechaAsistencia,
      carrera: carreraId,
      grupo: grupoNombre,
      presentes,
      total,
      porcentaje
    };
    
    historial.unshift(nuevaAsistencia);
    
    alert(`Asistencia guardada correctamente\nPresentes: ${presentes}/${total} (${porcentaje}%)`);
    
  } catch (error) {
    console.error('Error al guardar asistencia:', error);
    alert('Error al guardar la asistencia');
  }
}

async function cargarHistorial() {
  try {
    // En una app real, esto vendría de una API
    historial = [
      {
        id: 1,
        fecha: '2024-05-01',
        carrera: carreraId,
        grupo: grupoNombre,
        presentes: 15,
        total: 20,
        porcentaje: 75
      },
      {
        id: 2,
        fecha: '2024-04-28',
        carrera: carreraId,
        grupo: grupoNombre,
        presentes: 18,
        total: 20,
        porcentaje: 90
      }
    ];
    
  } catch (error) {
    console.error('Error al cargar historial:', error);
  }
}

function mostrarHistorial() {
  renderizarHistorial();
  document.getElementById('modal-historial').style.display = 'block';
  
  // Establecer fechas por defecto
  const hoy = new Date().toISOString().split('T')[0];
  document.getElementById('fecha-fin').value = hoy;
  
  const haceUnMes = new Date();
  haceUnMes.setMonth(haceUnMes.getMonth() - 1);
  document.getElementById('fecha-inicio').value = haceUnMes.toISOString().split('T')[0];
}

function renderizarHistorial() {
  const tbody = document.getElementById('historial-lista');
  tbody.innerHTML = '';

  if (historial.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="no-historial">
          No hay registros de asistencia para este grupo.
        </td>
      </tr>
    `;
    return;
  }

  historial.forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${item.fecha}</td>
      <td>${item.presentes}</td>
      <td>${item.total}</td>
      <td>${item.porcentaje}%</td>
      <td>
        <button class="btn-ver" data-id="${item.id}">
          <i class="fas fa-eye"></i> Ver
        </button>
        <button class="btn-pdf" data-id="${item.id}">
          <i class="fas fa-file-pdf"></i> PDF
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Agregar eventos a los botones
  document.querySelectorAll('.btn-ver').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = parseInt(e.currentTarget.dataset.id);
      verDetalleAsistencia(id);
    });
  });

  document.querySelectorAll('.btn-pdf').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = parseInt(e.currentTarget.dataset.id);
      generarPDF(id);
    });
  });
}

function filtrarHistorial() {
  const fechaInicio = document.getElementById('fecha-inicio').value;
  const fechaFin = document.getElementById('fecha-fin').value;
  
  if (!fechaInicio || !fechaFin) {
    alert('Por favor selecciona ambas fechas');
    return;
  }
  
  const filtrado = historial.filter(item => {
    return item.fecha >= fechaInicio && item.fecha <= fechaFin;
  });
  
  // Simula filtrado
  alert(`Mostrando asistencias entre ${fechaInicio} y ${fechaFin}`);
  
}

function verDetalleAsistencia(id) {
  const item = historial.find(h => h.id === id);
  if (item) {
    alert(`Detalles de asistencia del ${item.fecha}\nPresentes: ${item.presentes}/${item.total} (${item.porcentaje}%)`);
  }
}

function generarPDF(id) {
  const item = historial.find(h => h.id === id);
  if (item) {
    
    alert(`Generando PDF para la asistencia del ${item.fecha}`);
    
  }
}