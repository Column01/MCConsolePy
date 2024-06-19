import datetime
import json
import os
import tkinter as tk
from tkinter import ttk

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
            insertbackground="white"
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
            font=("Segoe UI", 12)
        )
        self.side_panel.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

        # Server selection dropdown
        self.server_var = tk.StringVar()
        self.server_dropdown = ttk.OptionMenu(
            self.side_panel_frame,
            self.server_var,
            "No servers running",
            style="Custom.TMenubutton",
        )
        self.server_dropdown.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        self.server_dropdown.bind("<<ComboboxSelected>>", self.on_server_change)

        # Bottom frame
        self.bottom_frame = ttk.Frame(self)
        self.bottom_frame.pack(fill=tk.X)

        # Text entry
        self.entry = ttk.Entry(self.bottom_frame, width=70, font=("Segoe UI", 12))  # Increase width and font size
        self.entry.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=10, expand=True)
        self.entry.bind("<Return>", self.submit_text)  # Bind Enter key to submit_text method

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

        # Initialize servers dictionary
        self.servers = {}
        # The previous line put into the output
        self.prev_line = None

        # Get the list of running servers
        self.get_server_list()

    def get_server_list(self):
        url = f"{self.url}/servers"
        headers = {"x-api-key": self.api_key} if self.api_key else None
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            server_list = response.json().get("servers", [])
            if server_list:
                for server_data in server_list:
                    server_name = server_data["name"]
                    self.servers[server_name] = Server(self, server_name)
                self.server_dropdown["menu"].delete(0, "end")
                for server_name in self.servers.keys():
                    self.server_dropdown["menu"].add_command(
                        label=server_name,
                        command=lambda value=server_name: self.server_var.set(value),
                    )
                self.server_var.set(
                    next(iter(self.servers.keys()))
                )  # Select the first server by default
                self.update_ui()
            else:
                print("No servers are running")
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while retrieving server list: {e}")

    def on_server_change(self, event):
        self.clear_output()
        self.clear_player_list()
        self.update_ui()

    def clear_output(self):
        self.text_display.configure(state="normal")
        self.text_display.delete("1.0", tk.END)
        self.text_display.configure(state="disabled")
        self.prev_line = None

    def clear_player_list(self):
        self.side_panel.delete(0, tk.END)

    def strip(self, line):
        ret = line.replace("\r\n", "")
        return ret

    def update_ui(self):
        selected_server = self.server_var.get()
        if selected_server:
            server = self.servers[selected_server]
            output_lines = server.get_output()
            self.text_display.configure(state="normal")  # Enable editing

            for line_data in output_lines:
                line = line_data["line"]
                timestamp = line_data["timestamp"]
                if self.prev_line is None or (
                    line != self.prev_line["line"]
                    and timestamp >= self.prev_line["timestamp"]
                ):
                    self.text_display.insert(tk.END, line + "\n")
                    self.prev_line = line_data

            self.text_display.configure(state="disabled")  # Disable editing
            self.text_display.see(tk.END)  # Scroll to the end

            player_list = server.get_player_list()
            self.side_panel.delete(0, tk.END)  # Clear the existing player list
            for player_name in player_list:
                self.side_panel.insert(tk.END, player_name)

        self.after(1000, self.update_ui)  # Schedule the next update after 1 second

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
