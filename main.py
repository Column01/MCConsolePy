import datetime
import json
import os
import tkinter as tk
from tkinter import messagebox, ttk

import requests

from server import Server


class App(tk.Tk):
    def __init__(self, config):
        super().__init__()

        self.config = config

        self._url = self.config.get("url", "127.0.0.1")
        self.port = self.config.get("port", 5000)
        self.url = f"http://{self._url}:{self.port}"

        self.session = requests.Session()

        # Initialize servers dictionary
        self.servers = {}
        # The previous line put into the output
        self.prev_line = {}

        print(f"Loaded settings from config. API URL: {self.url}")

        self.title("MCConsolePy")
        self.geometry("800x600")

        # Set dark theme
        self.configure(bg="black")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background="black", foreground="white")
        style.configure("TFrame", background="black")
        style.configure("TButton", background="gray25", foreground="white")
        style.map("TButton", foreground=[("active", "black")])
        style.configure("TEntry", fieldbackground="gray25", foreground="white")
        style.configure("Custom.TMenubutton", background="gray25", foreground="white")
        style.map(
            "Custom.TMenubutton",
            background=[("active", "white")],
            foreground=[("active", "black")],
        )

        # Create menu bar
        self.menu_bar = tk.Menu(self)
        self.configure(menu=self.menu_bar)

        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Exit", command=self.on_closing)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # Refresh servers
        self.menu_bar.add_command(label="Refresh Servers", command=self.refresh_servers)
        # Start a server
        self.menu_bar.add_command(label="Start a Server", command=self.start_server)

        # Create main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Text display box
        self.text_display = tk.Text(
            self.main_frame,
            height=20,
            width=50,
            state="disabled",
            bg="black",
            fg="white",
            insertbackground="white",
        )
        self.text_display.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10
        )

        # Side panel
        self.side_panel_frame = ttk.Frame(self.main_frame, width=210)
        self.side_panel_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.side_panel = tk.Listbox(
            self.side_panel_frame,
            height=20,
            width=20,
            bg="black",
            fg="white",
            selectbackground="gray25",
            selectforeground="white",
            font=("Segoe UI", 12),
        )
        self.side_panel.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

        # Server selection dropdown
        self.server_var = tk.StringVar()
        # Server selection dropdown
        self.server_var = tk.StringVar()
        self.server_var.trace("w", self.on_server_change)
        self.server_dropdown = ttk.OptionMenu(
            self.side_panel_frame,
            self.server_var,
            "No servers running",
            style="Custom.TMenubutton",
        )
        self.server_dropdown.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Bottom frame
        self.bottom_frame = ttk.Frame(self)
        self.bottom_frame.pack(fill=tk.X)

        # Text entry
        self.entry = ttk.Entry(self.bottom_frame, width=70, font=("Segoe UI", 12))
        self.entry.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=10, expand=True)
        # Pressing enter submits textbox
        self.entry.bind("<Return>", self.submit_text)

        # Submit button
        self.submit_button = ttk.Button(
            self.bottom_frame, text="Submit", command=self.submit_text
        )
        self.submit_button.pack(side=tk.LEFT, padx=5)

        # Update minimum window size
        self.update_idletasks()
        self.minsize(self.winfo_width(), self.winfo_height())

        # Load the API key from api_key.txt
        try:
            with open("api_key.txt", "r") as file:
                self.api_key = file.read().strip()
        except FileNotFoundError:
            exit(
                "API key file not found. Please create api_key.txt with your API key in it."
            )

        # Get the list of running servers
        self.get_server_list()

    def get_server_list(self):
        # Remove no longer running servers
        to_remove = [
            server
            for server in self.servers.keys()
            if self.servers[server].stop_event.is_set()
        ]
        _ = [self.servers.pop(server, None) for server in to_remove]

        url = f"{self.url}/servers"
        headers = {"x-api-key": self.api_key} if self.api_key else None
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            server_list = response.json().get("servers", [])
            if server_list:
                for server_data in server_list:
                    server_name = server_data["name"]
                    if server_name not in self.servers:
                        self.servers[server_name] = Server(self, server_name)
                self.server_dropdown["menu"].delete(0, "end")
                for server_name in self.servers.keys():
                    self.server_dropdown["menu"].add_command(
                        label=server_name,
                        command=lambda value=server_name: self.server_var.set(value),
                    )
                # Select the first server by default
                self.server_var.set(next(iter(self.servers.keys())))
                self.update_ui()
            else:
                print("No servers are running")
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while retrieving server list: {e}")

    def on_server_change(self, *args):
        self.clear_output()
        self.clear_player_list()
        self.update_ui()
        # Scroll to the end
        self.text_display.see(tk.END)

    def clear_output(self):
        self.text_display.configure(state="normal")
        self.text_display.delete("1.0", tk.END)
        self.text_display.configure(state="disabled")
        self.prev_line = {}

    def clear_player_list(self):
        self.side_panel.delete(0, tk.END)

    def update_ui(self):
        selected_server = self.server_var.get()
        if selected_server:
            server = self.servers.get(selected_server, None)
            if server is not None:
                output_lines = server.get_output()
                self.text_display.configure(state="normal")  # Enable editing

                for line_data in output_lines:
                    line = line_data["line"]
                    timestamp = line_data["timestamp"]
                    if self.prev_line.get("line") is None or (
                        line != self.prev_line["line"]
                        and timestamp > self.prev_line["timestamp"]
                    ):
                        self.text_display.insert(tk.END, line + "\n")
                        # Scroll to the end
                        self.text_display.see(tk.END)
                        self.prev_line = line_data

                self.text_display.configure(state="disabled")  # Disable editing

                player_list = server.get_player_list()
                self.side_panel.delete(0, tk.END)  # Clear the existing player list
                for player_name in player_list:
                    self.side_panel.insert(tk.END, player_name)

        self.after(100, self.update_ui)  # Schedule the next update after 100ms

    def submit_text(self, event=None):
        text = self.entry.get()
        if text:
            self.text_display.configure(state="normal")  # Enable editing

            # Format the input text with timestamp and prefix
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_text = f"[{timestamp}] [MCConsolePy] {text}"

            self.text_display.insert(tk.END, formatted_text + "\n")
            self.text_display.configure(state="disabled")  # Disable editing
            self.entry.delete(0, tk.END)

            # Send HTTP POST request with the input text as a query parameter and API key
            url = f"{self.url}/input"
            headers = {"x-api-key": self.api_key} if self.api_key else None
            params = {"command": text, "server_name": self.server_var.get()}
            try:
                response = requests.post(url, headers=headers, params=params)
                response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
                print("Input sent successfully")
            except requests.exceptions.RequestException as e:
                print(f"Error occurred while sending input: {e}")

    def refresh_servers(self):
        self.get_server_list()

    def start_server(self):
        start_server_window = tk.Toplevel(self)
        start_server_window.title("Start a Server")
        start_server_window.geometry("300x175")
        start_server_window.configure(bg="black")

        # Server name label and entry
        server_name_label = ttk.Label(start_server_window, text="Server Name:")
        server_name_label.pack(pady=5)
        server_name_entry = ttk.Entry(start_server_window)
        server_name_entry.pack(pady=5)

        # Server path label and entry
        server_path_label = ttk.Label(
            start_server_window, text="Server Path (optional):"
        )
        server_path_label.pack(pady=5)
        server_path_entry = ttk.Entry(start_server_window)
        server_path_entry.pack(pady=5)

        def start_server_submit():
            server_name = server_name_entry.get()
            server_path = server_path_entry.get()

            if server_name:
                url = f"{self.url}/start_server"
                headers = {"x-api-key": self.api_key} if self.api_key else None
                params = {"server_name": server_name}
                if server_path:
                    params["server_path"] = server_path

                try:
                    response = requests.post(url, headers=headers, params=params)
                    if response.status_code == 404:
                        error_message = response.json().get("message", "Server not found")
                        messagebox.showerror("Error", error_message)
                    elif response.status_code == 400:
                        error_message = response.json().get(
                            "message", "Error starting the server"
                        )
                        messagebox.showerror("Error", error_message)
                    else:
                        response.raise_for_status()  # Raise an exception for other 4xx or 5xx status codes
                        success_message = response.json().get(
                            "message", "Server started successfully"
                        )
                        messagebox.showinfo("Success", success_message)
                        start_server_window.destroy()
                        self.refresh_servers()
                except requests.exceptions.RequestException as e:
                    print(f"Error occurred while starting the server: {e}")
            else:
                messagebox.showerror("Error", "Please enter a server name")

        # Start Server button
        start_server_button = ttk.Button(
            start_server_window, text="Start Server", command=start_server_submit
        )
        start_server_button.pack(pady=10)

    def on_closing(self):
        for server in self.servers.values():
            server.stop()
        self.destroy()
        os._exit(0)


if __name__ == "__main__":
    config = {}
    with open("config.json", "r") as fp:
        config = json.load(fp)

    app = App(config)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.on_closing()
