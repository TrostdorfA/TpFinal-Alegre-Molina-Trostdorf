from tkinter import Listbox, messagebox, simpledialog
import TpFinal
import requests
import threading
from customtkinter import CTkLabel, CTkEntry, CTkButton, CTkToplevel, CTkFrame, CTk
API_URL = "http://localhost:8000"

# Clase principal que representa la interfaz de usuario
class Interfaz(CTk):
    def __init__(self):
        super().__init__()
        self.headers = {}
        self.title("Administrador de tareas")
        self.geometry("+%d+%d" % (self.winfo_screenwidth() / 2 -
                      400, self.winfo_screenheight() / 2 - 350))
        self.geometry("800x700")
        self.tasks = []
        self.current_window = None
        self.configure(bg="#F0F0F0")
        self.autenticar()
        self.autenticado = False

    # Ventana de error
    def show_error_message(self, message, title):
        error_window = CTkToplevel()
        error_window.title(title)
        error_window.geometry("+%d+%d" % (self.winfo_screenwidth() / 2 -
                                      150, self.winfo_screenheight() / 2 - 50))
        error_window.geometry("300x100")
        error_window.configure(bg="#F0F0F0")
        error_window.resizable(False, False)

        CTkLabel(error_window, text=message).pack(pady=10)
        CTkButton(error_window, text="Aceptar",
              command=error_window.destroy).pack(pady=10)

        # Hacer que la ventana de error esté siempre en primer plano
        error_window.attributes("-topmost", True)
        error_window.grab_set()

        # Asegurarse de que la ventana principal quede bloqueada mientras la ventana de error esté abierta
        self.wait_window(error_window)


    # Ventana de autenticación
    def autenticar(self):
        auth_window = CTkToplevel(self)
        auth_window.title("Autenticación")
        auth_window.geometry("+%d+%d" % (self.winfo_screenwidth() / 2 -
                                         150, self.winfo_screenheight() / 2 - 100))
        auth_window.geometry("300x200")
        auth_window.configure(bg="#F0F0F0")
        auth_window.resizable(False, False)
        auth_window.attributes('-topmost', True)
        auth_window.protocol("WM_DELETE_WINDOW", cerrar_aplicacion)

        CTkLabel(auth_window, text="Usuario:").pack(pady=5)
        username_entry = CTkEntry(auth_window)
        username_entry.pack(pady=5)

        CTkLabel(auth_window, text="Contraseña:").pack(pady=5)
        password_entry = CTkEntry(auth_window, show="*")
        password_entry.pack(pady=5)

        CTkButton(auth_window, text="Ingresar", command=lambda: self.verify_credentials(
            username_entry.get(), password_entry.get(), auth_window)).pack(pady=5)


    # Ventana verificacion de credenciales del usuario
    def verify_credentials(self, username, password, auth_window):
        payload = {"username": username, "password": password}
        response = requests.post(f"{API_URL}/login", data=payload)

        if response.status_code == 200:
            self.headers["Authorization"] = f"Bearer {response.json()['token']}"
            auth_window.withdraw()
            self.autenticado = True
            self.setup_ui()
            self.load_tasks()
        else:
            self.show_error_message("Error, usuario o contraseña incorrectos", "Error de autenticación")

    def clear_ui(self):
        self.CTkButton_CTkFrame.destroy()
        self.listbox_tasks.destroy()
        self.CTkLabel_description.destroy()

    def logout(self):
        self.headers = {}
        self.autenticado = False
        self.clear_ui()
        self.autenticar()

    def setup_ui(self):
        self.CTkButton_CTkFrame = CTkFrame(self)
        self.CTkButton_CTkFrame.pack(side="right", padx=10, pady=10)

        self.CTkButton_create = CTkButton(
            self.CTkButton_CTkFrame, text="Crear", command=self.open_create_window)
        self.CTkButton_create.pack(side="top", pady=5)

        self.CTkButton_search = CTkButton(
            self.CTkButton_CTkFrame, text="Buscar", command=self.open_search_window)
        self.CTkButton_search.pack(side="top", pady=5)

        self.CTkButton_update = CTkButton(
            self.CTkButton_CTkFrame, text="Actualizar", command=self.open_update_window)
        self.CTkButton_update.pack(side="top", pady=5)

        self.CTkButton_delete = CTkButton(
            self.CTkButton_CTkFrame, text="Eliminar", command=self.delete_task)
        self.CTkButton_delete.pack(side="top", pady=5)

        self.CTkButton_Logout = CTkButton(
            self.CTkButton_CTkFrame, text="Cerrar Sesión", command=self.logout)
        self.CTkButton_Logout.pack(side="top", pady=5)

        self.listbox_tasks = Listbox(self, width=100, height=30)
        self.listbox_tasks.pack(padx=10, pady=10)
        self.listbox_tasks.bind("<<ListboxSelect>>", self.select_task)
        self.listbox_tasks.configure(bg="#F0F0F0")

        self.CTkLabel_description = CTkLabel(
            self, text="", wraplength=700, justify="left")
        self.CTkLabel_description.pack(padx=10, pady=(0, 10))


    # Carga las tareas desde el servidor y las guarda en la lista de tareas
    def load_tasks(self, update_description=True):
        response = requests.get(f"{API_URL}")
        if response.status_code == 200:
            data = response.json()
            self.tasks = data.get("tareas", [])
            self.listbox_tasks.delete(0, "end")
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
            self.CTkLabel_description.configure(
                text="Error al cargar las tareas")

    # Muestra la descripción de la tarea seleccionada
    def select_task(self, event):
        index = self.listbox_tasks.curselection()
        if index:
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
    
    # Ventana para actualizar una tarea
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
            self.current_window.geometry(
                "+%d+%d" % (self.winfo_screenwidth() / 2 - 150, self.winfo_screenheight() / 2 - 100))
            self.current_window.resizable(False, False)
            self.current_window.attributes("-topmost", True)

            CTkLabel_message = CTkLabel(
                self.current_window, text="Ingrese el nuevo estado:")
            CTkLabel_message.pack(padx=10, pady=10)

            self.CTkEntry_message = CTkEntry(self.current_window)
            self.CTkEntry_message.pack(padx=10, pady=5)

            CTkButton_send = CTkButton(self.current_window, text="Actualizar", command=lambda: self.update_selected_task(
                tarea_uid, self.CTkEntry_message.get()))
            CTkButton_send.pack(padx=10, pady=5)
        else:
            self.show_error_message("Seleccione una tarea para actualizar.", "Información")

    # Actualiza tarea seleccionada
    def update_selected_task(self, uid, estado):
        response = requests.get(
            f"{API_URL}/actualizar/{uid}", params={"estado": estado})
        if response.status_code == 200:
            self.load_tasks(update_description=False)
            self.current_window.destroy()
            self.show_error_message("Tarea actualizada con éxito!", "Información")
        else:
            self.show_error_message("Error al actualizar la tarea", "Error")

    # Ventana eliminar tareas
    def delete_task(self):
        if self.current_window:
            self.current_window.destroy()

        selected_index = self.listbox_tasks.curselection()
        if selected_index:
            tarea_text = self.listbox_tasks.get(selected_index[0])
            tarea_uid = tarea_text.split(" | ")[0]

            self.current_window = CTkToplevel(self)
            self.current_window.title("Eliminar tarea")
            self.current_window.geometry("300x150")
            self.current_window.geometry(
                "+%d+%d" % (self.winfo_screenwidth() / 2 - 150, self.winfo_screenheight() / 2 - 100))
            self.current_window.resizable(False, False)
            self.current_window.attributes("-topmost", True)

            CTkLabel_message = CTkLabel(
                self.current_window, text="¿Qué acción desea realizar?")
            CTkLabel_message.pack(pady=10)

            CTkButton_delete_selected = CTkButton(
                self.current_window, text="Eliminar tarea seleccionada", command=lambda: self.delete_selected_task(tarea_uid))
            CTkButton_delete_selected.pack(pady=5)

            CTkButton_delete_all = CTkButton(
                self.current_window, text="Eliminar todas las tareas", command=self.delete_all_tasks)
            CTkButton_delete_all.pack(pady=5)
        else:
            self.show_error_message("Seleccione una tarea para eliminar.", "Información")

    # Elimina la tarea seleccionada
    def delete_selected_task(self, uid):
        response = requests.get(f"{API_URL}/eliminar/{uid}")
        if response.status_code == 200:
            self.load_tasks(update_description=False)
            self.current_window.destroy()
            self.show_error_message("Tarea eliminada con éxito!", "Información")
        else:
            self.show_error_message("Error al eliminar la tarea", "Error")

    # Elimina todas las tareas
    def delete_all_tasks(self):
        response = requests.get(f"{API_URL}/eliminar-todas")
        if response.status_code == 200:
            self.load_tasks(update_description=False)
            self.current_window.destroy()
            self.show_error_message("Todas las tareas han sido eliminadas.", "Información")
        else:
            self.show_error_message("Error al eliminar todas las tareas.", "Error")

    #Ventana de creacion de tarea
    def open_create_window(self):
        if self.current_window:
            self.current_window.destroy()
        create_window = CTkToplevel(self)
        create_window.title("Crear tarea")
        create_window.geometry("300x250")
        create_window.geometry(
            "+%d+%d" % (self.winfo_screenwidth() / 2 - 150, self.winfo_screenheight() / 2 - 100))
        create_window.grab_set()
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

        CTkButton_save = CTkButton(create_window, text="Guardar", command=lambda: self.save_task(
            CTkEntry_title.get(), CTkEntry_description.get(), CTkEntry_status.get(), create_window))
        CTkButton_save.pack(pady=5)

        CTkButton_cancel = CTkButton(
            create_window, text="Cancelar", command=create_window.destroy)
        CTkButton_cancel.pack(pady=5)

    # Guarda la tarea en la base de datos
    def save_task(self, titulo, descripcion, estado, create_window):
        if not titulo:
            self.show_error_message("Por favor, complete titulo de la tarea", "Error")
            return
        if not estado:
            estado = "Por definir"

        payload = {
            "titulo": str(titulo),
            "descripcion": str(descripcion),
            "estado": str(estado),
        }

        response = requests.post(f"{API_URL}/agregar", json=payload)
        if response.status_code == 200:
            self.load_tasks(update_description=False)
            create_window.destroy()
            self.show_error_message("Tarea creada con éxito!", "Información")
        else:
            self.show_error_message("Error al guardar la tarea", "Error")

    # Ventana buscar tarea
    def open_search_window(self):
        if self.current_window:
            self.current_window.destroy()
        search_window = CTkToplevel(self)
        search_window.title("Buscar tarea")
        search_window.geometry("300x150")
        search_window.geometry(
            "+%d+%d" % (self.winfo_screenwidth() / 2 - 150, self.winfo_screenheight() / 2 - 100))
        search_window.grab_set()
        self.current_window = search_window

        CTkLabel_uid = CTkLabel(search_window, text="UID:")
        CTkLabel_uid.pack()
        CTkEntry_uid = CTkEntry(search_window)
        CTkEntry_uid.pack()

        CTkButton_search = CTkButton(search_window, text="Buscar", command=lambda: self.search_task_by_uid(
            CTkEntry_uid.get(), search_window))
        CTkButton_search.pack(pady=5)

        CTkButton_cancel = CTkButton(
            search_window, text="Cancelar", command=search_window.destroy)
        CTkButton_cancel.pack(pady=5)

    # Busca la tarea por uid en la lista de tareas
    def search_task_by_uid(self, uid, search_window):
        if uid.isdigit():
            uid = int(uid)
            tarea_encontrada = None

            for index, tarea in enumerate(self.tasks):
                if tarea["uid"] == uid:
                    tarea_encontrada = tarea
                    break

            if tarea_encontrada:
                self.listbox_tasks.selection_clear(0, "end")
                self.listbox_tasks.selection_set(index)
                self.listbox_tasks.see(index)

                descripcion = f"UID: {tarea_encontrada['uid']}\nTítulo: {tarea_encontrada['titulo']}\nDescripción: {tarea_encontrada['descripcion']}\nEstado: {tarea_encontrada['estado']}\nCreada: {tarea_encontrada['creada']}\nActualizada: {tarea_encontrada['actualizada']}"
                self.CTkLabel_description.configure(text=descripcion)
                search_window.destroy()
                self.show_error_message("Tarea encontrada: {}".format(
                    tarea_encontrada["titulo"]), "Información")
            else:
                self.CTkLabel_description.configure(text="")
                self.show_error_message(
                    "No se encontró ninguna tarea con el UID: {}".format(uid), "Información")
        else:
            self.show_error_message("Error, Ingrese un UID válido", "Error de UID")

# Apaga el servidor uvicorn cuando se cierra la aplicacion
def cerrar_aplicacion():
    if TpFinal.proceso_servidor:
        TpFinal.proceso_servidor.terminate()
    app.quit()


if __name__ == "__main__":
    thread_servidor = threading.Thread(target=TpFinal.iniciar_servidor)
    thread_servidor.start()
    app = Interfaz()
    app.protocol("WM_DELETE_WINDOW", cerrar_aplicacion)
    app.mainloop()
