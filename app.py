from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from datetime import datetime
from io import BytesIO
from flask import send_file
import tempfile
from flask import send_from_directory
from datetime import datetime 


# --- Inicialización de la app y configuración ---
app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

# Configuración
REPORTES_FOLDER = os.path.join(os.path.dirname(__file__), 'reportes')
os.makedirs(REPORTES_FOLDER, exist_ok=True)


# --- Inicializar la base de datos ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Tabla de administradores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Tabla de observaciones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS observaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        estado TEXT DEFAULT 'Sin iniciar',
        responsable TEXT,
        fecha_inicio TEXT,
        avance TEXT DEFAULT '0%',
        inversion TEXT,
        recursos TEXT,
        ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
    # Tabla de reportes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER NOT NULL,
            nombre_archivo TEXT NOT NULL,
            ruta_archivo TEXT NOT NULL,
            fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tipo TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
        )
    ''')
    # Tabla de carreras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carreras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            codigo TEXT NOT NULL UNIQUE
        )
    ''')

    # Tabla de grupos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grupos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            carrera_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            codigo TEXT NOT NULL UNIQUE,
            FOREIGN KEY (carrera_id) REFERENCES carreras (id)
        )
    ''')

    # Tabla de alumnos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alumnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grupo_id INTEGER NOT NULL,
            matricula TEXT NOT NULL UNIQUE,
            apellidos TEXT NOT NULL,
            nombre TEXT NOT NULL,
            FOREIGN KEY (grupo_id) REFERENCES grupos (id)
        )
    ''')

    # Tabla de asistencias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asistencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grupo_id INTEGER NOT NULL,
            fecha DATE NOT NULL,
            FOREIGN KEY (grupo_id) REFERENCES grupos (id),
            UNIQUE(grupo_id, fecha)
        )
    ''')

    # Tabla de detalle_asistencias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detalle_asistencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asistencia_id INTEGER NOT NULL,
            alumno_id INTEGER NOT NULL,
            presente BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY (asistencia_id) REFERENCES asistencias (id),
            FOREIGN KEY (alumno_id) REFERENCES alumnos (id),
            UNIQUE(asistencia_id, alumno_id)
        )
    ''')

    # Insertar datos iniciales
    insertar_datos_iniciales(cursor)

        # Crear admin por defecto
    cursor.execute('''
        INSERT OR IGNORE INTO admin (username, password)
        VALUES (?, ?)
    ''', ('ADMIN', generate_password_hash('Admin123!')))
    
    cursor.execute('SELECT COUNT(*) FROM proyectos')
    if cursor.fetchone()[0] == 0:
        proyectos_base = [
            (1, 'Bomba/Sistema de Riego', 'Sistema de riego automatizado para el invernadero'),
            (2, 'Hidroponía', 'Cultivo de plantas usando soluciones minerales en lugar de suelo agrícola'),
            (3, 'Composta', 'Producción de abono orgánico'),
            (4, 'Germinación', 'Proceso de desarrollo de plantas a partir de semillas'),
            (5, 'Iluminación', 'Sistema de iluminación para el invernadero'),
            (6, 'Hotel de Insectos', 'Estructura para albergar insectos beneficiosos'),
            (7, 'Producto Pomada', 'Elaboración de pomadas con plantas medicinales'),
            (8, 'Eólico', 'Sistema de energía eólica para el invernadero'),
            (9, 'Mantenimiento', 'Mantenimiento general del invernadero')
        ]
        cursor.executemany('''
            INSERT INTO proyectos (id, nombre, descripcion)
            VALUES (?, ?, ?)
        ''', proyectos_base)

    conn.commit()
    conn.close()
    
    



