import subprocess
import threading
import sys


def stream_output(process, prefix, color_code):
    """Stream output from a process with a colored prefix."""
    for line in iter(process.stdout.readline, b''):
        text = line.decode('utf-8', errors='replace').rstrip()
        print(f"\033[{color_code}m[{prefix}]\033[0m {text}", flush=True)


def run_processes(commands: dict[str, str]):
    """
    Run multiple terminal commands simultaneously.

    Args:
        commands: dict of {label: command} pairs
    """
    colors = [92, 94, 93, 91, 95, 96]  # green, blue, yellow, red, magenta, cyan
    processes = []
    threads = []

    print(f"Starting {len(commands)} processes...\n")

    for i, (label, cmd) in enumerate(commands.items()):
        color = colors[i % len(colors)]
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # merge stderr into stdout
        )
        processes.append(proc)

        # Each process gets its own thread to read output
        t = threading.Thread(
            target=stream_output,
            args=(proc, label, color),
            daemon=True
        )
        t.start()
        threads.append(t)
        print(f"\033[{color}m[{label}]\033[0m PID {proc.pid} started: {cmd}")

    print()

    try:
        # Wait for all threads to finish (i.e., all processes to exit)
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n\nShutting down all processes...")
        for proc in processes:
            proc.terminate()
        for proc in processes:
            proc.wait()
        print("All processes stopped.")
        sys.exit(0)


if __name__ == "__main__":
    # Replace these with your actual API startup commands
    commands = {
        "Frontend": "cd frontend && python main.py",
        #"Backend": "cd backend/api && uvicorn main:app --host 0.0.0.0 --port 8000",
        "Model": "cd model && uvicorn main:app --host 0.0.0.0 --port 8001",
    }

    run_processes(commands)