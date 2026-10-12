# gui/components/stream_dialog.py
import customtkinter as ctk

class StreamSourceDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_select_callback):
        super().__init__(parent)
        self.title("Select Table Video Source")
        self.geometry("320x220")
        self.configure(fg_color="#1E1E1E")
        self.attributes("-topmost", True)
        self.on_select_callback = on_select_callback

        lbl_title = ctk.CTkLabel(
            self,
            text="Enter Camera Index / ID:",
            font=("Segoe UI", 12, "bold"),
            text_color="#FFFFFF"
        )
        lbl_title.pack(pady=(15, 5))

        lbl_hint = ctk.CTkLabel(
            self,
            text="Usually 0 or 1 for webcams / virtual streams.",
            font=("Segoe UI", 10),
            text_color="#888888"
        )
        lbl_hint.pack(pady=(0, 10))

        # Pole do wpisania numeru indeksu (domyślnie "0")
        self.index_entry = ctk.CTkEntry(
            self,
            font=("Segoe UI", 14),
            justify="center",
            width=100,
            height=32
        )
        self.index_entry.insert(0, "0")
        self.index_entry.pack(pady=5)

        btn_confirm = ctk.CTkButton(
            self,
            text="Connect Stream",
            font=("Segoe UI", 11, "bold"),
            fg_color="#00FF66",
            hover_color="#00CC52",
            text_color="#121212",
            command=self.confirm_selection
        )
        btn_confirm.pack(pady=15, ipadx=10, ipady=4)

    def confirm_selection(self):
        val = self.index_entry.get().strip()
        try:
            # Próbujemy przekonwertować wpisaną wartość na liczbę (indeks kamery)
            camera_id = int(val)
        except ValueError:
            # Jeśli wpisano coś innego, przekazujemy tekstowo
            camera_id = val

        self.on_select_callback(camera_id)
        self.destroy()