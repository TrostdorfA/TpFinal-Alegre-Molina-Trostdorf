from typing import List
from tinydb import TinyDB, Query
from prettytable import PrettyTable
import datetime
import json


class ModeloBase:
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class Tarea(ModeloBase):
    def __init__(self, titulo: str, descripcion: str, estado: str, creada: str, actualizada: str):
        self.titulo = titulo
        self.descripcion = descripcion
        self.estado = estado
        self.creada = creada
        self.actualizada = actualizada

    def to_dict(self):
        return {
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "estado": self.estado,
            "creada": self.creada,
            "actualizada": self.actualizada
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def actualizar_fecha_actualizacion(self):
        self.actualizada = datetime.datetime.now().strftime('%Y-%m-%d')


class AdminTarea:
    def __init__(self, db_path: str):
        self.db = TinyDB(db_path)

    def agregar_tarea(self, tarea: Tarea) -> int:
        tarea_dict = tarea.to_dict()
        tarea_id = self.db.insert(tarea_dict)
        return tarea_id

    def agregar_tareas(self, tareas: List[Tarea]) -> List[int]:
        tareas_dict = [tarea.to_dict() for tarea in tareas]
        tarea_ids = self.db.insert_multiple(tareas_dict)
        return tarea_ids

    def traer_tarea(self, tarea_id: int) -> Tarea:
        tarea_dict = self.db.get(doc_id=tarea_id)
        tarea = PrettyTable()
        tarea.field_names = ["ID", "Título",
                             "Descripción", "Estado", "Creada", "Actualizada"]
        tarea.add_row([tarea_id, tarea_dict["titulo"], tarea_dict["descripcion"],
                      tarea_dict["estado"], tarea_dict["creada"], tarea_dict["actualizada"]])
        return tarea

    def actualizar_estado_tarea(self, tarea_id: int, estado: str):
        tarea = self.db.get(doc_id=tarea_id)
        tarea["estado"] = estado
        tarea["actualizada"] = datetime.datetime.now().strftime('%Y-%m-%d')
        self.db.update(tarea, doc_ids=[tarea_id])

    def eliminar_tarea(self, tarea_id: int):
        self.db.remove(doc_ids=[tarea_id])

    def traer_todas_tareas(self) -> List[Tarea]:
        tareas_dicts = self.db.all()
        tareas = PrettyTable()
        tareas.field_names = ["ID", "Título",
                              "Descripción", "Estado", "Creada", "Actualizada"]
        for tarea_dict in tareas_dicts:
            tareas.add_row([tarea_dict.doc_id, tarea_dict["titulo"], tarea_dict["descripcion"],
                           tarea_dict["estado"], tarea_dict["creada"], tarea_dict["actualizada"]])
        return tareas


def mostrar_menu():
    print("Selecciona una opción:")
    print("1. Agregar tarea")
    print("2. Agregar varias tareas")
    print("3. Traer tarea")
    print("4. Actualizar estado de tarea")
    print("5. Eliminar tarea")
    print("6. Traer todas las tareas")
    print("7. Salir")


def input_valido(mensaje: str, predeterminado: str = "") -> str:
    valor = input(mensaje)
    return valor if valor.strip() != "" else predeterminado


if __name__ == "__main__":
    db_path = "tareas.json"
    admin_tarea = AdminTarea(db_path)

    corriendo = True
    while corriendo:
        mostrar_menu()
        print()
        opcion = input_valido("Ingrese una opción: ")

        match opcion:
            case "1":
                titulo = input_valido("Ingrese el título de la tarea: ")
                descripcion = input_valido(
                    "Ingrese la descripción de la tarea: ")
                estado = input_valido("Ingrese el estado de la tarea: ")

                if not all([titulo, estado]):
                    print("Los campos: título y estado son obligatorios")
                    print()
                    continue

                tarea = Tarea(
                    titulo=titulo,
                    descripcion=descripcion,
                    estado=estado,
                    creada=datetime.datetime.now().strftime('%Y-%m-%d'),
                    actualizada=datetime.datetime.now().strftime('%Y-%m-%d')
                )
                tarea_id = admin_tarea.agregar_tarea(tarea)
                print(f"Tarea agregada con ID {tarea_id}")

            case "2":
                tareas = []
                cantidad_tareas = int(input_valido(
                    "Ingrese la cantidad de tareas que desea agregar: "))
                for i in range(cantidad_tareas):
                    titulo = input_valido(
                        f"Ingrese el título de la tarea {i+1}: ")
                    descripcion = input_valido(
                        f"Ingrese la descripción de la tarea {i+1}: ")
                    estado = input_valido(
                        f"Ingrese el estado de la tarea {i+1}: ")
                    tarea = Tarea(
                        titulo=titulo,
                        descripcion=descripcion,
                        estado=estado,
                        creada=datetime.datetime.now().strftime('%Y-%m-%d'),
                        actualizada=datetime.datetime.now().strftime('%Y-%m-%d')
                    )
                    tareas.append(tarea)
                tarea_ids = admin_tarea.agregar_tareas(tareas)
                print(f"Se agregaron las tareas con IDs {tarea_ids}")

            case "3":
                tarea_id = int(input_valido(
                    "Ingrese el ID de la tarea que desea traer: "))
                tarea = admin_tarea.traer_tarea(tarea_id)
                if tarea:
                    print(tarea)
                else:
                    print(f"No existe la tarea con ID {tarea_id}")

            case "4":
                tarea_id = int(input_valido(
                    "Ingrese el ID de la tarea que desea actualizar: "))
                estado = input_valido("Ingrese el nuevo estado de la tarea: ")
                admin_tarea.actualizar_estado_tarea(tarea_id, estado)
                print("Tarea actualizada")

            case "5":
                tarea_id = int(input_valido(
                    "Ingrese el ID de la tarea que desea eliminar: "))
                admin_tarea.eliminar_tarea(tarea_id)
                print("Tarea eliminada")

            case "6":
                tareas = admin_tarea.traer_todas_tareas()
                if not tareas:
                    print("No hay tareas")
                    print()
                    continue
                tareas_ordenadas = tareas.get_string(sortby="Actualizada")
                print(tareas_ordenadas)

            case "7":
                print("Saliendo...")
                corriendo = False

            case _:
                print("Opción inválida. Intente de nuevo.")

        print()  # Salto de línea
