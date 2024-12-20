from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, jsonify
import cx_Oracle
import os
from flask_mail import Mail, Message
from flask import jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'frikilandplus@gmail.com'  
app.config['MAIL_PASSWORD'] = 'wqgt upzl cuqa jxyf'         
app.config['MAIL_DEFAULT_SENDER'] = 'frikilandplus@gmail.com'

mail = Mail(app)

def get_db_connection():
    connection = cx_Oracle.connect(
        user='ProyectoDefinitivo',
        password='ProyectoDefinitivo',
        dsn='localhost:1521/xe',
        encoding='UTF-8'
    )
    return connection


#############################################################################################################

@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        correo = request.form['correo']
        cedula = request.form['cedula']

        if correo == 'ADMIN@ADMIN.AD' and cedula == '987654321':
            session['user_id'] = 1  
            session['is_admin'] = True
            return redirect(url_for('index'))  

        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT ID_Cliente FROM FIDE_CLIENTES_TB WHERE Correo = :correo AND Cedula = :cedula', {'correo': correo, 'cedula': cedula})
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                session['user_id'] = user[0]
                session['is_admin'] = False
                return redirect(url_for('home'))  

            else:
                flash('Correo o cédula incorrectos. Inténtelo de nuevo.')

    return render_template('login.html')


#############################################################################################################

@app.route('/home')
def home():
    return render_template('home.html')

#############################################################################################################

@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')
    
#############################################################################################################

