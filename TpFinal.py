import datetime
import os
from fastapi import FastAPI, Request, Form, Depends, Query, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
import sqlite3
from sqlite3 import Error
import subprocess
import threading
import hashlib

db_path = os.path.join(os.path.dirname(__file__), "tareas.db")


app = FastAPI()
templates = Jinja2Templates(directory="templates")
conn = sqlite3.connect(db_path, check_same_thread=False)
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

contraseña_admin = hashlib.md5("12345".encode()).hexdigest()  # Encriptar la contraseña

# Verificar si el usuario "Admin" ya existe
cursor.execute("SELECT * FROM usuarios WHERE nombre = ?", ("Admin",))
existing_user = cursor.fetchone()

if existing_user is None:
    # El usuario no existe, se puede crear
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
            if tarea is not None:
                tareas.append(Tarea(
                    tarea[0],  # uid
                    tarea[1],  # titulo
                    tarea[2],  # descripcion
                    tarea[3],  # estado
                    tarea[4],  # creada
                    tarea[5],  # actualizada
                ))
            else:
                return None
        return tareas
    
def get_current_user(nombre: str = Cookie(None), contraseña: str = Cookie(None)):
    usuario = Usuario.validar_credenciales(nombre, contraseña)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return usuario

   
@app.get("/")
def read_root(request: Request, usuario: Usuario = Depends(get_current_user)):
    tareas = AdminTarea.__traer_todas_tareas__()
    return templates.TemplateResponse("index.html", {"request": request, "tareas": tareas})

    
@app.get("/tasks")
def get_tasks():
    tareas = AdminTarea.__traer_todas_tareas__()
    return {"tareas": tareas}


@app.post("/agregar")
def agregar_tarea(request: Request, tarea: dict):
    titulo = tarea.get("titulo")
    descripcion = tarea.get("descripcion")
    estado = tarea.get("estado")
    creada = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    actualizada = creada
    AdminTarea.agregar_tarea(titulo, descripcion, estado, creada, actualizada)


@app.get("/eliminar/{uid}")
def eliminar_tarea(uid: int):
    AdminTarea.eliminar_tarea(uid)
    return {"success": True}


@app.get("/eliminar-todas")
def eliminar_todas_tareas():
    AdminTarea.eliminar_todas_las_tareas()
    return {"success": True}


@app.get("/actualizar/{uid}")
def actualizar_estado(uid: int, estado: str= Query(...)):
    AdminTarea.actualizar_estado(uid, estado)
    return {"success": True}


@app.get("/buscar/{uid}")
def buscar_tarea(uid: int):
    tarea = AdminTarea.__traer_tarea__(uid)
    if tarea is not None:
        return {"tarea": tarea}
    else:
        return {"tarea": None}
 
def iniciar_servidor():
    global proceso_servidor 
    proceso_servidor= subprocess.Popen(["uvicorn", "TpFinal:app", "--reload"])