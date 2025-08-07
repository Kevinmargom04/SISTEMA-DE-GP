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
@app.route('/api/carreras')
def get_carreras():
    # Esto es un ejemplo - deberías conectarte a tu base de datos real
    carreras = [
        {
            "id": "software",
            "nombre": "Ingeniería en Software",
            "icono": "fa-laptop-code",
            "grupos": [
                "1925° IS - INGENIERÍA DE SOFTWARE",
                "2925° IS - INGENIERÍA DE SOFTWARE"
            ]
        },
        {
            "id": "manufactura",
            "nombre": "Ingeniería en Manufactura",
            "icono": "fa-industry",
            "grupos": [
                "1625° ITM - Ingeniería en Manufactura"
            ]
        }
    ]
    return jsonify(carreras)

# Ruta para la lista de asistencia
@app.route('/lista-asistencia')
def lista_asistencia():
    carrera = request.args.get('carrera')
    grupo = request.args.get('grupo')
    fecha = request.args.get('fecha')
    
    # Aquí deberías obtener los alumnos del grupo seleccionado
    # Esto es un ejemplo:
    alumnos = [
        {"matricula": "A12345", "nombre": "Juan Pérez", "asistencia": False},
        {"matricula": "A67890", "nombre": "María García", "asistencia": False}
    ]
    
    return render_template('lista_asistencia.html', 
                         carrera=carrera, 
                         grupo=grupo, 
                         fecha=fecha,
                         alumnos=alumnos)   
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

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
