from __future__ import annotations

import socket
import threading
import time
from datetime import datetime
from pathlib import Path


WATCH_DIR = r"E:\Download\AI\Test"
LOG_DIR = r"E:\Download\AI\Test"
FILE_NAME_PATTERN = "*.txt"

MATCH_TEXT_1 = "Result=OK"
RESPONSE_TEXT_1 = "PASS"
MATCH_TEXT_2 = "Result=NG"
RESPONSE_TEXT_2 = "FAIL"
DEFAULT_RESPONSE_TEXT = "WAIT_TIMEOUT"

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 9000
SEARCH_TIMEOUT_SECONDS = 5
SEARCH_RETRY_INTERVAL_SECONDS = 1
FILE_ENCODING = "utf-8"
LOG_FILE_NAME = "tcp_txt_server_watcher.log"
REQUEST_BUFFER_SIZE = 4096
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


def read_text_file(file_path: Path, encoding: str) -> str:
    return file_path.read_text(encoding=encoding)


def should_send(content: str, target_text: str) -> bool:
    return target_text in content


def append_log(
    log_path: Path,
    timestamp_text: str,
    file_path_or_request: str,
    match_result: str,
    action_result: str,
    detail: str,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = f"{timestamp_text} | {file_path_or_request} | {match_result} | {action_result} | {detail}\n"
    with log_path.open("a", encoding="utf-8", newline="") as log_file:
        log_file.write(line)


def build_runtime_config(
    watch_dir: Path = Path(WATCH_DIR),
    log_dir: Path = Path(LOG_DIR),
    log_file_name: str = LOG_FILE_NAME,
    file_name_pattern: str = FILE_NAME_PATTERN,
    match_text_1: str = MATCH_TEXT_1,
    response_text_1: str = RESPONSE_TEXT_1,
    match_text_2: str = MATCH_TEXT_2,
    response_text_2: str = RESPONSE_TEXT_2,
    default_response_text: str = DEFAULT_RESPONSE_TEXT,
    server_host: str = SERVER_HOST,
    server_port: int = SERVER_PORT,
    search_timeout_seconds: float = SEARCH_TIMEOUT_SECONDS,
    search_retry_interval_seconds: float = SEARCH_RETRY_INTERVAL_SECONDS,
    file_encoding: str = FILE_ENCODING,
    request_buffer_size: int = REQUEST_BUFFER_SIZE,
) -> dict:
    log_dir.mkdir(parents=True, exist_ok=True)
    return {
        "WATCH_DIR": watch_dir,
        "LOG_PATH": log_dir / log_file_name,
        "FILE_NAME_PATTERN": file_name_pattern,
        "MATCH_TEXT_1": match_text_1,
        "RESPONSE_TEXT_1": response_text_1,
        "MATCH_TEXT_2": match_text_2,
        "RESPONSE_TEXT_2": response_text_2,
        "DEFAULT_RESPONSE_TEXT": default_response_text,
        "SERVER_HOST": server_host,
        "SERVER_PORT": server_port,
        "SEARCH_TIMEOUT_SECONDS": search_timeout_seconds,
        "SEARCH_RETRY_INTERVAL_SECONDS": search_retry_interval_seconds,
        "FILE_ENCODING": file_encoding,
        "REQUEST_BUFFER_SIZE": request_buffer_size,
    }


def search_once(request_text: str, config: dict) -> tuple[str, str, str] | None:
    request_text = request_text.strip()
    if request_text == "":
        return None

    watch_dir = Path(config["WATCH_DIR"])
    for file_path in sorted(watch_dir.glob(config["FILE_NAME_PATTERN"])):
        if request_text not in file_path.name:
            continue

        content = read_text_file(file_path, config["FILE_ENCODING"])
        if should_send(content, config["MATCH_TEXT_1"]):
            return (config["RESPONSE_TEXT_1"], "MATCH_1", str(file_path))
        if should_send(content, config["MATCH_TEXT_2"]):
            return (config["RESPONSE_TEXT_2"], "MATCH_2", str(file_path))

    return None


def find_reply_for_request(
    request_text: str,
    config: dict,
    monotonic_func=time.monotonic,
    sleep_func=time.sleep,
) -> tuple[str, str, str]:
    start_time = monotonic_func()
    timeout_seconds = config["SEARCH_TIMEOUT_SECONDS"]
    retry_interval_seconds = config["SEARCH_RETRY_INTERVAL_SECONDS"]

    while True:
        search_result = search_once(request_text, config)
        if search_result is not None:
            return search_result

        elapsed_seconds = monotonic_func() - start_time
        if elapsed_seconds >= timeout_seconds:
            return (
                config["DEFAULT_RESPONSE_TEXT"],
                "TIMEOUT",
                "no matching file content before timeout",
            )

        remaining_seconds = timeout_seconds - elapsed_seconds
        sleep_func(min(retry_interval_seconds, remaining_seconds))


def handle_client_request(client_socket, address, config: dict, log_func=append_log) -> None:
    try:
        while True:
            try:
                request_bytes = client_socket.recv(config["REQUEST_BUFFER_SIZE"])
            except TimeoutError:
                continue
            except socket.timeout:
                continue
            if not request_bytes:
                break

            request_text = request_bytes.decode("utf-8", errors="replace").strip()
            response_text, match_result, detail = find_reply_for_request(request_text, config)
            client_socket.sendall(response_text.encode("utf-8"))

            timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_func(
                Path(config["LOG_PATH"]),
                timestamp_text,
                request_text,
                match_result,
                "REPLIED",
                f"{detail} | client={address}",
            )
    finally:
        try:
            client_socket.close()
        except OSError:
            pass


def accept_clients(server_socket, config: dict, stop_event: threading.Event) -> None:
    server_socket.settimeout(1.0)
    while not stop_event.is_set():
        try:
            client_socket, address = server_socket.accept()
        except socket.timeout:
            continue
        client_thread = threading.Thread(
            target=handle_client_request,
            args=(client_socket, address, config),
            daemon=True,
        )
        client_thread.start()


def start_tcp_server(config: dict, stop_event: threading.Event):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((config["SERVER_HOST"], config["SERVER_PORT"]))
    server_socket.listen()

    accept_thread = threading.Thread(
        target=accept_clients,
        args=(server_socket, config, stop_event),
        daemon=True,
    )
    accept_thread.start()
    return server_socket, accept_thread


def main() -> None:
    display_startup_banner()
    config = build_runtime_config()
    if not Path(config["WATCH_DIR"]).exists():
        raise FileNotFoundError(f"watch directory not found: {config['WATCH_DIR']}")

    stop_event = threading.Event()
    server_socket, _accept_thread = start_tcp_server(config, stop_event)
    try:
        while True:
            time.sleep(1)
    finally:
        stop_event.set()
        server_socket.close()


if __name__ == "__main__":
    main()
