from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import cx_Oracle
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    connection = cx_Oracle.connect(
        user='Proyecto1',
        password='Proyecto1',
        dsn='localhost:1521/XE',
        encoding='UTF-8'
    )
    return connection

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        cedula = request.form['cedula']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT ID_Cliente FROM FIDE_CLIENTES_TB WHERE Correo = :correo AND Cedula = :cedula', {'correo': correo, 'cedula': cedula})
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        else:
            flash('Correo o cédula incorrectos. Inténtelo de nuevo.')
    return render_template('login.html')

@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        cedula = request.form['cedula']
        correo = request.form['correo']
        pais = request.form['pais']
        provincia = request.form['provincia']
        canton = request.form['canton']
        distrito = request.form['distrito']
        foto = request.files['foto']
        foto_blob = foto.read()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO FIDE_CLIENTES_TB 
            (Nombre, Telefono, Cedula, Correo, Pais, Provincia, Canton, Distrito, Foto)
            VALUES (:nombre, :telefono, :cedula, :correo, :pais, :provincia, :canton, :distrito, :foto_blob)
        """, {
            'nombre': nombre,
            'telefono': telefono,
            'cedula': cedula,
            'correo': correo,
            'pais': pais,
            'provincia': provincia,
            'canton': canton,
            'distrito': distrito,
            'foto_blob': foto_blob
        })
        conn.commit()
        cursor.close()
        conn.close()
        flash('Usuario registrado exitosamente. Ahora puede iniciar sesión.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = session['user_id']
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        cedula = request.form['cedula']
        correo = request.form['correo']
        pais = request.form['pais']
        provincia = request.form['provincia']
        canton = request.form['canton']
        distrito = request.form['distrito']
        foto = request.files['foto']
        
        if foto:
            foto_blob = foto.read()
            cursor.execute("""
                UPDATE FIDE_CLIENTES_TB SET 
                Nombre=:nombre, Telefono=:telefono, Cedula=:cedula, Correo=:correo, 
                Pais=:pais, Provincia=:provincia, Canton=:canton, Distrito=:distrito, Foto=:foto_blob 
                WHERE ID_Cliente=:user_id
            """, {
                'nombre': nombre,
                'telefono': telefono,
                'cedula': cedula,
                'correo': correo,
                'pais': pais,
                'provincia': provincia,
                'canton': canton,
                'distrito': distrito,
                'foto_blob': foto_blob,
                'user_id': user_id
            })
        else:
            cursor.execute("""
                UPDATE FIDE_CLIENTES_TB SET 
                Nombre=:nombre, Telefono=:telefono, Cedula=:cedula, Correo=:correo, 
                Pais=:pais, Provincia=:provincia, Canton=:canton, Distrito=:distrito
                WHERE ID_Cliente=:user_id
            """, {
                'nombre': nombre,
                'telefono': telefono,
                'cedula': cedula,
                'correo': correo,
                'pais': pais,
                'provincia': provincia,
                'canton': canton,
                'distrito': distrito,
                'user_id': user_id
            })
        
        conn.commit()
        flash('Información actualizada con éxito.')
    
    cursor.execute('SELECT Nombre, Telefono, Cedula, Correo, Pais, Provincia, Canton, Distrito FROM FIDE_CLIENTES_TB WHERE ID_Cliente = :user_id', {'user_id': user_id})
    user_info = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('profile.html', user_info=user_info)

@app.route('/user_photo/<int:user_id>')
def user_photo(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT Foto FROM FIDE_CLIENTES_TB WHERE ID_Cliente = :user_id', {'user_id': user_id})
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row and row[0]:
        response = make_response(row[0].read())
        response.headers.set('Content-Type', 'image/jpeg')
        return response
    return 'No image found', 404

@app.route('/inventario', methods=['GET', 'POST'])
def inventario():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if request.method == 'POST':
            nombre = request.form['nombre']
            precio = request.form['precio']
            detalle = request.form['detalle']
            cantidad = request.form['cantidad']
            categoria = request.form['categoria']
            proveedor_id = request.form['proveedor_id']
            casillero_id = request.form['casillero_id']
            imagen = request.files['imagen']
            imagen_blob = imagen.read()

            print("Datos recibidos para insertar:")
            print(f"Nombre: {nombre}, Precio: {precio}, Detalle: {detalle}, Cantidad: {cantidad}, Categoría: {categoria}, Proveedor ID: {proveedor_id}, Casillero ID: {casillero_id}, Imagen: {len(imagen_blob)} bytes")

            cursor.execute("""
                INSERT INTO FIDE_INVENTARIO_TB 
                (Nombre, Imagen, Precio, Detalle, Cantidad, Categoria, Proveedor_ID, Casillero_ID, Fecha_Entrada)
                VALUES (:nombre, :imagen_blob, :precio, :detalle, :cantidad, :categoria, :proveedor_id, :casillero_id, SYSTIMESTAMP)
            """, {
                'nombre': nombre,
                'imagen_blob': imagen_blob,
                'precio': precio,
                'detalle': detalle,
                'cantidad': cantidad,
                'categoria': categoria,
                'proveedor_id': proveedor_id,
                'casillero_id': casillero_id
            })
            conn.commit()
            print("Producto insertado correctamente")
        cursor.execute('SELECT ID_Producto, Nombre, Imagen, Precio, Detalle, Cantidad, Categoria, Proveedor_ID, Casillero_ID, Estado_ID, Fecha_Entrada FROM FIDE_INVENTARIO_TB')
        productos = cursor.fetchall()
        print("Productos obtenidos:", productos)
        return render_template('inventario.html', productos=productos)
    except Exception as e:
        print("Error en la operación:", str(e))
    finally:
        cursor.close()
        conn.close()

@app.route('/imagen/<int:producto_id>')
def imagen(producto_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT Imagen FROM FIDE_INVENTARIO_TB WHERE ID_Producto = :producto_id', {'producto_id': producto_id})
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row and row[0]:
        response = make_response(row[0].read())
        response.headers.set('Content-Type', 'image/jpeg')
        return response
    return 'No image found', 404

@app.route('/clientes', methods=['GET', 'POST'])
def clientes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        cedula = request.form['cedula']
        correo = request.form['correo']
        pais = request.form['pais']
        provincia = request.form['provincia']
        canton = request.form['canton']
        distrito = request.form['distrito']
        cursor.execute("""
            INSERT INTO FIDE_CLIENTES_TB 
            (Nombre, Telefono, Cedula, Correo, Pais, Provincia, Canton, Distrito, Estado_ID)
            VALUES (:nombre, :telefono, :cedula, :correo, :pais, :provincia, :canton, :distrito, 1)
        """, {
            'nombre': nombre,
            'telefono': telefono,
            'cedula': cedula,
            'correo': correo,
            'pais': pais,
            'provincia': provincia,
            'canton': canton,
            'distrito': distrito
        })
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('clientes'))

    cursor.execute('SELECT ID_Cliente, Nombre, Telefono, Cedula, Correo, Pais, Provincia, Canton, Distrito, Estado_ID FROM FIDE_CLIENTES_TB')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('clientes.html', rows=rows)

@app.route('/proveedores', methods=['GET', 'POST'])
def proveedores():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre']
        contacto = request.form['contacto']
        telefono = request.form['telefono']
        correo = request.form['correo']
        direccion = request.form['direccion']

        cursor.execute("""
            INSERT INTO FIDE_PROVEEDORES_TB 
            (Nombre, Contacto, Telefono, Correo, Direccion)
            VALUES (:nombre, :contacto, :telefono, :correo, :direccion)
        """, {
            'nombre': nombre,
            'contacto': contacto,
            'telefono': telefono,
            'correo': correo,
            'direccion': direccion
        })
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('proveedores'))

    cursor.execute('SELECT ID_Proveedor, Nombre, Contacto, Telefono, Correo, Direccion FROM FIDE_PROVEEDORES_TB')
    proveedores = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('proveedores.html', proveedores=proveedores)

if __name__ == '__main__':
    app.run(debug=True)
