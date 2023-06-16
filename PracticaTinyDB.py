from tinydb import TinyDB, Query
import datetime
from os import system
from tabulate import tabulate
from tkinter import messagebox

db=TinyDB('db.json')


class Tarea:
    def __init__(self,uid,titulo,descripcion,estado,creada,actualizada,eliminada):
        self.uid = uid
        self.titulo= titulo
        self.descripcion= descripcion
        self.estado= estado
        self.creada= creada
        self.actualizada= actualizada
        self.eliminada= eliminada

class AdminTarea:
    @staticmethod
    def agregar_tarea(titulo,descripcion,estado,creada,actualizada,eliminada):
        if len(db) == 0:
            max_id = 0
        else:
            max_id = max([tarea['uid'] for tarea in db])
        uid = max_id + 1
        tarea = Tarea(uid, titulo, descripcion, estado, creada, actualizada,eliminada)
        db.insert(tarea.__dict__)
        print("Tarea agregada con exito!")

    @staticmethod
    def actualizar_estado(uid,estado):
        Tarea = Query()
        db.update({'estado': estado, 'actualizada': datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}, Tarea['uid'] == uid)
        print("Tarea actualizada con exito!")

    @staticmethod
    def eliminar_tarea(uid):
        Tarea= Query()
        db.update({'eliminada': True}, Tarea['uid'] == uid)

    @staticmethod
    def eliminar_todas_tareas():
        db.truncate()

    @staticmethod
    def __traer_tarea__(uid,):
        TareaQ=Query()
        tarea_db = db.get(TareaQ.uid==uid)
        if tarea_db is not None and tarea_db['eliminada']==False:
            tarea = Tarea(
                tarea_db['uid'],
                tarea_db['titulo'],
                tarea_db['descripcion'],
                tarea_db['estado'],
                tarea_db['creada'],
                tarea_db['actualizada'],
                   tarea_db['eliminada']
            )
            return tarea
        else:
            return None
    @staticmethod
    def __traer_todas_tareas__(eliminada):
        tareas_db = db.all()
        tareas = []
        for tarea in tareas_db:
            match eliminada:
                case False:
                    if tarea['eliminada']== False:
                        tareas.append(Tarea(
                            tarea['uid'],
                            tarea['titulo'],
                            tarea['descripcion'],
                            tarea['estado'],
                            tarea['creada'],
                            tarea['actualizada'],
                            tarea['eliminada']
                        ))
                case True:
                    if tarea['eliminada']== True:
                        tareas.append(Tarea(
                            tarea['uid'],
                            tarea['titulo'],
                            tarea['descripcion'],
                            tarea['estado'],
                            tarea['creada'],
                            tarea['actualizada'],
                            tarea['eliminada']
                        ))
        return tareas   
 
#IMPRESION DE TAREAS
    @staticmethod
    def imprimir_tarea(uid):
        tarea = AdminTarea.__traer_tarea__(uid)
        headers = ["ID", "Titulo", "Descripción", "Estado", "Creada", "Actualizada", "Eliminada"]
        rows=[]
        if tarea is None:
            print("La tarea que se pide no existe o ya fue eliminada!")
        else:
            rows.append([
                tarea.uid,
                tarea.titulo,
                tarea.descripcion,
                tarea.estado,
                tarea.creada,
                tarea.actualizada,
            ])
            print(tabulate(rows, headers=headers, tablefmt="grid"))

    @staticmethod
    def imprimir_todas_tareas():
        lista_tareas = AdminTarea.__traer_todas_tareas__(False)
        headers = ["ID", "Titulo", "Descripción", "Estado", "Creada", "Actualizada", "Eliminada"]
        rows = []
        for tarea in lista_tareas:
            rows.append([
                tarea.uid,
                tarea.titulo,
                tarea.descripcion,
                tarea.estado,
                tarea.creada,
                tarea.actualizada,
            ])
        print(tabulate(rows, headers=headers, tablefmt="grid"))



#MENU ADMINISTRADOR DE TAREAS
while True:
    system("cls")
    try:
        print("MENU ADMINISTRADOR DE TAREAS\n1. Agregar tarea\n2. Eliminar tarea\n3. Eliminar todas las tareas\n4. Actualizar tarea\n5. Imprimir todas las tareas\n6. Salir")
        opcion=int(input("Ingrese la opcion: "))
        match opcion:
            case 1:
                while True:
                    system("cls")
                    titulo=input("Ingrese el titulo de la tarea: ")
                    descripcion=input("Ingrese la descripcion de la tarea: ")
                    estado=input("Ingrese el estado de la tarea: ")
                    creada= datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
                    actualizada= creada
                    eliminada= False
                    AdminTarea.agregar_tarea(titulo,descripcion,estado,creada,actualizada,eliminada)
                    if input("Desea agregar otra tarea? (y/n): ") == 'n':
                        break
            case 2:
                system("cls")
                try:
                    if db:
                        uid = int(input("Ingrese el ID de la tarea a eliminar: "))
                        tareaid = AdminTarea.__traer_tarea__(uid)
                        if tareaid:
                            print("Se eliminara la siguiente tarea:")
                            AdminTarea.imprimir_tarea(uid)
                            confirmacion = input("Esta seguro que desea eliminar esta tarea? (y/n): ")
                            if confirmacion.lower() == 'y':
                                AdminTarea.eliminar_tarea(uid)
                                print("Tarea eliminada con exito.")
                            else:
                                print("Operacion cancelada.")
                        else:
                            print("No se encontro una tarea con ese ID o esta ya fue eliminada.")
                    else:
                        print("No hay ninguna tarea para eliminar.")
                except ValueError:
                    system("cls")
                    print("Ingrese una ID valida")
                system("pause")
            case 3:
                system("cls")
                if db:
                    confirmacion = input("Esta seguro que deseas eliminar todas las tareas? (y/n): ")
                    if confirmacion.lower() == 'y':
                        AdminTarea.eliminar_todas_tareas()
                        print("Todas las tareas han sido eliminadas.")
                    else:
                        print("Operacion cancelada.")
                else:
                    print("No hay ninguna tarea para eliminar.")
                system("pause")
            case 4:
                system("cls")
                try:
                    if db:
                        uid= int(input("Ingrese la ID de la tarea a actualizar su estado: "))
                        tareaid = AdminTarea.__traer_tarea__(uid)
                        if tareaid:
                            estado= input("Ingrese el nuevo estado: ")
                            AdminTarea.actualizar_estado(uid,estado)
                        else:
                            print("No se encontro una tarea con ese ID.")
                    else:
                        print("No hay ninguna tarea para actualizar.")
                except ValueError:
                    system("cls")
                    print("Ingrese una ID valida")
                system("pause")
            case 5:
                system("cls")
                if db:
                    AdminTarea.imprimir_todas_tareas()
                else:
                    print("No hay ninguna tarea para imprimir.")
                system("pause")
            case 6:
                break
    except ValueError:
        system("cls")
        print("Ingrese una opcion valida")
        system("pause")
