#!/usr/bin/env python3

import argparse
import json
import subprocess
import threading
import time
import os

from openai import OpenAI

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
    return response
    

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
    
    return receive_notification_and_response(process)

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

def get_files(comile_commands_dir):
    compile_commands = os.path.join(comile_commands_dir, 'compile_commands.json')
    with open(compile_commands, 'r') as f:
        compile_commands = json.load(f)
    
    files = []
    for compile_command in compile_commands:
        files.append('file://'+compile_command['file'])
    
    return files

def get_symbol_at_line(process, uri, line):
    # Send a textDocument/documentSymbol request
    response = send_request(process, "textDocument/documentSymbol", {
        "textDocument": {"uri": uri}
    })

    # Process the documentSymbol response
    if "result" in response:
        symbols = response["result"]
        for symbol in symbols:
            if symbol["location"]["range"]["start"]["line"] <= line <= symbol["location"]["range"]["end"]["line"]:
                return symbol
    return None
        
def review_code(file_path):
    with open(file_path, 'r') as file:
        file_text = file.read()

    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "system", "content": "You are a helpful assistant that reviews code."},
                {"role": "user", "content": f"Please review the following code in Korean:\n\n{file_text}"}
            ]
    )

    # 응답 출력
    print("Code review response for file:", file_path)
    print(completion.choices[0].message.content)

def lsp_main(process, compile_commands_dir, sandbox_project_dir):
    # Initialize the server
    send_request(process, "initialize", {
        "processId": None,
        "rootUri": None,
        "capabilities": {
            "textDocument": {
                "references": {
                    "dynamicRegistration": True,
                    "container": True  # clangd 16 or later
                }
            }
         }
    })
    
    open_files(process, get_files(compile_commands_dir))

    # Wait for seconds
    time.sleep(1)

    main_uri = 'file://'+os.path.join(sandbox_project_dir, 'src', 'main.c')
    util_uri = 'file://'+os.path.join(sandbox_project_dir, 'src', 'util.c')

    # Send another request
    send_request(process, "textDocument/definition", {
        "textDocument": {"uri": main_uri},
        "position": {"line": 19-1, "character": 15-1} # zero-based line and character
    })

    send_request(process, "textDocument/references", {
        "textDocument": {"uri": util_uri},
        "position": {"line": 68, "character": 4},  # Adjusted for 0-based indexing
        "context": {"includeDeclaration": False}
    })

    # Get symbol at specific line
    symbol = get_symbol_at_line(process, main_uri, 18)
    if symbol:
        print("Symbol at line 18:", symbol)
    else:
        print("No symbol found at line 18.")

    # Shutdown the server
    send_request(process, "shutdown", {})    

def run_client():   
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile-commands-dir", 
                        type=str, 
                        help="Path to the compile_commands.json directory")

    parser.add_argument("--sandbox-project-dir", 
                        type=str, 
                        help="Path to the sandbox project directory")
    
    args = parser.parse_args()

    if args.compile_commands_dir is None or not os.path.isdir(args.compile_commands_dir):
        parser.print_help()
        return

    if args.sandbox_project_dir is None or not os.path.isdir(args.sandbox_project_dir):
        parser.print_help()
        return
    
    if not os.path.isabs(args.sandbox_project_dir):
        args.sandbox_project_dir = os.path.abspath(args.sandbox_project_dir)

    with open('err.txt', 'w') as err_file:   
        process = subprocess.Popen(
            ['clangd', '--log=verbose', '--background-index', '--clang-tidy',
                       '--completion-style=detailed',
                       '--compile-commands-dir='+args.compile_commands_dir],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=err_file
        )

        lsp_main(process, args.compile_commands_dir, args.sandbox_project_dir)

        review_code(os.path.join(args.sandbox_project_dir, 'src', 'main.c'))

        process.stdin.close()
        process.stdout.close()
        process.wait()

if __name__ == "__main__":
    client_thread = threading.Thread(target=run_client)
    client_thread.start()
    client_thread.join()