def insertar_datos_iniciales(cursor):
    # Insertar carreras
    carreras = [
        ('Ingeniería en Software', 'IS'),
        ('Ingeniería en Manufactura', 'ITM'),
        ('Ingeniería Mecánica A', 'IMA')
    ]
    cursor.executemany('INSERT OR IGNORE INTO carreras (nombre, codigo) VALUES (?, ?)', carreras)

    # Obtener IDs de carreras
    cursor.execute('SELECT id, codigo FROM carreras')
    carrera_ids = {codigo: id for id, codigo in cursor.fetchall()}

    # Insertar grupos
    grupos = [
        (carrera_ids['IS'], '1925° IS - INGENIERÍA DE SOFTWARE', 'IS-1925'),
        (carrera_ids['IS'], '2925° IS - INGENIERÍA DE SOFTWARE', 'IS-2925'),
        (carrera_ids['IS'], '3925° IS - INGENIERÍA DE SOFTWARE', 'IS-3925'),
        (carrera_ids['ITM'], '1625° ITM - Ingeniería en Manufactura', 'ITM-1625'),
        (carrera_ids['ITM'], '1325° ITM - Ingeniería en Manufactura', 'ITM-1325'),
        (carrera_ids['ITM'], '2326° ITM - Ingeniería en Manufactura', 'ITM-2326'),
        (carrera_ids['IMA'], '1925° IMA - Ingeniería Mecánica A', 'IMA-1925'),
        (carrera_ids['IMA'], '2325° IMA - Ingeniería Mecánica A', 'IMA-2325'),
        (carrera_ids['IMA'], '3325° IMA - Ingeniería Mecánica A', 'IMA-3325')
    ]
    cursor.executemany('INSERT OR IGNORE INTO grupos (carrera_id, nombre, codigo) VALUES (?, ?, ?)', grupos)

    # Ejemplo de alumnos (puedes borrar esto o usarlo para pruebas)
    cursor.execute('SELECT id FROM grupos WHERE codigo = "IS-1925"')
    grupo_id = cursor.fetchone()[0]
    
    alumnos_ejemplo = [
        (grupo_id, 'A12345', 'Pérez', 'Juan'),
        (grupo_id, 'A54321', 'García', 'María')
    ]
    cursor.executemany('INSERT OR IGNORE INTO alumnos (grupo_id, matricula, apellidos, nombre) VALUES (?, ?, ?, ?)', alumnos_ejemplo)
    
    
init_db()

# --- Rutas ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().upper()
        password = request.form.get('password', '')

        if not username or not password:
            flash("Por favor, completa todos los campos.", "warning")
            return render_template('login.html')

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, password FROM admin WHERE username = ?', (username,))
        admin = cursor.fetchone()
        conn.close()
        
        if admin and check_password_hash(admin[1], password):
            session['admin_id'] = admin[0]
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Acceso denegado. Credenciales incorrectas.", "danger")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        flash("Inicia sesión para acceder.", "warning")
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/asistencia')
def asistencia():
    if 'admin_id' not in session:
        flash("Acceso restringido. Inicia sesión.", "warning")
        return redirect(url_for('login'))
    return render_template('asistencia.html')

@app.route('/proyectos')
def proyectos():
    if 'admin_id' not in session:
        flash("Acceso restringido. Inicia sesión.", "warning")
        return redirect(url_for('login'))
    
    # Obtener todos los proyectos de la base de datos
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        proyectos = conn.execute('SELECT * FROM proyectos ORDER BY id').fetchall()
    
    return render_template('proyectos.html', proyectos=proyectos)

@app.route('/reportes')
def reportes():
    if 'admin_id' not in session:
        flash("Acceso restringido. Inicia sesión.", "warning")
        return redirect(url_for('login'))
    
    # Obtener todos los reportes
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        reportes = conn.execute('''
            SELECT r.*, p.nombre as proyecto_nombre 
            FROM reportes r
            JOIN proyectos p ON r.proyecto_id = p.id
            ORDER BY r.fecha_generacion DESC
        ''').fetchall()
    
    return render_template('reportes.html', reportes=reportes)

