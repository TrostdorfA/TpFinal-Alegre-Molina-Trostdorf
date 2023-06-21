from tkinter import Tk, Label, Entry, Button, Listbox, messagebox, Toplevel, Frame, simpledialog
import TpFinal
import datetime
import requests
import threading
import sqlite3
import hashlib
API_URL = "http://localhost:8000"



class Interfaz(Tk):
    def __init__(self):
        super().__init__()
        self.headers = {}
        self.title("Administrador de tareas")
        self.geometry("800x700")
        self.setup_ui()
        self.load_tasks()
        self.current_window = None  # Variable para almacenar la ventana abierta actualmente
        self.autenticado = False  # Variable para almacenar el estado de autenticación
        self.autenticar()

    def autenticar(self):
        auth_window = Tk()
        auth_window.title("Autenticación")
        auth_window.geometry("300x150")
        auth_window.resizable(False, False)
        auth_window.attributes("-topmost", True)

        label_username = Label(auth_window, text="Nombre de usuario:")
        label_username.pack()
        entry_username = Entry(auth_window)
        entry_username.pack()

        label_password = Label(auth_window, text="Contraseña:")
        label_password.pack()
        entry_password = Entry(auth_window, show="*")
        entry_password.pack()

        button_submit = Button(auth_window, text="Iniciar sesión", command=lambda: self.verificar_credenciales(entry_username.get(), entry_password.get(), auth_window))
        button_submit.pack(pady=10)

        auth_window.mainloop()

    def verificar_credenciales(self, username, password, auth_window):
        # Conexión a la base de datos
        conn = sqlite3.connect("tareas.db")
        cursor = conn.cursor()

        # Consulta para verificar las credenciales
        query = "SELECT * FROM usuarios WHERE nombre = ? AND contraseña = ?"
        password_md5 = hashlib.md5(password.encode()).hexdigest()  # Encriptar la contraseña en MD5
        cursor.execute(query, (username, password_md5))
        result = cursor.fetchone()

        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

        # Verificar si se encontraron coincidencias
        if result:
            auth_window.destroy()  # Cerrar la ventana de autenticación
            return True
        else:
            messagebox.showerror("Error", "Credenciales inválidas")
            return False

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

        self.listbox_tasks = Listbox(self, width=100, height=30)
        self.listbox_tasks.pack(padx=10, pady=10)
        self.listbox_tasks.bind("<<ListboxSelect>>", self.update_description)

        self.label_description = Label(self, text="", wraplength=700, justify="left")
        self.label_description.pack(padx=10, pady=(0, 10))


    def load_tasks(self):
        self.listbox_tasks.delete(0, "end")
        response = requests.get(f"{API_URL}/tasks", headers=self.headers)
        if response.status_code == 200:
            tareas = response.json().get("tareas")
            for tarea in tareas:
                uid = tarea.get("uid")
                titulo = tarea.get("titulo")
                estado = tarea.get("estado")
                creada = tarea.get("creada")
                actualizada = tarea.get("actualizada")
                task_text = f"{uid} | {titulo} | Estado: {estado} | Creación: {creada} | Actualización: {actualizada}"
                self.listbox_tasks.insert("end", task_text)

            if tareas:
                self.update_description_by_uid(tareas[0].get("uid"))  # Actualizar la descripción con la primera tarea

        self.update_description(None)

    def update_task(self):
        if self.current_window:
            self.current_window.destroy()  # Cierra la ventana abierta actualmente

        selected_index = self.listbox_tasks.curselection()
        if selected_index:
            tarea_text = self.listbox_tasks.get(selected_index[0])
            tarea_uid = tarea_text.split(" | ")[0]
            update_text = simpledialog.askstring("Actualizar Tarea", "Ingrese el nuevo estado:")
            if update_text:
                response = requests.get(f"{API_URL}/actualizar/{tarea_uid}", params={"estado": update_text})
                if response.status_code == 200:
                    self.load_tasks()
                    messagebox.showinfo("Información", "Tarea actualizada con éxito!")
                else:
                    messagebox.showerror("Error", "Error al actualizar la tarea")
        else:
            messagebox.showinfo("Información", "Seleccione una tarea para actualizar.")

    def delete_task(self):
        if self.current_window:
            self.current_window.destroy()  # Cierra la ventana abierta actualmente

        selected_index = self.listbox_tasks.curselection()
        if selected_index:
            tarea_text = self.listbox_tasks.get(selected_index[0])
            tarea_uid = tarea_text.split(" | ")[0]
 
            self.current_window = Toplevel(self)
            self.current_window.title("Eliminar tarea")
            self.current_window.geometry("300x150")
            self.current_window.resizable(False, False)
            self.current_window.attributes("-topmost", True)

            label_message = Label(self.current_window, text="¿Qué acción desea realizar?")
            label_message.pack(pady=10)

            button_delete_selected = Button(self.current_window, text="Eliminar tarea seleccionada", command=lambda: self.delete_selected_task(tarea_uid))
            button_delete_selected.pack(pady=5)

            button_delete_all = Button(self.current_window, text="Eliminar todas las tareas", command=self.delete_all_tasks)
            button_delete_all.pack(pady=5)

            # Centrar la ventana emergente en la pantalla
            window_width = self.current_window.winfo_reqwidth()
            window_height = self.current_window.winfo_reqheight()
            position_right = int(self.current_window.winfo_screenwidth() / 2 - window_width / 2)
            position_down = int(self.current_window.winfo_screenheight() / 2 - window_height / 2)
            self.current_window.geometry("+{}+{}".format(position_right, position_down))
        else:
            messagebox.showinfo("Información", "Seleccione una tarea para eliminar.")

    def delete_selected_task(self, uid):
        response = requests.get(f"{API_URL}/eliminar/{uid}")
        if response.status_code == 200:
            self.load_tasks()
            self.current_window.destroy()
            messagebox.showinfo("Información", "Tarea eliminada con éxito!")
        else:
            messagebox.showerror("Error", "Error al eliminar la tarea")

    def delete_all_tasks(self):
        response = requests.get(f"{API_URL}/eliminar-todas")
        if response.status_code == 200:
            self.load_tasks()
            self.current_window.destroy()
            messagebox.showinfo("Información", "Todas las tareas han sido eliminadas.")
        else:
            messagebox.showerror("Error", "Error al eliminar todas las tareas")


    def open_create_window(self):
        if self.current_window:
            self.current_window.destroy()  # Cierra la ventana abierta actualmente
        create_window = Toplevel(self)
        create_window.title("Crear tarea")
        create_window.geometry("+%d+%d" % (self.winfo_screenwidth() / 2 - 200, self.winfo_screenheight() / 2 - 150))
        create_window.grab_set()  # Bloquea la ventana principal hasta que se cierre la ventana emergente
        self.current_window = create_window

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

    def save_task(self, titulo, descripcion, estado, create_window):
        payload = {
            "titulo": str(titulo),
            "descripcion": str(descripcion),
            "estado": str(estado),
        }

        # Enviar la solicitud POST a la API
        response = requests.post(f"{API_URL}/agregar", json=payload)
        self.load_tasks()
        create_window.destroy()
        messagebox.showinfo("Información", "Tarea creada con éxito!")


    def open_search_window(self):
        if self.current_window:
            self.current_window.destroy()  # Cierra la ventana abierta actualmente
        search_window = Toplevel(self)
        search_window.title("Buscar tarea")
        search_window.geometry("+%d+%d" % (self.winfo_screenwidth() / 2 - 200, self.winfo_screenheight() / 2 - 150))
        search_window.grab_set()  # Bloquea la ventana principal hasta que se cierre la ventana emergente
        self.current_window = search_window

        label_uid = Label(search_window, text="UID:")
        label_uid.pack()
        entry_uid = Entry(search_window)
        entry_uid.pack()

        button_search = Button(search_window, text="Buscar", command=lambda: self.search_task_by_uid(entry_uid.get(), search_window))
        button_search.pack(pady=5)

        button_cancel = Button(search_window, text="Cancelar", command=self.cancel_search)
        button_cancel.pack(pady=5)

    def search_task_by_uid(self, uid, search_window):
        if uid.isdigit():
            uid = int(uid)
            response = requests.get(f"{API_URL}/buscar/{uid}")
            if response.status_code == 200:
                data = response.json()
                tarea = data.get("tarea")
                if tarea:
                    index = uid - 1
                    self.listbox_tasks.selection_clear(0, "end")
                    self.listbox_tasks.selection_set(index)
                    self.listbox_tasks.see(index)
                    self.update_description_by_uid(uid)  # Actualizar la descripción
                    messagebox.showinfo("Información", "Tarea encontrada: {}".format(tarea["titulo"]))
                else:
                    self.label_description.config(text="")  # Limpiar la descripción si no se encuentra la tarea
                    messagebox.showinfo("Información", "No se encontró ninguna tarea con el UID: {}".format(uid))
            else:
                messagebox.showerror("Error", "Error al buscar la tarea")
        else:
            messagebox.showerror("Error", "Ingrese un UID válido")

        search_window.destroy()

    def update_description_by_uid(self, uid):
        tarea = TpFinal.AdminTarea.__traer_tarea__(uid)
        if tarea:
            descripcion = f"UID: {tarea.uid}\nTítulo: {tarea.titulo}\nDescripción: {tarea.descripcion}\nEstado: {tarea.estado}\nCreada: {tarea.creada}\nActualizada: {tarea.actualizada}"
            self.label_description.config(text=descripcion)
        else:
            self.label_description.config(text="")

    def update_description(self, event):
        # Obtener el índice de la tarea seleccionada en la Listbox
        index = self.listbox_tasks.curselection()

        if index:
            # Obtener la tarea seleccionada
            tarea_text = self.listbox_tasks.get(index)
            tarea_uid = tarea_text.split(" | ")[0]
            tarea = TpFinal.AdminTarea.__traer_tarea__(int(tarea_uid))

            # Actualizar la etiqueta de descripción con los datos de la tarea
            descripcion = f"UID: {tarea.uid}\nTítulo: {tarea.titulo}\nDescripción: {tarea.descripcion}\nEstado: {tarea.estado}\nCreada: {tarea.creada}\nActualizada: {tarea.actualizada}"
            self.label_description.config(text=descripcion)
        else:
            self.label_description.config(text="")

    def cancel_search(self):
        if self.current_window:
            self.current_window.destroy()
        
    

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