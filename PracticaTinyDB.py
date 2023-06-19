from os import system
import datetime
import sqlite3
from tkinter import Tk, Label, Entry, Button, Listbox, messagebox, Toplevel, Frame
from tkinter import simpledialog


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
        cursor.execute("INSERT INTO tareas (titulo, descripcion, estado, creada, actualizada, eliminada) VALUES (?, ?, ?, ?, ?, ?)",
                       (titulo, descripcion, estado, creada, actualizada, eliminada))
        conn.commit()
        print("Tarea agregada con éxito!")
        
    @staticmethod
    def actualizar_estado(uid, estado):
        cursor.execute("UPDATE tareas SET estado = ?, actualizada = ? WHERE uid = ?", (estado, datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), uid))
        conn.commit()
        print("Tarea actualizada con éxito!")

    @staticmethod
    def eliminar_tarea(uid):
        cursor.execute("DELETE FROM tareas WHERE uid = ?", (uid,))
        conn.commit()
        
    @staticmethod
    def eliminar_todas_tareas():
        cursor.execute("DELETE FROM tareas")
        conn.commit()

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
   
 



class Interfaz(Tk):
    def __init__(self):
        super().__init__()
        self.title("Administrador de tareas")
        self.geometry("800x700")
        self.setup_ui()
        self.load_tasks()
        self.search_window_open = False
        self.create_window_open = False


    def setup_ui(self):
        self.button_frame = Frame(self)
        self.button_frame.pack(side="right", padx=10, pady=10)

        self.button_create = Button(self.button_frame, text="Crear", command=self.open_create_window)
        self.button_create.pack(side="top", pady=5)

        self.button_search = Button(self.button_frame, text="Buscar", command=self.open_search_window)
        self.button_search.pack(side="top", pady=5)

        self.button_update = Button(self.button_frame, text="Actualizar", command=self.update_task)
        self.button_update.pack(side="top", pady=5)

        self.button_delete = Button(self.button_frame, text="Eliminar", command=self.delete_task)
        self.button_delete.pack(side="top", pady=5)

        self.listbox_tasks = Listbox(self, width=100, height=600)
        self.listbox_tasks.pack(side="top", padx=10, pady=10)
        self.listbox_tasks.bind("<<ListboxSelect>>", self.update_description)

        self.label_description = Label(self, text="", wraplength=700)
        self.label_description.pack(padx=10, pady=(0, 10))


    def load_tasks(self):
        self.listbox_tasks.delete(0, "end")
        cursor.execute("SELECT * FROM tareas WHERE eliminada = ''")
        tareas = cursor.fetchall()
        for tarea in tareas:
            uid = tarea[0]
            titulo = tarea[1]
            estado = tarea[3]
            creada = tarea[4]
            actualizada = tarea[5]
            task_text = f"{uid} | {titulo} | Estado: {estado} | Creación: {creada} | Actualización: {actualizada}"
            self.listbox_tasks.insert("end", task_text)

    def update_task(self):
        selected_index = self.listbox_tasks.curselection()
        if selected_index:
            tarea_text = self.listbox_tasks.get(selected_index[0])
            tarea_uid = tarea_text.split(" | ")[0]
            tarea = AdminTarea.__traer_tarea__(int(tarea_uid))
            if tarea:
                update_text = simpledialog.askstring("Actualizar Tarea", "Ingrese la actualización a realizar:")
                if update_text:
                    # Actualizar la tarea con la actualización ingresada
                    AdminTarea.actualizar_estado(tarea.uid, update_text)
                    self.load_tasks()
                    messagebox.showinfo("Información", "Tarea actualizada con éxito!")
                else:
                    messagebox.showwarning("Advertencia", "No se ingresó ninguna actualización.")
            else:
                messagebox.showinfo("Información", "No se encontró la tarea.")
        else:
            messagebox.showinfo("Información", "Seleccione una tarea para actualizar.")

    def delete_task(self):
        selected_index = self.listbox_tasks.curselection()
        if selected_index:
            tarea_text = self.listbox_tasks.get(selected_index[0])
            tarea_uid = tarea_text.split(" | ")[0]
            tarea = AdminTarea.__traer_tarea__(int(tarea_uid))
            if tarea:
                response = messagebox.askyesno("Confirmar ocultación", "¿Estás seguro de que deseas ocultar la tarea?")
                if response == messagebox.YES:
                    tarea.eliminada = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")  # Marcar la tarea como eliminada
                    AdminTarea.actualizar_estado(tarea.uid, tarea.eliminada)  # Actualizar el estado de la tarea en la base de datos
                    self.load_tasks()
                    messagebox.showinfo("Información", "Tarea ocultada con éxito!")
            else:
                messagebox.showinfo("Información", "No se encontró la tarea.")
        else:
            messagebox.showinfo("Información", "Seleccione una tarea para ocultar.")




    def open_create_window(self):
        if self.create_window_open:
            messagebox.showinfo("Información", "La ventana de creación de tarea ya está abierta.")
            self.create_window.lift()
            return

        create_window = Toplevel(self)
        create_window.title("Crear tarea")
        create_window.protocol("WM_DELETE_WINDOW", self.on_create_window_close)  # Capturar evento de cierre de la ventana
        self.create_window_open = True  # Marcar la ventana de creación de tarea como abierta
        self.create_window = create_window

        label_title = Label(create_window, text="Título:")
        label_title.pack()
        entry_title = Entry(create_window)
        entry_title.pack()

        label_description = Label(create_window, text="Descripción:")
        label_description.pack()
        entry_description = Entry(create_window)
        entry_description.pack()

        label_status = Label(create_window, text="Estado:")
        label_status.pack()
        entry_status = Entry(create_window)
        entry_status.pack()

        button_save = Button(create_window, text="Guardar", command=lambda: self.save_task(entry_title.get(), entry_description.get(), entry_status.get(), create_window))
        button_save.pack(pady=5)

        button_cancel = Button(create_window, text="Cancelar", command=create_window.destroy)
        button_cancel.pack(pady=5)

    def on_create_window_close(self):
        self.create_window.destroy()
        self.reset_create_window_open()

    def reset_create_window_open(self):
        self.create_window_open = False

    def save_task(self, title, description, status, create_window):
        current_time = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        AdminTarea.agregar_tarea(title, description, status, current_time, current_time, "")
        self.load_tasks()
        create_window.destroy()


    def open_search_window(self):
        if self.search_window_open:
            messagebox.showinfo("Información", "La ventana de búsqueda ya está abierta.")
            self.search_window.lift()
            return

        search_window = Toplevel(self)
        search_window.title("Buscar tarea")
        search_window.protocol("WM_DELETE_WINDOW", self.on_search_window_close)  # Capturar evento de cierre de la ventana
        self.search_window_open = True  # Marcar la ventana de búsqueda como abierta
        self.search_window = search_window

        label_uid = Label(search_window, text="UID:")
        label_uid.pack()
        entry_uid = Entry(search_window)
        entry_uid.pack()

        button_search = Button(search_window, text="Buscar", command=lambda: self.search_task_by_uid(entry_uid.get(), search_window))
        button_search.pack(pady=5)

    def on_search_window_close(self):
        self.search_window_open = False  # Marcar la ventana de búsqueda como cerrada
        self.focus()

    def search_task_by_uid(self, uid, search_window):
        if uid.isdigit():
            uid = int(uid)
            tarea = AdminTarea.__traer_tarea__(uid)
            if tarea is not None:
                index = uid - 1  # Restar 1 al UID para obtener el índice correspondiente en el Listbox
                self.listbox_tasks.selection_clear(0, "end")  # Deseleccionar todos los elementos en el Listbox
                self.listbox_tasks.selection_set(index)  # Establecer la nueva selección
                self.listbox_tasks.see(index)
                messagebox.showinfo("Información", "Tarea encontrada: {}".format(tarea.titulo))
            else:
                messagebox.showinfo("Información", "No se encontró ninguna tarea con el UID: {}".format(uid))
        else:
            messagebox.showerror("Error", "Ingrese un UID válido")

        search_window.destroy()


    def update_description(self, event):
        selected_index = self.listbox_tasks.curselection()
        if selected_index:
            tarea_text = self.listbox_tasks.get(selected_index[0])
            tarea_uid = tarea_text.split(" | ")[0]
            tarea = AdminTarea.__traer_tarea__(int(tarea_uid))
            if tarea:
                self.label_description.configure(text=tarea.descripcion)
            else:
                self.label_description.configure(text="")



if __name__ == "__main__":
    app = Interfaz()
    app.mainloop()

