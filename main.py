import datetime
import json
import threading
import tkinter as tk
from tkinter import ttk

import requests


class App(tk.Tk):
    def __init__(self, config):
        super().__init__()

        self.config = config

        self._url = self.config.get("url", "127.0.0.1")
        self.port = self.config.get("port", 5000)
        self.url = f"http://{self._url}:{self.port}"

        print(f"Loaded settings from config. API URL: {self.url}")

        self.title("MCConsolePy")
        self.geometry("600x400")

        # Set dark theme
        self.configure(bg="black")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background="black", foreground="white")
        style.configure("TFrame", background="black")
        style.configure("TButton", background="gray25", foreground="white")
        style.map("TButton", foreground=[("active", "black")])
        style.configure("TEntry", fieldbackground="gray25", foreground="white")

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
        self.side_panel_frame = ttk.Frame(self.main_frame, width=200)
        self.side_panel_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.side_panel = tk.Listbox(
            self.side_panel_frame,
            height=20,
            width=20,
            bg="black",
            fg="white",
            selectbackground="gray25",
            selectforeground="white",
        )
        self.side_panel.pack(fill=tk.BOTH, expand=True)

        # Bottom frame
        self.bottom_frame = ttk.Frame(self)
        self.bottom_frame.pack(fill=tk.X, padx=10, pady=5)

        # Text entry
        self.entry = ttk.Entry(self.bottom_frame, width=50)
        self.entry.pack(side=tk.LEFT, fill=tk.X, padx=5, expand=True)

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

        # Threads are daemon threads because the requests block,
        # causing indefinite hanging when trying to close the application
        # Start the output streaming thread
        self.stream_stop_event = threading.Event()
        self.stream_thread = threading.Thread(target=self.stream_output)
        self.stream_thread.daemon = True  # Set the thread as a daemon thread
        self.stream_thread.start()

        # Start the player list update thread
        self.player_list_stop_event = threading.Event()
        self.player_list_thread = threading.Thread(target=self.update_player_list)
        self.player_list_thread.daemon = True  # Set the thread as a daemon thread
        self.player_list_thread.start()

    def submit_text(self):
        text = self.entry.get()
        if text:
            self.text_display.configure(state="normal")  # Enable editing

            # Format the input text with timestamp and prefix
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_text = f"[{timestamp}] [MCConsole] {text}"

            self.text_display.insert(tk.END, formatted_text + "\n")
            self.text_display.configure(state="disabled")  # Disable editing
            self.entry.delete(0, tk.END)

            # Send HTTP POST request with the input text as a query parameter and API key
            url = f"{self.url}/input"
            headers = {"x-api-key": self.api_key} if self.api_key else None
            params = {"command": text}
            try:
                response = requests.post(url, headers=headers, params=params)
                response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
                print("Input sent successfully")
            except requests.exceptions.RequestException as e:
                print(f"Error occurred while sending input: {e}")

    def stream_output(self):
        url = f"{self.url}/output"
        headers = {"x-api-key": self.api_key} if self.api_key else None
        try:
            with requests.get(url, headers=headers, stream=True) as response:
                buffer = ""
                for chunk in response.iter_content(chunk_size=1):
                    if self.stream_stop_event.is_set():
                        break
                    if chunk:
                        buffer += chunk.decode("utf-8")
                        if "\n" in buffer:
                            lines = buffer.split("\n")
                            buffer = lines[
                                -1
                            ]  # Keep the last incomplete line in the buffer
                            for line in lines[:-1]:
                                try:
                                    json_data = json.loads(line)
                                    output_line = json_data.get("line", "")
                                    self.text_display.configure(
                                        state="normal"
                                    )  # Enable editing
                                    self.text_display.insert(tk.END, output_line + "\n")
                                    self.text_display.configure(
                                        state="disabled"
                                    )  # Disable editing
                                    self.text_display.see(tk.END)  # Scroll to the end
                                except json.JSONDecodeError:
                                    print(f"Error decoding JSON: {line}")
        except requests.exceptions.RequestException as e:
            if not self.stream_stop_event.is_set():
                print(f"Error occurred during streaming: {e}")

    def update_player_list(self):
        url = f"{self.url}/players"
        headers = {"x-api-key": self.api_key} if self.api_key else None
        while not self.player_list_stop_event.is_set():
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
                json_data = response.json()
                player_list = json_data.get("players", [])
                self.side_panel.delete(0, tk.END)  # Clear the existing player list
                for player_name in player_list:
                    self.side_panel.insert(tk.END, player_name)
            except requests.exceptions.RequestException as e:
                print(f"Error occurred while retrieving player list: {e}")

            # Wait for 3 seconds before the next update
            self.player_list_stop_event.wait(3)

    def on_closing(self):
        # Lazily try to join threads and just exit if we can't, they're daemon threads anyways
        self.stream_stop_event.set()
        self.stream_thread.join(timeout=1)
        self.player_list_stop_event.set()
        self.player_list_thread.join(timeout=1)
        self.destroy()
        exit()


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
