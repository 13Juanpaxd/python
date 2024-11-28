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
        dsn='localhost:1521/xe',
        encoding='UTF-8'
    )
    return connection

@app.route('/', methods=['GET', 'POST'])
def login():
    """
    Esta función maneja la lógica de inicio de sesión.

    Permite a los usuarios iniciar sesión como administradores o usuarios regulares.
    Verifica las credenciales ingresadas y redirige al usuario a la página correspondiente.
    """

    if request.method == 'POST':
        # Obtener los datos del formulario
        correo = request.form['correo']
        cedula = request.form['cedula']

        # Verificar si es un administrador
        if correo == 'ADMIN@ADMIN.AD' and cedula == '987654321':
            # Inicio de sesión exitoso para administrador
            session['user_id'] = 1  # Reemplaza 1 con el ID real del administrador en tu base de datos
            session['is_admin'] = True
            return redirect(url_for('index'))  # Redirigir al panel de administrador

        # Verificar si es un usuario regular
        else:
            # Conectar a la base de datos y buscar al usuario
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT ID_Cliente FROM FIDE_CLIENTES_TB WHERE Correo = :correo AND Cedula = :cedula', {'correo': correo, 'cedula': cedula})
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            # Si se encontró al usuario, iniciar sesión
            if user:
                session['user_id'] = user[0]
                session['is_admin'] = False
                return redirect(url_for('home'))  # Redirigir a la página principal del usuario

            # Si no se encontró al usuario, mostrar un mensaje de error
            else:
                flash('Correo o cédula incorrectos. Inténtelo de nuevo.')

    # Mostrar el formulario de inicio de sesión
    return render_template('login.html')
@app.route('/home')
def home():
    return render_template('home.html')

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
    try:
        cursor.execute('SELECT Imagen FROM FIDE_INVENTARIO_TB WHERE ID_Producto = :producto_id', {'producto_id': producto_id})
        row = cursor.fetchone()
        if row and row[0]:
            response = make_response(row[0].read())
            # Ajusta el tipo de contenido según el formato de tu imagen (por ejemplo, JPEG, PNG)
            response.headers.set('Content-Type', 'image/jpeg')
            return response
        else:
            return 'No image found for product ID: {}'.format(producto_id), 404
    except Exception as e:
        print(f"Error fetching image: {str(e)}")
        return 'Error fetching image', 500
    finally:
        cursor.close()
        conn.close()

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
   
@app.route('/envios')
def envios():
    """
    Página de gestión de envíos.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Aquí puedes agregar lógica para obtener envíos desde la base de datos si es necesario
    return render_template('envios.html')  # Asegúrate de tener el archivo envios.html

@app.route('/facturas')
def facturas():
    """
    Página de facturas para el cliente.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Aquí puedes agregar lógica para obtener facturas desde la base de datos si es necesario
    return render_template('facturas.html')  # Asegúrate de tener el archivo facturas.html

@app.route('/encargos', methods=['GET', 'POST'])
def encargos():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirige al login si no hay sesión activa
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            # Datos del formulario
            producto = request.form['producto']
            cantidad = request.form['cantidad']
            detalles = request.form['detalles']
            user_id = session['user_id']

            # Insertar encargo en la base de datos
            cursor.execute("""
                INSERT INTO FIDE_ENCARGOS_TB 
                (ID_Cliente, Producto, Cantidad, Detalles, Fecha_Encargo, Estado) 
                VALUES (:user_id, :producto, :cantidad, :detalles, SYSTIMESTAMP, 'Pendiente')
            """, {
                'user_id': user_id,
                'producto': producto,
                'cantidad': cantidad,
                'detalles': detalles
            })
            conn.commit()
            flash('Encargo realizado con éxito.', 'success')

        # Obtener encargos del usuario
        cursor.execute("""
            SELECT ID_Encargo, Producto, Cantidad, Detalles, Fecha_Encargo, Estado 
            FROM FIDE_ENCARGOS_TB 
            WHERE ID_Cliente = :user_id
        """, {'user_id': session['user_id']})
        encargos = cursor.fetchall()

        return render_template('encargos.html', encargos=encargos)

    except Exception as e:
        print(f"Error: {e}")
        flash('Ocurrió un error al procesar la solicitud.', 'error')
        return render_template('encargos.html', encargos=[])
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/carrito', methods=['GET', 'POST'])
def carrito():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirige al login si no hay sesión activa
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            # Datos del formulario
            producto_id = request.form['producto_id']
            cantidad = request.form['cantidad']
            user_id = session['user_id']

            # Insertar producto en el carrito
            cursor.execute("""
                INSERT INTO FIDE_CARRITO_TB 
                (ID_Cliente, ID_Producto, Cantidad) 
                VALUES (:user_id, :producto_id, :cantidad)
            """, {
                'user_id': user_id,
                'producto_id': producto_id,
                'cantidad': cantidad
            })
            conn.commit()
            flash('Producto añadido al carrito.', 'success')

        # Obtener productos del carrito
        cursor.execute("""
            SELECT c.ID_Producto, i.Nombre, c.Cantidad, i.Precio, (c.Cantidad * i.Precio) AS Total
            FROM FIDE_CARRITO_TB c
            JOIN FIDE_INVENTARIO_TB i ON c.ID_Producto = i.ID_Producto
            WHERE c.ID_Cliente = :user_id
        """, {'user_id': session['user_id']})
        carrito = cursor.fetchall()

        # Calcular el total general
        total = sum(item[4] for item in carrito)

        return render_template('carrito.html', carrito=carrito, total=total)

    except Exception as e:
        print(f"Error: {e}")
        flash('Ocurrió un error al procesar la solicitud.', 'error')
        return render_template('carrito.html', carrito=[], total=0)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == '__main__':
    app.run(debug=True)

