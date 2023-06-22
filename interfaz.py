from tkinter import Listbox, messagebox, simpledialog
import TpFinal
import datetime
import requests
import threading
from customtkinter import CTkLabel, CTkEntry, CTkButton, CTkToplevel, CTkFrame, CTk
API_URL = "http://localhost:8000"

class Interfaz(CTk):
    def __init__(self):
        super().__init__()
        self.title("Administrador de tareas")
        self.geometry("+%d+%d" % (self.winfo_screenwidth() / 2 - 450, self.winfo_screenheight() / 2 - 350))
        self.geometry("800x700")
        self.setup_ui()
        self.tasks = []  # Lista para almacenar las tareas cargadas desde la API
        self.load_tasks()
        self.current_window = None  # Variable para almacenar la ventana abierta actualmente
        self.configure(bg="#F0F0F0")  # Cambiar el color de fondo de la ventana principal

    def setup_ui(self):
        self.CTkButton_CTkFrame = CTkFrame(self)
        self.CTkButton_CTkFrame.pack(side="right", padx=10, pady=10)

        self.CTkButton_create = CTkButton(self.CTkButton_CTkFrame, text="Crear", command=self.open_create_window)
        self.CTkButton_create.pack(side="top", pady=5)

        self.CTkButton_search = CTkButton(self.CTkButton_CTkFrame, text="Buscar", command=self.open_search_window)
        self.CTkButton_search.pack(side="top", pady=5)

        self.CTkButton_update = CTkButton(self.CTkButton_CTkFrame, text="Actualizar", command=self.open_update_window)
        self.CTkButton_update.pack(side="top", pady=5)

        self.CTkButton_delete = CTkButton(self.CTkButton_CTkFrame, text="Eliminar", command=self.delete_task)
        self.CTkButton_delete.pack(side="top", pady=5)

        self.listbox_tasks = Listbox(self, width=100, height=30)
        self.listbox_tasks.pack(padx=10, pady=10)
        self.listbox_tasks.bind("<<ListboxSelect>>", self.select_task)
        self.listbox_tasks.configure(bg="#F0F0F0")  # Cambiar el color de fondo de la lista de tareas

        self.CTkLabel_description = CTkLabel(self, text="", wraplength=700, justify="left")
        self.CTkLabel_description.pack(padx=10, pady=(0, 10))

    def load_tasks(self, update_description=True):
        response = requests.get(f"{API_URL}")  # Hacer una solicitud GET a la API
        if response.status_code == 200:
            data = response.json()  # Obtener los datos en formato JSON
            self.tasks = data.get("tareas", [])  # Obtener la lista de tareas del campo "tareas" en los datos
            self.listbox_tasks.delete(0, "end")  # Limpiar la lista actual de tareas
            for tarea in self.tasks:
                uid = tarea["uid"]
                titulo = tarea["titulo"]
                estado = tarea["estado"]
                creada = tarea["creada"]
                actualizada = tarea["actualizada"]
                task_text = f"{uid} | {titulo} | Estado: {estado} | Creación: {creada} | Actualización: {actualizada}"
                self.listbox_tasks.insert("end", task_text)

            if update_description and self.tasks:
                tarea = self.tasks[0]
                descripcion = f"UID: {tarea['uid']}\nTítulo: {tarea['titulo']}\nDescripción: {tarea['descripcion']}\nEstado: {tarea['estado']}\nCreada: {tarea['creada']}\nActualizada: {tarea['actualizada']}"
                self.CTkLabel_description.configure(text=descripcion)
            else:
                self.CTkLabel_description.configure(text="")
        else:
            self.CTkLabel_description.configure(text="Error al cargar las tareas")

    def select_task(self, event):
        # Obtener el índice de la tarea seleccionada en la Listbox
        index = self.listbox_tasks.curselection()
        if index:
            # Obtener la tarea seleccionada de self.tasks
            tarea_text = self.listbox_tasks.get(index)
            tarea_uid = tarea_text.split(" | ")[0]
            for tarea in self.tasks:
                if tarea["uid"] == int(tarea_uid):
                    descripcion = f"UID: {tarea['uid']}\nTítulo: {tarea['titulo']}\nDescripción: {tarea['descripcion']}\nEstado: {tarea['estado']}\nCreada: {tarea['creada']}\nActualizada: {tarea['actualizada']}"
                    self.CTkLabel_description.configure(text=descripcion)
                    tarea_encontrada = True
                    break

            if tarea_encontrada:
                self.CTkLabel_description.configure(text=descripcion)
            else:
                self.CTkLabel_description.configure(text="")
        else:
            self.CTkLabel_description.configure(text="")

    # def update_task(self):
    #     if self.current_window:
    #         self.current_window.destroy()  # Cierra la ventana abierta actualmente

    #     selected_index = self.listbox_tasks.curselection()
    #     if selected_index:
    #         tarea_text = self.listbox_tasks.get(selected_index[0])
    #         tarea_uid = tarea_text.split(" | ")[0]
    #         update_text = simpledialog.askstring("Actualizar Tarea", "Ingrese el nuevo estado:")
    #         if update_text:
    #             response = requests.get(f"{API_URL}/actualizar/{tarea_uid}", params={"estado": update_text})
    #             if response.status_code == 200:
    #                 self.load_tasks(update_description=False)
    #                 messagebox.showinfo("Información", "Tarea actualizada con éxito!")
    #             else:
    #                 messagebox.showerror("Error", "Error al actualizar la tarea")
    #     else:
    #         messagebox.showinfo("Información", "Seleccione una tarea para actualizar.")

    def open_update_window(self):
        if self.current_window:
            self.current_window.destroy()
    
        selected_index = self.listbox_tasks.curselection()
        if selected_index:
            tarea_text = self.listbox_tasks.get(selected_index[0])
            tarea_uid = tarea_text.split(" | ")[0]

            self.current_window = CTkToplevel(self)
            self.current_window.title("Actualizar tarea")
            self.current_window.geometry("300x150")
            self.current_window.geometry("+%d+%d" % (self.winfo_screenwidth() / 2 - 200, self.winfo_screenheight() / 2 - 150))
            self.current_window.resizable(False, False)
            self.current_window.attributes("-topmost", True)

            CTkLabel_message = CTkLabel(self.current_window, text="Ingrese el nuevo estado:")
            CTkLabel_message.pack(padx=10, pady=10)

            self.CTkEntry_message = CTkEntry(self.current_window)
            self.CTkEntry_message.pack(padx=10, pady=5)

            CTkButton_send = CTkButton(self.current_window, text="Actualizar", command=lambda: self.update_selected_task(tarea_uid, self.CTkEntry_message.get()))
            CTkButton_send.pack(padx=10, pady=5)
        else:
            messagebox.showinfo("Información", "Seleccione una tarea para actualizar.")

    def update_selected_task(self, uid, estado):
        response = requests.get(f"{API_URL}/actualizar/{uid}", params={"estado": estado})
        if response.status_code == 200:
            self.load_tasks(update_description=False)
            self.current_window.destroy()
            messagebox.showinfo("Información", "Tarea actualizada con éxito!")
        else:
            messagebox.showerror("Error", "Error al actualizar la tarea")


    def delete_task(self):
        if self.current_window:
            self.current_window.destroy()  # Cierra la ventana abierta actualmente

        selected_index = self.listbox_tasks.curselection()
        if selected_index:
            tarea_text = self.listbox_tasks.get(selected_index[0])
            tarea_uid = tarea_text.split(" | ")[0]
 
            self.current_window = CTkToplevel(self)
            self.current_window.title("Eliminar tarea")
            self.current_window.geometry("300x150")
            self.current_window.geometry("+%d+%d" % (self.winfo_screenwidth() / 2 - 200, self.winfo_screenheight() / 2 - 150))
            self.current_window.resizable(False, False)
            self.current_window.attributes("-topmost", True)

            CTkLabel_message = CTkLabel(self.current_window, text="¿Qué acción desea realizar?")
            CTkLabel_message.pack(pady=10)

            CTkButton_delete_selected = CTkButton(self.current_window, text="Eliminar tarea seleccionada", command=lambda: self.delete_selected_task(tarea_uid))
            CTkButton_delete_selected.pack(pady=5)

            CTkButton_delete_all = CTkButton(self.current_window, text="Eliminar todas las tareas", command=self.delete_all_tasks)
            CTkButton_delete_all.pack(pady=5)
        else:
            messagebox.showinfo("Información", "Seleccione una tarea para eliminar.")

    def delete_selected_task(self, uid):
        response = requests.get(f"{API_URL}/eliminar/{uid}")
        if response.status_code == 200:
            self.load_tasks(update_description=False)
            self.current_window.destroy()
            messagebox.showinfo("Información", "Tarea eliminada con éxito!")
        else:
            messagebox.showerror("Error", "Error al eliminar la tarea")

    def delete_all_tasks(self):
        response = requests.get(f"{API_URL}/eliminar-todas")
        if response.status_code == 200:
            self.load_tasks(update_description=False)
            self.current_window.destroy()
            messagebox.showinfo("Información", "Todas las tareas han sido eliminadas.")
        else:
            messagebox.showerror("Error", "Error al eliminar todas las tareas")


    def open_create_window(self):
        if self.current_window:
            self.current_window.destroy()  # Cierra la ventana abierta actualmente
        create_window = CTkToplevel(self)
        create_window.title("Crear tarea")
        create_window.geometry("300x250")
        create_window.geometry("+%d+%d" % (self.winfo_screenwidth() / 2 - 200, self.winfo_screenheight() / 2 - 150))
        create_window.grab_set()  # Bloquea la ventana principal hasta que se cierre la ventana emergente
        self.current_window = create_window

        CTkLabel_title = CTkLabel(create_window, text="Título:")
        CTkLabel_title.pack()
        CTkEntry_title = CTkEntry(create_window)
        CTkEntry_title.pack()

        CTkLabel_description = CTkLabel(create_window, text="Descripción:")
        CTkLabel_description.pack()
        CTkEntry_description = CTkEntry(create_window)
        CTkEntry_description.pack()

        CTkLabel_status = CTkLabel(create_window, text="Estado:")
        CTkLabel_status.pack()
        CTkEntry_status = CTkEntry(create_window)
        CTkEntry_status.pack()

        CTkButton_save = CTkButton(create_window, text="Guardar", command=lambda: self.save_task(CTkEntry_title.get(), CTkEntry_description.get(), CTkEntry_status.get(), create_window))
        CTkButton_save.pack(pady=5)

        CTkButton_cancel = CTkButton(create_window, text="Cancelar", command=create_window.destroy)
        CTkButton_cancel.pack(pady=5)

    def save_task(self, titulo, descripcion, estado, create_window):
        payload = {
            "titulo": str(titulo),
            "descripcion": str(descripcion),
            "estado": str(estado),
        }

        # Enviar la solicitud POST a la API
        response = requests.post(f"{API_URL}/agregar", json=payload)
        self.load_tasks(update_description=False)
        create_window.destroy()
        messagebox.showinfo("Información", "Tarea creada con éxito!")


    def open_search_window(self):
        if self.current_window:
            self.current_window.destroy()  # Cierra la ventana abierta actualmente
        search_window = CTkToplevel(self)
        search_window.title("Buscar tarea")
        search_window.geometry("300x150")
        search_window.geometry("+%d+%d" % (self.winfo_screenwidth() / 2 - 200, self.winfo_screenheight() / 2 - 150))
        search_window.grab_set()  # Bloquea la ventana principal hasta que se cierre la ventana emergente
        self.current_window = search_window

        CTkLabel_uid = CTkLabel(search_window, text="UID:")
        CTkLabel_uid.pack()
        CTkEntry_uid = CTkEntry(search_window)
        CTkEntry_uid.pack()

        CTkButton_search = CTkButton(search_window, text="Buscar", command=lambda: self.search_task_by_uid(CTkEntry_uid.get(), search_window))
        CTkButton_search.pack(pady=5)

        CTkButton_cancel = CTkButton(search_window, text="Cancelar", command=search_window.destroy)
        CTkButton_cancel.pack(pady=5)

    def search_task_by_uid(self, uid, search_window):
        if uid.isdigit():
            uid = int(uid)
            tarea_encontrada = None

            for tarea in self.tasks:
                if tarea["uid"] == uid:
                    tarea_encontrada = tarea
                    break

            if tarea_encontrada:
                index = uid - 1
                self.listbox_tasks.selection_clear(0, "end")
                self.listbox_tasks.selection_set(index)
                self.listbox_tasks.see(index)

                descripcion = f"UID: {tarea_encontrada['uid']}\nTítulo: {tarea_encontrada['titulo']}\nDescripción: {tarea_encontrada['descripcion']}\nEstado: {tarea_encontrada['estado']}\nCreada: {tarea_encontrada['creada']}\nActualizada: {tarea_encontrada['actualizada']}"
                self.CTkLabel_description.configure(text=descripcion)
                search_window.destroy()
                messagebox.showinfo("Información", "Tarea encontrada: {}".format(tarea_encontrada["titulo"]))
            else:
                self.CTkLabel_description.configure(text="")  # Limpiar la descripción si no se encuentra la tarea
                messagebox.showinfo("Información", "No se encontró ninguna tarea con el UID: {}".format(uid))
        else:
            messagebox.showerror("Error", "Ingrese un UID válido")

def cerrar_aplicacion():
# Detener el servidor de la API
    if TpFinal.proceso_servidor:
        TpFinal.proceso_servidor.terminate()
    app.quit()

if __name__ == "__main__":
    thread_servidor= threading.Thread(target=TpFinal.iniciar_servidor)
    thread_servidor.start()
    app = Interfaz()
    app.protocol("WM_DELETE_WINDOW", cerrar_aplicacion)
    app.mainloop()