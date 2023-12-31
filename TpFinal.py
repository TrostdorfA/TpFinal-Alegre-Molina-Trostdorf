import datetime
from fastapi import FastAPI, Request, Form, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
import sqlite3
from sqlite3 import Error
import subprocess
import threading
import hashlib
import secrets

app = FastAPI()
conn = sqlite3.connect('tareas.db', check_same_thread=False)
cursor = conn.cursor()

class ConnectionPool:
    def __init__(self, max_connections):
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()

    def get_connection(self):
        with self.lock:
            if len(self.connections) < self.max_connections:
                connection = sqlite3.connect("tareas.db")
                self.connections.append(connection)
            else:
                connection = self.connections.pop(0)
            return connection

    def release_connection(self, connection):
        with self.lock:
            self.connections.append(connection)


pool = ConnectionPool(max_connections=10)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.connection = pool.get_connection()
    response = await call_next(request)
    pool.release_connection(request.state.connection)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=400, content={"message": "Validation error"})


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})

# Creacion de tablas en base de datos
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tareas (
        uid INTEGER PRIMARY KEY,
        titulo string,
        descripcion string,
        estado string,
        creada datetime,
        actualizada datetime
    )
''')
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        apellido TEXT,
        fecha_nacimiento TEXT,
        dni TEXT,
        contraseña TEXT,
        ultimo_acceso TEXT DEFAULT NULL
    )
''')

# Contraseña de administrador
contraseña_admin = hashlib.md5("12345".encode()).hexdigest()

# Verificar si el usuario administrador ya existe en la base de datos
cursor.execute("SELECT * FROM usuarios WHERE nombre = ?", ("Admin",))
existing_user = cursor.fetchone()

if existing_user is None:

    cursor.execute('''
        INSERT INTO usuarios (nombre, apellido, fecha_nacimiento, dni, contraseña, ultimo_acceso)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("Admin", "Admin", "2000-01-01", "123456789", contraseña_admin, None))
    conn.commit()


class Persona:
    def __init__(self, id, nombre, apellido, fecha_nacimiento, dni):
        self.id = id
        self.nombre = nombre
        self.apellido = apellido
        self.fecha_nacimiento = fecha_nacimiento
        self.dni = dni


class Usuario(Persona):
    def __init__(self, id, nombre, apellido, fecha_nacimiento, dni, contraseña):
        super().__init__(id, nombre, apellido, fecha_nacimiento, dni)
        self.contraseña = hashlib.md5(contraseña.encode()).hexdigest()
        self.ultimo_acceso = None

    def registrar_acceso(self):
        self.ultimo_acceso = datetime.datetime.now()


class Tarea:
    def __init__(self, uid, titulo, descripcion, estado, creada, actualizada):
        self.uid = uid
        self.titulo = titulo
        self.descripcion = descripcion
        self.estado = estado
        self.creada = creada
        self.actualizada = actualizada


class AdminTarea:
    @staticmethod
    def agregar_tarea(titulo, descripcion, estado, creada, actualizada):
        cursor.execute(
            "INSERT INTO tareas (titulo, descripcion, estado, creada, actualizada) VALUES (?, ?, ?, ?, ?)",
            (titulo, descripcion, estado, creada, actualizada)
        )
        conn.commit()
        print("Tarea agregada con éxito!")

    @staticmethod
    def actualizar_estado(uid, estado):
        cursor.execute(
            "UPDATE tareas SET estado = ?, actualizada = ? WHERE uid = ?",
            (estado, datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), uid)
        )
        conn.commit()
        print("Tarea actualizada con éxito!")

    @staticmethod
    def eliminar_tarea(uid):
        cursor.execute("DELETE FROM tareas WHERE uid = ?", (uid,))
        conn.commit()

    @staticmethod
    def eliminar_todas_las_tareas():
        cursor.execute("DELETE FROM tareas")
        conn.commit()
        print("Todas las tareas han sido eliminadas con éxito!")

    @staticmethod
    def __traer_tarea__(uid):
        cursor.execute("SELECT * FROM tareas WHERE uid = ?", (uid,))
        tarea_db = cursor.fetchone()
        if tarea_db is not None:
            tarea = Tarea(
                tarea_db[0],  # uid
                tarea_db[1],  # titulo
                tarea_db[2],  # descripcion
                tarea_db[3],  # estado
                tarea_db[4],  # creada
                tarea_db[5],  # actualizada
            )
            return tarea
        else:
            return None

    @staticmethod
    def __traer_todas_tareas__():
        cursor.execute("SELECT * FROM tareas")
        tareas_db = cursor.fetchall()
        tareas = []
        for tarea in tareas_db:
            tareas.append({
                "uid": tarea[0],
                "titulo": tarea[1],
                "descripcion": tarea[2],
                "estado": tarea[3],
                "creada": tarea[4],
                "actualizada": tarea[5]
            })
        return tareas

# Genera el token para el usuario logueado
def generate_token(username):
    token = secrets.token_hex(16)
    return f"{username}:{token}"

# Envia actualizacion de todas las tareas
@app.get("/")
def read_root(request: Request):
    tareas = AdminTarea.__traer_todas_tareas__()
    return JSONResponse(content={"tareas": tareas})

# Verifica credenciales del usuario y le da un token
@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    cursor.execute("SELECT * FROM usuarios WHERE nombre = ?", (username,))
    user = cursor.fetchone()

    if user is None:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    hashed_password = hashlib.md5(password.encode()).hexdigest()

    if user[5] != hashed_password:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token = generate_token(user[0])
    response = JSONResponse({"token": access_token})

    response.set_cookie(key="nombre", value=user[1])
    response.set_cookie(key="password", value=user[5])

    update_query = "UPDATE usuarios SET ultimo_acceso = ? WHERE nombre = ?"
    current_datetime = datetime.datetime.now()
    cursor.execute(update_query, (current_datetime, username))
    conn.commit()

    return response

# Recibe los datos de la tarea a agregar y la guarda en la base de datos
@app.post("/agregar")
def agregar_tarea(request: Request, tarea: dict):
    titulo = tarea.get("titulo")
    descripcion = tarea.get("descripcion")
    estado = tarea.get("estado")
    creada = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    actualizada = creada
    AdminTarea.agregar_tarea(titulo, descripcion, estado, creada, actualizada)

# Recibe uid de tarea a eliminar y la elimina de la base de datos
@app.get("/eliminar/{uid}")
def eliminar_tarea(uid: int):
    AdminTarea.eliminar_tarea(uid)
    return {"success": True}

# Recibe llamada y elimina todas las tareas de la base de datos
@app.get("/eliminar-todas")
def eliminar_todas_tareas():
    AdminTarea.eliminar_todas_las_tareas()
    return {"success": True}

# Recibe uid y estado de la tarea a actualizar y la actualiza en la base de datos
@app.get("/actualizar/{uid}")
def actualizar_estado(uid: int, estado: str = Query(...)):
    AdminTarea.actualizar_estado(uid, estado)
    return {"success": True}

# Recibe uid y busca y devuelve la tarea de la base de datos
@app.get("/buscar/{uid}")
def buscar_tarea(uid: int):
    tarea = AdminTarea.__traer_tarea__(uid)
    if tarea is not None:
        return {"tarea": tarea}
    else:
        return {"tarea": None}

# Inicia el servidor uvicorn para la API
def iniciar_servidor():
    global proceso_servidor
    proceso_servidor = subprocess.Popen(
        ["python", "-m", "uvicorn", "TpFinal:app", "--reload"])