@app.route('/observaciones', methods=['GET', 'POST'])
def observaciones():
    if 'admin_id' not in session:
        flash("Acceso restringido. Inicia sesión.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        texto = request.form.get('observacion', '').strip()
        if texto:
            with sqlite3.connect('database.db') as conn:
                conn.execute('INSERT INTO observaciones (texto, fecha) VALUES (?, datetime("now"))', (texto,))
            flash("Observación guardada correctamente.", "success")
            return redirect(url_for('observaciones'))

    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        observaciones = conn.execute('SELECT texto, fecha FROM observaciones ORDER BY fecha DESC').fetchall()

    return render_template('observaciones.html', observaciones=observaciones)



@app.route('/get-proyecto/<int:proyecto_id>')
def get_proyecto(proyecto_id):
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        proyecto = conn.execute('''
            SELECT id, nombre, descripcion, estado, responsable, 
                   fecha_inicio, avance, inversion, recursos 
            FROM proyectos WHERE id = ?
        ''', (proyecto_id,)).fetchone()
    
    if proyecto:
        return jsonify(dict(proyecto))
    return jsonify({"error": "Proyecto no encontrado"}), 404

@app.route('/actualizar-proyecto/<int:proyecto_id>', methods=['POST'])
def actualizar_proyecto(proyecto_id):
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({"success": False, "error": "Datos no proporcionados"}), 400
        
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            
            # Construir la consulta dinámicamente
            set_clause = ', '.join([f"{key} = ?" for key in datos.keys()])
            valores = list(datos.values())
            valores.append(proyecto_id)
            
            cursor.execute(
                f"UPDATE proyectos SET {set_clause} WHERE id = ?",
                valores
            )
            
            conn.commit()
            return jsonify({"success": True})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route('/generar-reporte/<int:proyecto_id>')
def generar_reporte(proyecto_id):
    try:
        # 1. Obtener datos del proyecto
        with sqlite3.connect('database.db') as conn:
            conn.row_factory = sqlite3.Row
            proyecto = conn.execute('SELECT * FROM proyectos WHERE id = ?', (proyecto_id,)).fetchone()
        
        if not proyecto:
            return jsonify({"success": False, "error": "Proyecto no encontrado"}), 404

        # 2. Crear archivo de reporte (ejemplo en texto plano)
        nombre_archivo = f"reporte_{proyecto['nombre']}_{datetime.now().strftime('%Y%m%d')}.txt"
        ruta_archivo = os.path.join(REPORTES_FOLDER, nombre_archivo)
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(f"Reporte del proyecto: {proyecto['nombre']}\n")
            f.write(f"Estado: {proyecto['estado']}\n")
            f.write(f"Avance: {proyecto['avance']}\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 3. Registrar en BD
        with sqlite3.connect('database.db') as conn:
            conn.execute('''
                INSERT INTO reportes (proyecto_id, nombre_archivo, ruta_archivo, tipo)
                VALUES (?, ?, ?, ?)
            ''', (proyecto_id, nombre_archivo, ruta_archivo, 'texto'))
            conn.commit()

        # 4. Devolver el archivo para descarga
        return send_from_directory(
            directory=REPORTES_FOLDER,
            path=nombre_archivo,
            as_attachment=True
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route('/eliminar-reporte/<int:reporte_id>', methods=['DELETE'])
def eliminar_reporte(reporte_id):
    try:
        # Primero obtenemos la ruta para borrar el archivo
        with sqlite3.connect('database.db') as conn:
            conn.row_factory = sqlite3.Row
            reporte = conn.execute('SELECT ruta_archivo FROM reportes WHERE id = ?', (reporte_id,)).fetchone()
            
            if reporte:
                # Eliminar archivo físico
                if os.path.exists(reporte['ruta_archivo']):
                    os.remove(reporte['ruta_archivo'])
                
                # Eliminar registro de BD
                conn.execute('DELETE FROM reportes WHERE id = ?', (reporte_id,))
                conn.commit()
                return jsonify({"success": True})
            
            return jsonify({"success": False, "error": "Reporte no encontrado"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/api/carreras/<int:carrera_id>/grupos')
def get_grupos_carrera(carrera_id):
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        grupos = conn.execute('''
            SELECT * FROM grupos 
            WHERE carrera_id = ?
            ORDER BY nombre
        ''', (carrera_id,)).fetchall()
    return jsonify([dict(grupo) for grupo in grupos])



# API para obtener información del usuario
@app.route('/api/user-info')
def get_user_info():
    if 'admin_id' not in session:
        return jsonify({"error": "No autenticado"}), 401
    
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        user = conn.execute('SELECT username FROM admin WHERE id = ?', (session['admin_id'],)).fetchone()
    
    return jsonify({
        "username": user['username'],
        "nombre": user['username']  # Puedes añadir más campos si los tienes
    })

# API para obtener carreras y grupos
# Obtener todas las carreras
@app.route('/api/carreras')
def get_carreras():
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        carreras = conn.execute('SELECT * FROM carreras ORDER BY nombre').fetchall()
    return jsonify([dict(carrera) for carrera in carreras])

# Obtener grupos por carrera
@app.route('/api/grupos/<int:carrera_id>')
def get_grupos(carrera_id):
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        grupos = conn.execute('''
            SELECT * FROM grupos 
            WHERE carrera_id = ?
            ORDER BY nombre
        ''', (carrera_id,)).fetchall()
    return jsonify([dict(grupo) for grupo in grupos])

# Obtener alumnos por grupo
@app.route('/api/alumnos/<int:grupo_id>')
def get_alumnos(grupo_id):
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        alumnos = conn.execute('''
            SELECT * FROM alumnos 
            WHERE grupo_id = ?
            ORDER BY apellidos, nombre
        ''', (grupo_id,)).fetchall()
    return jsonify([dict(alumno) for alumno in alumnos])

# Añadir nuevo alumno
@app.route('/api/alumnos', methods=['POST'])
def add_alumno():
    data = request.get_json()
    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alumnos (grupo_id, matricula, apellidos, nombre)
                VALUES (?, ?, ?, ?)
            ''', (data['grupo_id'], data['matricula'], data['apellidos'], data['nombre']))
            conn.commit()
        return jsonify({"success": True, "id": cursor.lastrowid})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "Matrícula ya existe"}), 400

# Eliminar alumno
@app.route('/api/alumnos/<int:alumno_id>', methods=['DELETE'])
def delete_alumno(alumno_id):
    try:
        with sqlite3.connect('database.db') as conn:
            conn.execute('DELETE FROM alumnos WHERE id = ?', (alumno_id,))
            conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Ruta para guardar asistencia
@app.route('/api/guardar-asistencia', methods=['POST'])
def guardar_asistencia():
    try:
        data = request.get_json()
        
        # Aquí iría la lógica para guardar en la base de datos
        print("Datos recibidos para guardar:", data)
        
        return jsonify({
            "success": True,
            "message": "Asistencia guardada correctamente"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Ruta para obtener historial
@app.route('/api/historial-asistencia')
def obtener_historial():
    carrera = request.args.get('carrera')
    grupo = request.args.get('grupo')
    
    # Datos de ejemplo - en producción vendrían de la BD
    historial = [
        {
            "id": 1,
            "fecha": "2024-05-01",
            "carrera": carrera,
            "grupo": grupo,
            "presentes": 15,
            "total": 20,
            "porcentaje": 75
        }
    ]
    
    return jsonify(historial)

# Ruta para generar PDF
@app.route('/generar-pdf-asistencia/<int:asistencia_id>')
def generar_pdf_asistencia(asistencia_id):
    # Datos de ejemplo
    data = {
        "fecha": "2024-05-01",
        "carrera": "Ingeniería en Software",
        "grupo": "1925° IS",
        "presentes": 15,
        "total": 20,
        "porcentaje": 75,
        "alumnos": [
            {"matricula": "A123", "nombre": "Juan Pérez", "asistencia": True},
            {"matricula": "A456", "nombre": "María García", "asistencia": False}
        ]
    }
    
    # En producción usarías ReportLab o similar para generar PDF
    # Esto es un ejemplo que devuelve HTML como PDF
    from flask import make_response
    html = render_template('pdf_asistencia.html', **data)
    response = make_response(html)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=asistencia_{asistencia_id}.pdf'
    return response


@app.route('/lista-asistencia')
def lista_asistencia():
    # Obtener parámetros de la URL
    grupo_id = request.args.get('grupo_id')  # Cambiado para coincidir con el JS
    fecha = request.args.get('fecha')
    
    if not grupo_id or not fecha:
        flash("Faltan parámetros necesarios", "error")
        return redirect(url_for('asistencia'))
    
    # Obtener datos del grupo y alumnos desde la BD
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        
        # Obtener información del grupo
        grupo = conn.execute('''
            SELECT g.*, c.nombre as carrera_nombre 
            FROM grupos g
            JOIN carreras c ON g.carrera_id = c.id
            WHERE g.id = ?
        ''', (grupo_id,)).fetchone()
        
        # Obtener alumnos del grupo
        alumnos = conn.execute('''
            SELECT * FROM alumnos 
            WHERE grupo_id = ?
            ORDER BY apellidos, nombre
        ''', (grupo_id,)).fetchall()
    
    if not grupo:
        flash("Grupo no encontrado", "error")
        return redirect(url_for('asistencia'))
    
    return render_template(
        'lista_asistencia.html',
        grupo=dict(grupo),
        alumnos=[dict(a) for a in alumnos],
        fecha=fecha
    )

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
