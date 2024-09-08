# client.py
import json
import subprocess
import threading
import time
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

def do_main(process):
    main_c = "file:///Users/jaehwang/work/ai_coding/sanbox_copilot/main.c"
    util_c = "file:///Users/jaehwang/work/ai_coding/sanbox_copilot/util.c"
    
    open_files(process, [main_c, util_c])

    # Wait for seconds
    time.sleep(3)
    
    # Send another request
    send_request(process, "textDocument/definition", {
        "textDocument": {"uri": main_c},
        "position": {"line": 19-1, "character": 15-1} # zero-based line and character
    })

        
def run_client():
    with open('err.txt', 'w') as err_file:   
        process = subprocess.Popen(
            ['clangd', '--log=verbose', '--background-index', '--clang-tidy','--completion-style=detailed'],
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

        do_main(process)
                
        # Shutdown the server
        send_request(process, "shutdown", {})

        process.stdin.close()
        process.stdout.close()
        process.wait()

if __name__ == "__main__":
    client_thread = threading.Thread(target=run_client)
    client_thread.start()
    client_thread.join()