from __future__ import annotations

import socket
import threading
import time
import zlib
from datetime import datetime
from pathlib import Path


WATCH_DIR = r"E:\Download\AI\Test"
LOG_DIR = r"E:\Download\AI\Test"
TARGET_TEXT = "Result=OK"
SEND_TEXT = "PING"
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 9000
SCAN_INTERVAL_SECONDS = 2
FILE_ENCODING = "utf-8"
LOG_FILE_NAME = "tcp_txt_server_watcher.log"
SOCKET_TIMEOUT_SECONDS = 3.0
STARTUP_BANNER = r"""
RRRR    U   U   N   N
R   R   U   U   NN  N
RRRR    U   U   N N N
R  R    U   U   N  NN
R   R    UUU    N   N
"""


def display_startup_banner(print_func=print) -> None:
    print_func(STARTUP_BANNER)


class ClientManager:
    def __init__(self) -> None:
        self._clients = []
        self._lock = threading.Lock()

    def add(self, client_socket, address) -> None:
        with self._lock:
            self._clients.append((client_socket, address))

    def remove(self, client_socket) -> None:
        with self._lock:
            self._clients = [(sock, addr) for sock, addr in self._clients if sock is not client_socket]
        try:
            client_socket.close()
        except OSError:
            pass

    def count(self) -> int:
        with self._lock:
            return len(self._clients)

    def send_to_all(self, payload: str) -> int:
        payload_bytes = payload.encode("utf-8")
        sent_count = 0
        failed_clients = []

        with self._lock:
            clients_snapshot = list(self._clients)

        for client_socket, _address in clients_snapshot:
            try:
                client_socket.sendall(payload_bytes)
                sent_count += 1
            except OSError:
                failed_clients.append(client_socket)

        for client_socket in failed_clients:
            self.remove(client_socket)

        return sent_count


def accept_clients(server_socket, client_manager: ClientManager, stop_event: threading.Event) -> None:
    server_socket.settimeout(1.0)
    while not stop_event.is_set():
        try:
            client_socket, address = server_socket.accept()
        except socket.timeout:
            continue
        client_socket.settimeout(SOCKET_TIMEOUT_SECONDS)
        client_manager.add(client_socket, address)


def start_tcp_server(host: str, port: int, client_manager: ClientManager, stop_event: threading.Event):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen()

    accept_thread = threading.Thread(
        target=accept_clients,
        args=(server_socket, client_manager, stop_event),
        daemon=True,
    )
    accept_thread.start()
    return server_socket, accept_thread


def read_text_file(file_path: Path, encoding: str) -> str:
    return file_path.read_text(encoding=encoding)


def should_send(content: str, target_text: str) -> bool:
    return target_text in content


def append_log(
    log_path: Path,
    timestamp_text: str,
    file_path: Path,
    match_result: str,
    action_result: str,
    detail: str,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = f"{timestamp_text} | {file_path.as_posix()} | {match_result} | {action_result} | {detail}\n"
    with log_path.open("a", encoding="utf-8", newline="") as log_file:
        log_file.write(line)


def get_file_state(file_path: Path) -> tuple[int, int, int]:
    stat_result = file_path.stat()
    content_crc = zlib.crc32(file_path.read_bytes())
    return (stat_result.st_mtime_ns, stat_result.st_size, content_crc)


def collect_changed_txt_files(watch_dir: Path, known_mtimes: dict[str, tuple[int, int, int]]) -> list[Path]:
    changed_files: list[Path] = []
    for file_path in sorted(watch_dir.glob("*.txt")):
        current_state = get_file_state(file_path)
        old_state = known_mtimes.get(str(file_path))
        if old_state is None or current_state != old_state:
            changed_files.append(file_path)
    return changed_files


def update_known_mtime(file_path: Path, known_mtimes: dict[str, tuple[int, int, int]]) -> None:
    known_mtimes[str(file_path)] = get_file_state(file_path)


def build_runtime_config(
    watch_dir: Path = Path(WATCH_DIR),
    log_dir: Path = Path(LOG_DIR),
    log_file_name: str = LOG_FILE_NAME,
    target_text: str = TARGET_TEXT,
    send_text: str = SEND_TEXT,
    server_host: str = SERVER_HOST,
    server_port: int = SERVER_PORT,
    scan_interval_seconds: int = SCAN_INTERVAL_SECONDS,
    file_encoding: str = FILE_ENCODING,
) -> dict:
    log_dir.mkdir(parents=True, exist_ok=True)
    return {
        "WATCH_DIR": watch_dir,
        "LOG_PATH": log_dir / log_file_name,
        "TARGET_TEXT": target_text,
        "SEND_TEXT": send_text,
        "SERVER_HOST": server_host,
        "SERVER_PORT": server_port,
        "SCAN_INTERVAL_SECONDS": scan_interval_seconds,
        "FILE_ENCODING": file_encoding,
    }


def process_one_file(file_path: Path, config: dict, client_manager: ClientManager, log_func=None) -> str:
    log_func = log_func or append_log
    timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        content = read_text_file(file_path, config["FILE_ENCODING"])
    except Exception as exc:
        log_func(Path(config["LOG_PATH"]), timestamp_text, file_path, "READ_ERROR", "SKIPPED", str(exc))
        return "READ_ERROR"

    if not should_send(content, config["TARGET_TEXT"]):
        log_func(Path(config["LOG_PATH"]), timestamp_text, file_path, "NO_MATCH", "SKIPPED", "target text not found")
        return "NO_MATCH"

    if config["SEND_TEXT"] == "":
        log_func(Path(config["LOG_PATH"]), timestamp_text, file_path, "MATCH", "NO_ACTION", "send text is empty")
        return "NO_ACTION"

    sent_count = client_manager.send_to_all(config["SEND_TEXT"])
    if sent_count == 0:
        log_func(Path(config["LOG_PATH"]), timestamp_text, file_path, "MATCH", "NO_CLIENTS", "no connected clients")
        return "NO_CLIENTS"

    log_func(Path(config["LOG_PATH"]), timestamp_text, file_path, "MATCH", "SENT", f"sent to {sent_count} client(s)")
    return "SENT"


def run_once(
    config: dict,
    known_mtimes: dict[str, tuple[int, int, int]],
    client_manager: ClientManager,
) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    changed_files = collect_changed_txt_files(config["WATCH_DIR"], known_mtimes)
    for file_path in changed_files:
        result = process_one_file(file_path, config, client_manager)
        update_known_mtime(file_path, known_mtimes)
        results.append((str(file_path), result))
    return results


def main() -> None:
    display_startup_banner()
    config = build_runtime_config()
    if not config["WATCH_DIR"].exists():
        raise FileNotFoundError(f"watch directory not found: {config['WATCH_DIR']}")

    client_manager = ClientManager()
    stop_event = threading.Event()
    server_socket, _accept_thread = start_tcp_server(
        config["SERVER_HOST"],
        config["SERVER_PORT"],
        client_manager,
        stop_event,
    )

    known_mtimes: dict[str, tuple[int, int, int]] = {}
    try:
        while True:
            run_once(config, known_mtimes, client_manager)
            time.sleep(config["SCAN_INTERVAL_SECONDS"])
    finally:
        stop_event.set()
        server_socket.close()


if __name__ == "__main__":
    main()
