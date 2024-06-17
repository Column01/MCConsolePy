# MCConsolePy

MCConsolePy is a Tkinter app designed to demonstrate the functionality of the MCConsoleAPI project. It provides a graphical user interface to interact with the MCConsoleAPI.

> [!NOTE]
> This project is a WIP and lacks some QOL features that you may want to see added. For example, the servers list is only populated at application startup. Use at your own risk and manage your expectations.
> This app exists really just to test the backend, I envisioned people would make frontends in other languages that will be better than anything I could ever make!

## Prerequisites

Before running MCConsolePy, ensure that you have the following prerequisite installed:

- Python 3.8 or higher

## Installation

1. Set up the MCConsoleAPI backend:
   - Follow the setup instructions in the [MCConsoleAPI repository](https://github.com/Column01/MCConsoleAPI) to ensure that the backend is properly configured and running on your Minecraft server.

2. Clone the MCConsolePy repository:

   ```bash
   git clone https://github.com/Column01/MCConsolePy.git
   ```

3. Navigate to the project directory:

   ```bash
   cd MCConsolePy
   ```

4. Copy the MCConsoleAPI key:
   - During the setup of the MCConsoleAPI project, you should have generated an API key.
   - Create a new file named `api_key.txt` in the root directory of the MCConsolePy repository.
   - Open the `api_key.txt` file and paste the MCConsoleAPI key into it, ensuring that there are no extra spaces or newlines.
   - **Note:** I strongly recommend going to the `/docs` endpoint of the console API and using the web interface to authenticate with the admin key and generate a new user API key to use here, but the admin key works too if security is not a concern

5. Install the required dependencies using pip:

   ```bash
   pip install -r requirements.txt
   ```

   Alternatively, you can manually install the `requests` library using PyPI:

   ```bash
   pip install requests
   ```

6. Check the `config.json` and ensure that the `url` and `port` are correctly set for the API backend

## Usage

To run the MCConsolePy app, follow these steps:

1. Open a terminal or command prompt.

2. Navigate to the project directory:

   ```bash
   cd MCConsolePy
   ```

3. Run the `main.py` script:

   ```bash
   python main.py
   ```

   This will launch the MCConsolePy GUI.

4. Interact with the app using the provided graphical interface.

## Acknowledgments

- MCConsolePy is built using the [Tkinter](https://docs.python.org/3/library/tkinter.html) library for creating the graphical user interface.
- The app demonstrates the functionality of the [MCConsoleAPI](https://github.com/Column01/MCConsoleAPI) project.
