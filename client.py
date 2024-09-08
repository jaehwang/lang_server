# client.py
import argparse
import json
import subprocess
import threading
import time
import os

from urllib.parse import urlparse

def read_response(process):
    # Read the Content-Length header
    content_length_header = process.stdout.readline().decode('utf-8').strip()
    content_length = int(content_length_header.split(': ')[1])
    print("Content-Length:", content_length, "\n")

    # Read the empty line
    process.stdout.readline()   
    
    # Read the response based on the Content-Length
    response = process.stdout.read(content_length).decode('utf-8')

    return json.loads(response)

def receive_notification_and_response(process):
    response = read_response(process)

    while "id" not in response:
        print("RECV Notification:", response, "\n")
        response = read_response(process)
    
    print("RECV Response:", response, "\n")
    

def send_notification(process, method, params):
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params
    }
    print("SEND Notification:", request, "\n")

    request_str = json.dumps(request) + '\n'
 
    content_length = len(request_str)
    headers = f"Content-Length: {content_length}\r\n\r\n"
    process.stdin.write(headers.encode('utf-8'))
    
    process.stdin.write(request_str.encode('utf-8'))
    process.stdin.flush()

req_id = 1

def send_request(process, method, params):
    global req_id

    request = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method,
        "params": params
    }
    req_id += 1

    print("SEND Request:", request, "\n")

    request_str = json.dumps(request) + '\n'
 
    content_length = len(request_str)
    headers = f"Content-Length: {content_length}\r\n\r\n"
    process.stdin.write(headers.encode('utf-8'))
    
    process.stdin.write(request_str.encode('utf-8'))
    process.stdin.flush()
    
    receive_notification_and_response(process)

def open_file(process, uri):
    parsed_uri = urlparse(uri)
    file_path = parsed_uri.path

    # Read the file content
    with open(file_path, 'r') as file:
        file_text = file.read()

    # Send a textDocument/completion request
    send_notification(process, "textDocument/didOpen", {
        "textDocument": {"uri": uri,
                         "languageId": "c",
                         "version": 1,
                         "text": file_text
                        }
    })

def open_files(process, files):
    for file in files:
        open_file(process, file)

# def do_main(process):
#     main_c = "file:///Users/jaehwang/work/ai_coding/sanbox_copilot/main.c"
 
#     # Send another request
#     send_request(process, "textDocument/definition", {
#         "textDocument": {"uri": main_c},
#         "position": {"line": 19-1, "character": 15-1} # zero-based line and character
#     })

def get_files(comile_commands_dir):
    compile_commands = os.path.join(comile_commands_dir, 'compile_commands.json')
    with open(compile_commands, 'r') as f:
        compile_commands = json.load(f)
    
    files = []
    for compile_command in compile_commands:
        files.append('file://'+compile_command['file'])
    
    return files
        
def run_client():
   
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile-commands-dir", type=str, help="Path to the compile_commands.json directory")
    args = parser.parse_args()

    if args.compile_commands_dir is None:
        # print("Please provide the compile_commands_dir")
        parser.print_help()
        return
    
    with open('err.txt', 'w') as err_file:   
        process = subprocess.Popen(
            ['clangd', '--log=verbose', '--background-index', '--clang-tidy',
                       '--completion-style=detailed',
                       '--compile-commands-dir='+args.compile_commands_dir],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=err_file
        )

        # Initialize the server
        send_request(process, "initialize", {
            "processId": None,
            "rootUri": None,
            "capabilities": {}
        })
        
        open_files(process, get_files(args.compile_commands_dir))

        # Wait for seconds
        time.sleep(1)

        # Send another request
        send_request(process, "textDocument/definition", {
            "textDocument": {"uri": "file:///Users/jaehwang/work/ai_coding/sanbox_copilot/main.c"},
            "position": {"line": 19-1, "character": 15-1} # zero-based line and character
        })
                
        # Shutdown the server
        send_request(process, "shutdown", {})

        process.stdin.close()
        process.stdout.close()
        process.wait()

if __name__ == "__main__":
    client_thread = threading.Thread(target=run_client)
    client_thread.start()
    client_thread.join()