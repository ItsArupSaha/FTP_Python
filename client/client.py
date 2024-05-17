import socket
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import time
import threading

# Define server address and port
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5001
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"

# Global variable for client socket
client_socket = None

def upload_files():
    global client_socket
    if not client_socket:
        messagebox.showerror("Connection Error", "You are not connected to the server.")
        return

    filepaths = filedialog.askopenfilenames()
    if not filepaths:
        return

    for filepath in filepaths:
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        client_socket.send(f"UPLOAD{SEPARATOR}{filename}{SEPARATOR}{filesize}".encode())
        print(f"Sent UPLOAD command for {filename}")

        with open(filepath, "rb") as f:
            while True:
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    break
                client_socket.sendall(bytes_read)
            print(f"File {filename} uploaded successfully.")
            # Add a small delay to allow the server to process each file individually
            time.sleep(0.1)
    messagebox.showinfo("Success", "All files uploaded successfully.")

def download_file():
    global client_socket
    if not client_socket:
        messagebox.showerror("Connection Error", "You are not connected to the server.")
        return

    # Function to handle file selection and download
    def handle_file_selection():
        print("Requesting list of available files...")
        # Request the list of available files from the server
        client_socket.send("LIST_FILES".encode())
        response = client_socket.recv(BUFFER_SIZE).decode()
        print("Received response from server:", response)
        files = response.split(SEPARATOR)
        
        if not files:
            messagebox.showinfo("No Files", "No files available for download.")
            return

        # Create a dialog window to display the list of files
        file_selection_dialog = tk.Toplevel()
        file_selection_dialog.title("Select File to Download")

        # Create a listbox to display the files
        file_listbox = tk.Listbox(file_selection_dialog, width=50)
        file_listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Add files to the listbox
        for filename in files:
            file_listbox.insert(tk.END, filename)

        def on_download():
            selection = file_listbox.curselection()
            if selection:
                index = selection[0]
                filename = file_listbox.get(index)
                print("User selected file:", filename)
                # Start a new thread to download the selected file
                threading.Thread(target=download_selected_file, args=(filename,)).start()
                file_selection_dialog.destroy()  # Close the file selection dialog
            else:
                messagebox.showerror("Selection Error", "Please select a file to download.")

        # Create a button to download the selected file
        download_button = tk.Button(file_selection_dialog, text="Download", command=on_download)
        download_button.pack(pady=10)

    # Schedule the function to be called in the main GUI thread
    handle_file_selection()

def download_selected_file(filename):
    global client_socket
    try:
        client_socket.send(f"DOWNLOAD{SEPARATOR}{filename}".encode())
        response = client_socket.recv(BUFFER_SIZE).decode()
        if response.startswith("File not found"):
            messagebox.showerror("Error", response)
            return

        file_info = response.split(SEPARATOR)
        filename = file_info[0]
        filesize = int(file_info[1])

        # Create a 'downloaded files' directory if it doesn't exist
        downloaded_files_dir = os.path.join(os.path.dirname(__file__), 'downloaded files')
        os.makedirs(downloaded_files_dir, exist_ok=True)

        filepath = os.path.join(downloaded_files_dir, filename)
        with open(filepath, "wb") as f:
            bytes_received = 0
            while bytes_received < filesize:
                bytes_read = client_socket.recv(BUFFER_SIZE)
                if not bytes_read:
                    break
                f.write(bytes_read)
                bytes_received += len(bytes_read)
        messagebox.showinfo("Success", f"File '{filename}' downloaded successfully.")
    except Exception as e:
        print(f"Error: {e}")

def connect_to_server():
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        messagebox.showinfo("Success", "Connected to the server.")
    except ConnectionRefusedError:
        messagebox.showerror("Connection Error", "The server is not started yet. Please start the server first.")

# Create the GUI
app = tk.Tk()
app.title("File Client")

connect_btn = tk.Button(app, text="Connect to Server", command=connect_to_server)
connect_btn.pack(pady=10)

upload_btn = tk.Button(app, text="Upload Files", command=upload_files)
upload_btn.pack(pady=10)

download_btn = tk.Button(app, text="Download File", command=download_file)
download_btn.pack(pady=10)

app.mainloop()