@app.route('/register', methods=['GET', 'POST'])
def register():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener datos para los dropdowns
    cursor.execute("SELECT ID_Pais, Nombre FROM FIDE_PAIS_TB")
    paises = cursor.fetchall()

    cursor.execute("SELECT ID_Provincia, Nombre FROM FIDE_PROVINCIA_TB")
    provincias = cursor.fetchall()

    cursor.execute("SELECT ID_Canton, Nombre FROM FIDE_CANTON_TB")
    cantones = cursor.fetchall()

    cursor.execute("SELECT ID_Distrito, Nombre FROM FIDE_DISTRITO_TB")
    distritos = cursor.fetchall()

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

        # Verificar si el correo ya existe
        cursor.execute("SELECT COUNT(*) FROM FIDE_CLIENTES_TB WHERE Correo = :correo", {'correo': correo})
        correo_existente = cursor.fetchone()[0]

        if correo_existente > 0:
            flash('El correo ingresado ya está en uso. Por favor, utiliza otro correo.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('register'))

        # Verificar si la cédula ya existe
        cursor.execute("SELECT COUNT(*) FROM FIDE_CLIENTES_TB WHERE Cedula = :cedula", {'cedula': cedula})
        cedula_existente = cursor.fetchone()[0]

        if cedula_existente > 0:
            flash('La cédula ingresada ya está en uso. Por favor, verifica los datos ingresados.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('register'))

        # Insertar el nuevo usuario
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

        # Enviar correo de confirmación
        try:
            msg = Message(
                '¡Registro exitoso!',
                recipients=[correo]
            )
            msg.body = f"Hola {nombre},\n\nGracias por registrarte en Frikiland. Tu usuario ha sido creado exitosamente.\n\n¡Bienvenido!"
            mail.send(msg)
            flash('Usuario registrado exitosamente. Se ha enviado un correo de confirmación.', 'success')
        except Exception as e:
            flash(f'Error al enviar el correo: {str(e)}', 'danger')

        return redirect(url_for('login'))

    return render_template('register.html', paises=paises, provincias=provincias, cantones=cantones, distritos=distritos)

#############################################################
@app.route('/eliminar_producto/<int:producto_id>', methods=['POST'])
def eliminar_producto(producto_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM productos WHERE ID = :producto_id', {'producto_id': producto_id})
    conn.commit()
    cursor.close()
    conn.close()

    flash('Producto eliminado exitosamente.', 'success')
    return redirect(url_for('inventario'))


#############################################################################################################


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        correo = request.form['correo']
        cedula = request.form['cedula']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar si el correo existe
        cursor.execute("SELECT COUNT(*) FROM FIDE_CLIENTES_TB WHERE Correo = :correo", {'correo': correo})
        correo_existente = cursor.fetchone()[0]

        # Verificar si la cédula existe
        cursor.execute("SELECT COUNT(*) FROM FIDE_CLIENTES_TB WHERE Cedula = :cedula", {'cedula': cedula})
        cedula_existente = cursor.fetchone()[0]

        if not correo_existente and not cedula_existente:
            flash('El correo y la cédula ingresados no están registrados.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('login'))

        if not correo_existente:
            flash('El correo ingresado no está registrado.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('login'))

        if not cedula_existente:
            flash('La cédula ingresada no está registrada.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('login'))

        # Validar si el correo y la cédula coinciden
        cursor.execute("""
            SELECT ID_Cliente FROM FIDE_CLIENTES_TB 
            WHERE Correo = :correo AND Cedula = :cedula
        """, {'correo': correo, 'cedula': cedula})
        usuario = cursor.fetchone()

        if usuario:
            # Iniciar sesión
            session['user_id'] = usuario[0]
            flash('Inicio de sesión exitoso. Bienvenido.', 'success')
            cursor.close()
            conn.close()
            return redirect(url_for('home'))
        else:
            flash('El correo y la cédula no coinciden. Por favor, verifica los datos ingresados.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('login'))

    return render_template('login.html')


#############################################################################################################

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

#############################################################################################################

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


#############################################################################################################

@app.route('/mostrar_foto/<int:cliente_id>')
def mostrar_foto(cliente_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Foto FROM FIDE_CLIENTES_TB WHERE ID_Cliente = :cliente_id", {'cliente_id': cliente_id})
        row = cursor.fetchone()
        if row and row[0]:
            response = make_response(row[0].read())
            response.headers.set('Content-Type', 'image/jpeg')
            return response
        else:
            response = requests.get('https://activosyvalores.com/assets/media/media_user/avar_user_default.png')
            return make_response(response.content)
    except Exception as e:
        print(f"Error fetching image: {str(e)}")
        return 'Error fetching image', 500
    finally:
        cursor.close()
        conn.close()


#############################################################################################################

@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = session['user_id']

    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        correo = request.form['correo']
        pais = request.form['pais']
        provincia = request.form['provincia']
        canton = request.form['canton']
        distrito = request.form['distrito']
        foto = request.files['foto']

     
        foto_blob = foto.read() if foto else None

    
        cursor.execute("""
            UPDATE FIDE_CLIENTES_TB
            SET Nombre = :nombre,
                Telefono = :telefono,
                Correo = :correo,
                Pais = :pais,
                Provincia = :provincia,
                Canton = :canton,
                Distrito = :distrito,
                Foto = :foto_blob
            WHERE ID_Cliente = :user_id
        """, {
            'nombre': nombre,
            'telefono': telefono,
            'correo': correo,
            'pais': pais,
            'provincia': provincia,
            'canton': canton,
            'distrito': distrito,
            'foto_blob': foto_blob,
            'user_id': user_id
        })
        conn.commit()

 
        try:
            msg = Message(
                'Actualización de Perfil',
                sender='nicoleobregon198@gmail.com',  
                recipients=[correo]
            )
            msg.body = f"""
            Hola {nombre},

            Tu perfil ha sido actualizado con éxito.

            Si no realizaste esta acción, por favor contáctanos de inmediato.

            Saludos,
            El equipo de Frikiland
            """
            mail.send(msg)
            flash('Perfil actualizado con éxito. Se ha enviado un correo de notificación.', 'success')
        except Exception as e:
            flash(f'Error al enviar el correo: {str(e)}', 'danger')


    cursor.execute("SELECT ID_Pais, Nombre FROM FIDE_PAIS_TB")
    paises = cursor.fetchall()
    cursor.execute("SELECT ID_Provincia, Nombre FROM FIDE_PROVINCIA_TB")
    provincias = cursor.fetchall()
    cursor.execute("SELECT ID_Canton, Nombre FROM FIDE_CANTON_TB")
    cantones = cursor.fetchall()
    cursor.execute("SELECT ID_Distrito, Nombre FROM FIDE_DISTRITO_TB")
    distritos = cursor.fetchall()
    cursor.execute("""
        SELECT Cedula, Nombre, Telefono, Correo, 
            (SELECT Nombre FROM FIDE_PAIS_TB WHERE ID_Pais = c.Pais),
            (SELECT Nombre FROM FIDE_PROVINCIA_TB WHERE ID_Provincia = c.Provincia),
            (SELECT Nombre FROM FIDE_CANTON_TB WHERE ID_Canton = c.Canton),
            (SELECT Nombre FROM FIDE_DISTRITO_TB WHERE ID_Distrito = c.Distrito),
            Foto 
        FROM FIDE_CLIENTES_TB c
        WHERE ID_Cliente = :user_id
    """, {'user_id': user_id})
    cliente = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('perfil.html', paises=paises, provincias=provincias, cantones=cantones, distritos=distritos, cliente=cliente)
#############################################################################################################


@app.route('/actualizar_perfil', methods=['POST'])
def actualizar_perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    nombre = request.form['nombre']
    telefono = request.form['telefono']
    correo = request.form['correo']
    pais = request.form['pais']
    provincia = request.form['provincia']
    canton = request.form['canton']
    distrito = request.form['distrito']
    foto = request.files['foto'].read() if 'foto' in request.files else None

    conn = get_db_connection()
    cursor = conn.cursor()

    if foto:
        cursor.execute("""
            UPDATE FIDE_CLIENTES_TB
            SET Nombre = :nombre, Telefono = :telefono, Correo = :correo, 
                Pais = :pais, Provincia = :provincia, Canton = :canton, 
                Distrito = :distrito, Foto = :foto
            WHERE ID_Cliente = :user_id
        """, {
            'nombre': nombre,
            'telefono': telefono,
            'correo': correo,
            'pais': pais,
            'provincia': provincia,
            'canton': canton,
            'distrito': distrito,
            'foto': foto,
            'user_id': user_id
        })
    else:
        cursor.execute("""
            UPDATE FIDE_CLIENTES_TB
            SET Nombre = :nombre, Telefono = :telefono, Correo = :correo, 
                Pais = :pais, Provincia = :provincia, Canton = :canton, 
                Distrito = :distrito
            WHERE ID_Cliente = :user_id
        """, {
            'nombre': nombre,
            'telefono': telefono,
            'correo': correo,
            'pais': pais,
            'provincia': provincia,
            'canton': canton,
            'distrito': distrito,
            'user_id': user_id
        })

    conn.commit()
    cursor.close()
    conn.close()

    flash('Perfil actualizado con éxito.', 'success')
    return redirect(url_for('perfil'))



#############################################################################################################

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
 


#############################################################################################################

@app.route('/editar_producto/<int:id_producto>', methods=['GET', 'POST'])
def editar_producto(id_producto):
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
            imagen = request.files.get('imagen')
            
            if imagen:
                imagen_blob = imagen.read()
                cursor.execute("""
                    UPDATE FIDE_INVENTARIO_TB
                    SET Nombre = :nombre, Imagen = :imagen_blob, Precio = :precio, 
                        Detalle = :detalle, Cantidad = :cantidad, Categoria = :categoria, 
                        Proveedor_ID = :proveedor_id, Casillero_ID = :casillero_id
                    WHERE ID_Producto = :id_producto
                """, {
                    'nombre': nombre,
                    'imagen_blob': imagen_blob,
                    'precio': precio,
                    'detalle': detalle,
                    'cantidad': cantidad,
                    'categoria': categoria,
                    'proveedor_id': proveedor_id,
                    'casillero_id': casillero_id,
                    'id_producto': id_producto
                })
            else:
                cursor.execute("""
                    UPDATE FIDE_INVENTARIO_TB
                    SET Nombre = :nombre, Precio = :precio, 
                        Detalle = :detalle, Cantidad = :cantidad, Categoria = :categoria, 
                        Proveedor_ID = :proveedor_id, Casillero_ID = :casillero_id
                    WHERE ID_Producto = :id_producto
                """, {
                    'nombre': nombre,
                    'precio': precio,
                    'detalle': detalle,
                    'cantidad': cantidad,
                    'categoria': categoria,
                    'proveedor_id': proveedor_id,
                    'casillero_id': casillero_id,
                    'id_producto': id_producto
                })
            conn.commit()
            return redirect(url_for('inventario'))

        cursor.execute('SELECT * FROM FIDE_INVENTARIO_TB WHERE ID_Producto = :id_producto', {'id_producto': id_producto})
        producto = cursor.fetchone()
        return render_template('editar_producto.html', producto=producto)
    except Exception as e:
        print("Error en la operación:", str(e))
    finally:
        cursor.close()
        conn.close()

#############################################################################################################

@app.route('/imagen/<int:producto_id>')
def imagen(producto_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT Imagen FROM FIDE_INVENTARIO_TB WHERE ID_Producto = :producto_id', {'producto_id': producto_id})
        row = cursor.fetchone()
        if row and row[0]:
            response = make_response(row[0].read())
            
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


#############################################################################################################

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
    
    cursor.execute("""
        SELECT c.ID_Cliente, c.Nombre, c.Telefono, c.Cedula, c.Correo, 
               p.Nombre AS Pais, pr.Nombre AS Provincia, 
               ca.Nombre AS Canton, d.Nombre AS Distrito, c.Estado_ID 
        FROM FIDE_CLIENTES_TB c
        JOIN FIDE_PAIS_TB p ON c.Pais = p.ID_Pais
        JOIN FIDE_PROVINCIA_TB pr ON c.Provincia = pr.ID_Provincia
        JOIN FIDE_CANTON_TB ca ON c.Canton = ca.ID_Canton
        JOIN FIDE_DISTRITO_TB d ON c.Distrito = d.ID_Distrito
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('clientes.html', rows=rows)


#############################################################################################################

@app.route('/proveedores', methods=['GET', 'POST'])
def proveedores():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        detalles = request.form['detalles']

        cursor.execute("""
            INSERT INTO FIDE_PROVEEDORES_TB 
            (Nombre, Detalles)
            VALUES (:nombre, :detalles)
        """, {
            'nombre': nombre,
            'detalles': detalles
        })
        conn.commit()
        flash('Proveedor agregado con éxito', 'success')
    
    cursor.execute('SELECT ID_Proveedor, Nombre, Detalles FROM FIDE_PROVEEDORES_TB')
    proveedores = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('proveedores.html', proveedores=proveedores)


#############################################################################################################

@app.route('/envios')
def envios():
    """
    Página de gestión de envíos.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.ID_Envios, e.Factura_ID, em.EMPRESA, e.Estado 
        FROM FIDE_ENVIOS_TB e
        JOIN FIDE_FACTURA_TB f ON e.Factura_ID = f.ID_Factura
        JOIN FIDE_CLIENTES_TB c ON f.Cliente_ID = c.ID_Cliente
        JOIN FIDE_EMPRESA_ENVIOS_TB em ON e.Empresa_ID = em.ID_MENSAJERO
    """)
    envios = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('envios.html', envios=envios)




#############################################################################################################

@app.route('/facturas')
def facturas():
    """
    Página de facturas para el cliente.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = session['user_id']

    cursor.execute("""
        SELECT f.ID_Factura, m.Descripcion, f.Detalle, f.Total 
        FROM FIDE_FACTURA_TB f
        JOIN FIDE_METODO_PAGO_TB m ON f.Metodo_ID = m.ID_Metodo
        WHERE f.Cliente_ID = :user_id
    """, {'user_id': user_id})
    facturas = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('facturas.html', facturas=facturas)




#############################################################################################################

@app.route('/encargos', methods=['GET', 'POST'])
def encargos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            producto_id = request.form['producto']
            cliente_id = session['user_id']
            plazo = 15  # Plazo fijo de 15 días

            cursor.execute("""
                INSERT INTO FIDE_ENCARGOS_TB 
                (Producto_ID, Cliente_ID, Plazo, Fecha_Inicial, Fecha_Limite) 
                VALUES (:producto_id, :cliente_id, :plazo, SYSTIMESTAMP, SYSTIMESTAMP + NUMTODSINTERVAL(:plazo, 'DAY'))
            """, {
                'producto_id': producto_id,
                'cliente_id': cliente_id,
                'plazo': plazo
            })
            conn.commit()
            flash('Encargo realizado con éxito.', 'success')

        # Obtener el listado de productos para el formulario
        cursor.execute("SELECT ID_Producto, Nombre FROM FIDE_INVENTARIO_TB")
        productos = cursor.fetchall()

        cursor.execute("""
            SELECT i.Nombre, e.Plazo, TO_CHAR(e.Fecha_Inicial, 'YYYY-MM-DD'), TO_CHAR(e.Fecha_Limite, 'YYYY-MM-DD') 
            FROM FIDE_ENCARGOS_TB e
            JOIN FIDE_INVENTARIO_TB i ON e.Producto_ID = i.ID_Producto
            WHERE e.Cliente_ID = :cliente_id
        """, {'cliente_id': session['user_id']})
        encargos = cursor.fetchall()

        return render_template('encargos.html', productos=productos, encargos=encargos)

    except Exception as e:
        print(f"Error: {e}")
        flash('Ocurrió un error al procesar la solicitud.', 'error')
        return render_template('encargos.html', productos=[], encargos=[])
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    

#############################################################################################################

@app.route('/carrito', methods=['GET', 'POST'])
def carrito():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.method == 'POST':
            producto_id = request.form['producto_id']
            cantidad = request.form['cantidad']
            user_id = session['user_id']

            cursor.execute("""
                INSERT INTO FIDE_CARRITO_TB 
                (Cliente_ID, Producto_ID, Cantidad) 
                VALUES (:user_id, :producto_id, :cantidad)
            """, {
                'user_id': user_id,
                'producto_id': producto_id,
                'cantidad': cantidad
            })
            conn.commit()
            flash('Producto añadido al carrito.', 'success')

        cursor.execute("""
            SELECT c.Producto_ID, i.Nombre, c.Cantidad, i.Precio, (c.Cantidad * i.Precio) AS Subtotal
            FROM FIDE_CARRITO_TB c
            JOIN FIDE_INVENTARIO_TB i ON c.Producto_ID = i.ID_Producto
            WHERE c.Cliente_ID = :user_id
        """, {'user_id': session['user_id']})
        carrito = cursor.fetchall()
        print("Productos en el carrito:", carrito)  # Línea de depuración

        total = sum(item[4] for item in carrito)
        print("Total calculado:", total)  # Línea de depuración

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


#############################################################################################################

@app.route('/catalogo', methods=['GET'])
def catalogo():
    """
    Muestra el catálogo de productos desde la base de datos.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT ID_Producto, Nombre, Imagen, Precio, Detalle, Cantidad FROM FIDE_INVENTARIO_TB')
        productos = cursor.fetchall()
        print("Productos obtenidos del catálogo:", productos)  # Línea de depuración

        return render_template('catalogo.html', productos=productos)

    except Exception as e:
        print(f"Error al cargar el catálogo: {e}")
        flash('Error al cargar el catálogo.', 'error')
        return render_template('catalogo.html', productos=[])
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


#############################################################################################################
@app.route('/favoritos', methods=['GET'])
def favoritos():
    if 'user_id' not in session:
        return redirect(url_for('login')) 

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        user_id = session['user_id']
        cursor.execute("""
            SELECT f.Producto_ID, i.Nombre, i.Precio, i.Detalle, i.Imagen
            FROM FIDE_FAVORITO_TB f
            JOIN FIDE_INVENTARIO_TB i ON f.Producto_ID = i.ID_Producto
            WHERE f.Cliente_ID = :user_id
        """, {'user_id': user_id})
        favoritos = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template('favoritos.html', favoritos=favoritos)


#############################################################################################################
@app.route('/agregar_favorito/<int:producto_id>', methods=['POST'])
def agregar_favorito(producto_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))  

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        user_id = session['user_id']

        # Verificar si el producto ya está en favoritos
        cursor.execute("""
            SELECT COUNT(*) 
            FROM FIDE_FAVORITO_TB 
            WHERE Cliente_ID = :user_id AND Producto_ID = :producto_id
        """, {'user_id': user_id, 'producto_id': producto_id})
        count = cursor.fetchone()[0]

        if count == 0:
            cursor.execute("""
                INSERT INTO FIDE_FAVORITO_TB (Cliente_ID, Producto_ID)
                VALUES (:user_id, :producto_id)
            """, {'user_id': user_id, 'producto_id': producto_id})
            conn.commit()
            flash('Producto agregado a favoritos.', 'success')
        else:
            flash('Este producto ya está en tu lista de favoritos.', 'info')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('catalogo'))


#############################################################################################################

@app.route('/eliminar_favorito/<int:producto_id>', methods=['POST'])
def eliminar_favorito(producto_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))  

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        user_id = session['user_id']

        cursor.execute("""
            DELETE FROM FIDE_FAVORITO_TB 
            WHERE Cliente_ID = :user_id AND Producto_ID = :producto_id
        """, {'user_id': user_id, 'producto_id': producto_id})
        conn.commit()
        flash('Producto eliminado de favoritos.', 'success')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('favoritos'))


#############################################################################################################
@app.route('/proveedores', methods=['GET', 'POST'])
def proveedores_view():
    if request.method == 'POST':
        
        id_proveedor = len(proveedores) + 1
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        correo = request.form['correo']
        producto = request.form['producto']
        precio = request.form['precio']
        
        proveedores.append((id_proveedor, nombre, telefono, correo, producto, float(precio)))
        flash('Proveedor agregado correctamente.', 'success')
        return redirect(url_for('proveedores_view'))
    
    return render_template('proveedores.html', proveedores=proveedores)

@app.route('/eliminar_proveedor/<int:proveedor_id>', methods=['POST'])
def eliminar_proveedor(proveedor_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Eliminar el proveedor por su ID
    cursor.execute('DELETE FROM proveedores WHERE ID_Proveedor = :proveedor_id', {'proveedor_id': proveedor_id})
    conn.commit()
    cursor.close()
    conn.close()

    flash('Proveedor eliminado exitosamente.', 'success')
    return redirect(url_for('proveedores'))


#############################################################################################################


#############################################################################################################

@app.route('/agregar_al_carrito/<int:producto_id>', methods=['POST'])
def agregar_al_carrito(producto_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        user_id = session['user_id']
        cantidad = int(request.form.get('cantidad', 1))
        estado_id = 1

        # Obtener el precio del producto para calcular el subtotal
        cursor.execute("SELECT Precio FROM FIDE_INVENTARIO_TB WHERE ID_Producto = :producto_id", {'producto_id': producto_id})
        precio = cursor.fetchone()[0]
        subtotal = precio * cantidad

        cursor.execute("""
            INSERT INTO FIDE_CARRITO_TB 
            (Producto_ID, Cantidad, Subtotal, Cliente_ID) 
            VALUES (:producto_id, :cantidad, :subtotal, :user_id)
        """, {
            'producto_id': producto_id,
            'cantidad': cantidad,
            'subtotal': subtotal,
            'user_id': user_id
        })
        conn.commit()
        flash('Producto añadido al carrito.', 'success')

    except Exception as e:
        print(f"Error al agregar producto al carrito: {e}")
        flash('Ocurrió un error al agregar el producto al carrito.', 'error')

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('catalogo'))


#############################################################################################################

@app.route('/vaciar_carrito', methods=['POST'])
def vaciar_carrito():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        user_id = session['user_id']

        # Eliminar todos los productos del carrito del usuario actual
        cursor.execute("""
            DELETE FROM FIDE_CARRITO_TB WHERE Cliente_ID = :user_id
        """, {'user_id': user_id})
        conn.commit()
        flash('Carrito vaciado con éxito.', 'success')

    except Exception as e:
        print(f"Error al vaciar el carrito: {e}")
        flash('Ocurrió un error al vaciar el carrito.', 'error')

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('carrito'))


#############################################################################################################
@app.route('/eliminar_del_carrito/<int:producto_id>', methods=['POST'])
def eliminar_del_carrito(producto_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        user_id = session['user_id']

        # Eliminar el producto específico del carrito del usuario actual
        cursor.execute("""
            DELETE FROM FIDE_CARRITO_TB WHERE Cliente_ID = :user_id AND Producto_ID = :producto_id
        """, {'user_id': user_id, 'producto_id': producto_id})
        conn.commit()
        flash('Producto eliminado del carrito.', 'success')

    except Exception as e:
        print(f"Error al eliminar producto del carrito: {e}")
        flash('Ocurrió un error al eliminar el producto del carrito.', 'error')

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('carrito'))

#############################################################################################################

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener productos del inventario
    cursor.execute("SELECT ID_Producto, Nombre, Imagen FROM FIDE_INVENTARIO_TB")
    productos = cursor.fetchall()

    # Obtener comentarios para cada producto
    comentarios = {}
    for producto in productos:
        cursor.execute("""
            SELECT f.Comentario, c.Nombre 
            FROM FIDE_FEEDBACK_TB f
            JOIN FIDE_CLIENTES_TB c ON f.Cliente_ID = c.ID_Cliente
            WHERE f.Producto_ID = :producto_id 
            ORDER BY f.ID_Feedback DESC 
            FETCH FIRST 3 ROWS ONLY
        """, {'producto_id': producto[0]})
        comentarios[producto[0]] = [{'comentario': row[0], 'nombre': row[1]} for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return render_template('feedback.html', productos=productos, comentarios=comentarios)

#############################################################################################################

@app.route('/comentar/<int:producto_id>', methods=['POST'])
def comentar(producto_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    comentario = request.form['comentario']
    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO FIDE_FEEDBACK_TB (Cliente_ID, Comentario, Producto_ID)
        VALUES (:cliente_id, :comentario, :producto_id)
    """, {'cliente_id': user_id, 'comentario': comentario, 'producto_id': producto_id})
    conn.commit()

    cursor.close()
    conn.close()

    flash('Comentario añadido con éxito.', 'success')
    return redirect(url_for('feedback'))

#############################################################################################################

@app.route('/ver_mas_comentarios/<int:producto_id>', methods=['GET'])
def ver_mas_comentarios(producto_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener todos los comentarios para el producto
    cursor.execute("""
        SELECT f.Comentario, c.Nombre 
        FROM FIDE_FEEDBACK_TB f
        JOIN FIDE_CLIENTES_TB c ON f.Cliente_ID = c.ID_Cliente
        WHERE f.Producto_ID = :producto_id 
        ORDER BY f.ID_Feedback DESC
    """, {'producto_id': producto_id})
    comentarios = [{'comentario': row[0], 'nombre': row[1]} for row in cursor.fetchall()]

    # Obtener información del producto
    cursor.execute("SELECT Nombre, Imagen FROM FIDE_INVENTARIO_TB WHERE ID_Producto = :producto_id", {'producto_id': producto_id})
    producto = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('ver_mas_comentarios.html', producto=producto, producto_id=producto_id, comentarios=comentarios)



#############################################################################################################

@app.route('/previsualizar_factura', methods=['POST'])
def previsualizar_factura():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    productos = request.form.getlist('productos[]')
    precios = request.form.getlist('precios[]')
    cantidades = request.form.getlist('cantidades[]')
    total = request.form.get('total')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener métodos de pago
    cursor.execute("SELECT ID_Metodo, Descripcion FROM FIDE_METODO_PAGO_TB")
    metodos_pago = cursor.fetchall()

    # Preparar detalles de la factura
    detalle = []
    subtotal = 0
    for i in range(len(productos)):
        subtotal += int(precios[i]) * int(cantidades[i])
        detalle.append({
            'producto': productos[i],
            'precio': precios[i],
            'cantidad': cantidades[i],
            'subtotal': int(precios[i]) * int(cantidades[i])
        })

    iva = subtotal * 0.13
    costo_envio = 1500
    total = subtotal + iva + costo_envio

    cursor.close()
    conn.close()

    return render_template('previsualizar_factura.html', detalle=detalle, subtotal=subtotal, iva=iva, costo_envio=costo_envio, total=total, metodos_pago=metodos_pago)

#############################################################################################################

@app.route('/confirmar_factura', methods=['POST'])
def confirmar_factura():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    metodo_pago = request.form['metodo_pago']
    productos = request.form.getlist('productos[]')
    precios = request.form.getlist('precios[]')
    cantidades = request.form.getlist('cantidades[]')
    subtotal = request.form['subtotal']
    iva = request.form['iva']
    costo_envio = request.form['costo_envio']
    total = request.form['total']

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    detalle = ', '.join(productos)

    cursor.execute("""
        INSERT INTO FIDE_FACTURA_TB (Cliente_ID, Metodo_ID, Detalle, TotalDeLineas, Total, Subtotal, IVA, Costo_Envio)
        VALUES (:cliente_id, :metodo_id, :detalle, :total_lineas, :total, :subtotal, :iva, :costo_envio)
    """, {
        'cliente_id': user_id,
        'metodo_id': metodo_pago,
        'detalle': detalle,
        'total_lineas': len(productos),
        'total': total,
        'subtotal': subtotal,
        'iva': iva,
        'costo_envio': costo_envio
    })
    conn.commit()

    # Vaciar el carrito del usuario
    cursor.execute("""
        DELETE FROM FIDE_CARRITO_TB WHERE Cliente_ID = :user_id
    """, {'user_id': user_id})
    conn.commit()

    cursor.close()
    conn.close()

    flash('Factura confirmada y guardada con éxito. El carrito ha sido vaciado.', 'success')
    return redirect(url_for('facturas'))

#############################################################################################################


@app.route('/enviar_factura/<int:factura_id>', methods=['POST'])
def enviar_factura(factura_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    empresa_id = 1  # ID de la empresa de envíos

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insertar envío
        cursor.execute("""
            INSERT INTO FIDE_ENVIOS_TB (Cliente_ID, Factura_ID, Empresa_ID)
            VALUES (:cliente_id, :factura_id, :empresa_id)
        """, {
            'cliente_id': user_id,
            'factura_id': factura_id,
            'empresa_id': empresa_id
        })
        conn.commit()
        flash('Factura enviada con éxito.', 'success')
    except Exception as e:
        print(f"Error al enviar la factura: {e}")
        flash('Ocurrió un error al enviar la factura.', 'error')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('facturas'))



if __name__ == '__main__':
    app.run(debug=True)