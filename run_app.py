import os
import sys
import socket
import webbrowser
import threading
import streamlit.web.cli as stcli
from pathlib import Path

def find_free_port(default=8501):
    port = default
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1

if __name__ == "__main__":
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

    
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = Path(__file__).parent.resolve()

    source_code = os.path.join(base_path, "source_code.py")

    port = find_free_port(8501)
    url = f"http://127.0.0.1:{port}"

    threading.Timer(5, lambda: webbrowser.open(url)).start()

    sys.argv = [
        "streamlit",
        "run", source_code,
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
    ]


    sys.exit(stcli.main())

