import datetime
from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
import sqlite3
from sqlite3 import Error
import threading


app = FastAPI()
templates = Jinja2Templates(directory="templates")


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

@app.get("/")
async def read_root(request: Request):
    connection = request.state.connection
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM tareas")
    tareas = cursor.fetchall()
    cursor.close()
    return {"tareas": tareas}


conn = sqlite3.connect('tareas.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS tareas (
        uid INTEGER PRIMARY KEY,
        titulo TEXT,
        descripcion TEXT,
        estado TEXT,
        creada TEXT,
        actualizada TEXT,
        eliminada TEXT
    )
''')
conn.commit()


class Tarea:
    def __init__(self, uid, titulo, descripcion, estado, creada, actualizada, eliminada):
        self.uid = uid
        self.titulo = titulo
        self.descripcion = descripcion
        self.estado = estado
        self.creada = creada
        self.actualizada = actualizada
        self.eliminada = eliminada


class AdminTarea:
    @staticmethod
    def agregar_tarea(titulo, descripcion, estado, creada, actualizada, eliminada):
        cursor.execute(
            "INSERT INTO tareas (titulo, descripcion, estado, creada, actualizada, eliminada) VALUES (?, ?, ?, ?, ?, ?)",
            (titulo, descripcion, estado, creada, actualizada, eliminada)
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
        if tarea_db is not None and not tarea_db[6]:
            tarea = Tarea(
                tarea_db[0],  # uid
                tarea_db[1],  # titulo
                tarea_db[2],  # descripcion
                tarea_db[3],  # estado
                tarea_db[4],  # creada
                tarea_db[5],  # actualizada
                tarea_db[6],  # eliminada
            )
            return tarea
        else:
            return None

    @staticmethod
    def __traer_todas_tareas__(eliminada):
        cursor.execute("SELECT * FROM tareas")
        tareas_db = cursor.fetchall()
        tareas = []
        for tarea in tareas_db:
            if eliminada:
                if tarea[6]:
                    tareas.append(Tarea(
                        tarea[0],  # uid
                        tarea[1],  # titulo
                        tarea[2],  # descripcion
                        tarea[3],  # estado
                        tarea[4],  # creada
                        tarea[5],  # actualizada
                        tarea[6],  # eliminada
                    ))
            else:
                if not tarea[6]:
                    tareas.append(Tarea(
                        tarea[0],  # uid
                        tarea[1],  # titulo
                        tarea[2],  # descripcion
                        tarea[3],  # estado
                        tarea[4],  # creada
                        tarea[5],  # actualizada
                        tarea[6],  # eliminada
                    ))
        return tareas
   

@app.get("/")
def read_root(request: Request):
    tareas = AdminTarea.__traer_todas_tareas__(False)
    return templates.TemplateResponse("index.html", {"request": request, "tareas": tareas})


@app.post("/agregar")
def agregar_tarea(request: Request, titulo: str = Form(...), descripcion: str = Form(...)):
    creada = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    actualizada = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    estado = "Pendiente"
    eliminada = ""
    AdminTarea.agregar_tarea(titulo, descripcion, estado, creada, actualizada, eliminada)
    return templates.TemplateResponse("index.html", {"request": request, "tareas": AdminTarea.__traer_todas_tareas__(False)})


@app.get("/eliminar/{uid}")
def eliminar_tarea(request: Request, uid: int):
    AdminTarea.eliminar_tarea(uid)
    return templates.TemplateResponse("index.html", {"request": request, "tareas": AdminTarea.__traer_todas_tareas__(False)})


@app.get("/eliminar-todas")
def eliminar_todas_tareas(request: Request):
    AdminTarea.eliminar_todas_tareas()
    return templates.TemplateResponse("index.html", {"request": request, "tareas": AdminTarea.__traer_todas_tareas__(False)})


@app.get("/actualizar/{uid}")
def actualizar_estado(request: Request, uid: int, estado: str):
    AdminTarea.actualizar_estado(uid, estado)
    return templates.TemplateResponse("index.html", {"request": request, "tareas": AdminTarea.__traer_todas_tareas__(False)})


@app.get("/buscar")
def buscar_tarea(request: Request, uid: int):
    tarea = AdminTarea.__traer_tarea__(uid)
    if tarea is not None:
        return templates.TemplateResponse("index.html", {"request": request, "tareas": [tarea]})
    else:
        return templates.TemplateResponse("index.html", {"request": request, "tareas": []})
 


