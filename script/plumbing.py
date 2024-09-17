#!/usr/bin/env python3

import argparse
import io
import os
import sys

from clang.cindex import Index, Config
from openai import OpenAI

import diffutil
import buildutil

Config.set_library_path('/Applications/Xcode.app/Contents/Frameworks')

def get_git_diff():
    diff_text = sys.stdin.read()

    parser = diffutil.GitDiffParser()
    diffs = parser.parse(diff_text)

    # TODO: C/C++ 파일과 나머지 파일의 처리를 분리해야 함.
    # 빌드 관련 파일, 문서, 리소스 파일, 소스 코드 등으로 분리 가능.
    code_diffs = [diff for diff in diffs if diff.new_path.endswith((".c", ".cpp"))]

    return (code_diffs, diffutil.summary(code_diffs))

def find_functions(compile_commands, rootdir, code_diffs):
    functions = {}
    index = Index.create()
    for file in code_diffs.keys():
        file_path = os.path.join(rootdir, file)

        cmd = compile_commands[file_path]
        c = buildutil.extract_args(cmd['command'])

        tu = index.parse(cmd['file'], c)
        function_list = buildutil.find_functions_in_file(tu, file_path, code_diffs[file])
        functions[file] = function_list

    return functions

def generate_call_graph(functions):
    call_graph = {}
    for file in functions:
        for file_path, line_no, function_name in functions[file]:
            print(f"Changed Function: {function_name}, File: {file}, Line: {line_no}")
   
    return call_graph

def ai_code_review(rootdir, code_diffs, functions, call_graph):
        
    client = OpenAI()

    for diff in code_diffs:

        stream = io.StringIO()

        file_path = os.path.join(rootdir, diff.new_path)

        stream.write(f"# {diff.new_path} 변경 사항 리뷰 요청\n")

        stream.write("## 다음은 수정된 파일입니다:\n")

        with open(file_path, 'r') as file:
            code = file.read()
            stream.write(f"```c\n{code}\n```\n")

        stream.write(f"## 다음은 Unified Diff입니다:\n")
        stream.write(f"```diff\n{diff.diff_text}\n```\n")

        stream.write(f"## 다음은 수정된 함수 목록입니다:\n")
        for file in functions:
            for file_path, line_no, function_name in functions[diff.new_path]:
                stream.write(f" * {function_name}, File: {file}, Line: {line_no}\n")

        stream.write(f"## 다음은 함수 호출 그래프입니다:\n")
        for function, calls in call_graph.items():
            stream.write(f"{function} 호출: {', '.join(calls) if calls else '없음'}\n")

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                    {"role": "system", "content": "당신은 30년 경력의 프로그래머입니다."},
                    {"role": "user", "content": f"{stream.getvalue()}"}
                ]
            )

        # 응답 출력
        print("Code review response for file:", diff.new_path)
        print(completion.choices[0].message.content)

        stream.close()

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--compile_commands",
        help="Path to compile_commands.json",
        required=True
    )
    parser.add_argument(
        "--rootdir",
        help="Absolute Path to project root directory",
        required=True
    )

    args = parser.parse_args()
 
    if not os.path.isabs(args.rootdir):
        parser.print_help()
        sys.exit(1)

    return args

def main():
    args = parse_arguments()
    
    compile_commands = buildutil.compile_commands_by_file(args.compile_commands)

    code_diffs, code_files = get_git_diff()
    
    functions = find_functions(compile_commands,args.rootdir,code_files)
    call_graph = generate_call_graph(functions)
    ai_code_review(args.rootdir, code_diffs, functions, call_graph)

if __name__ == "__main__":
    main()