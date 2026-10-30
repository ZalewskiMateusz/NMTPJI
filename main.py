import threading
from tkinter import messagebox
from gui.app_window import AppWindow
from utils.updater import AppUpdater


def check_updates_background(app):
    """Checks for updates in a background thread and prompts the user if available."""
    has_update, version, url = AppUpdater.check_for_updates()
    if has_update:
        # app.after ensures the prompt runs safely on the main GUI thread
        app.after(0, lambda: prompt_update(app, version, url))


def prompt_update(app, version, url):
    """Displays the update confirmation dialog."""
    answer = messagebox.askyesno(
        "Update Available",
        f"A new version has been detected ({version}). Do you want to download and install it now?",
        parent=app
    )
    if answer:
        AppUpdater.download_and_update(url)


if __name__ == "__main__":
    app = AppWindow()

    # Start the update check in a background thread so it doesn't freeze startup
    threading.Thread(target=check_updates_background, args=(app,), daemon=True).start()

    app.mainloop()