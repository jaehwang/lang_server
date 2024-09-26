#!/usr/bin/env python3

import argparse
import io
import os
import sys
import json

from git import Repo
from openai import OpenAI

import diffutil
import buildutil as bu

# --- Begin of configuration ---
config_path = os.path.join(os.path.dirname(__file__), 'config.json')

with open(config_path, 'r') as config_file:
    config = json.load(config_file)

python_clang_package_dir = config.get('python_clang_package_dir')

if python_clang_package_dir is not None:
    sys.path.append(python_clang_package_dir)

from clang.cindex import Index, Config

libclang_dir = config.get('libclang_dir')

if libclang_dir is not None:
    Config.set_library_path(libclang_dir)
# --- End of configuration ---

def git_diff(repo, commit1, commit2):
    """
    Generate a diff between two commits in a git repository.

    Args:
        repo (git.Repo): The git repository object.
        commit1 (str): The SHA or reference of the first commit.
        commit2 (str): The SHA or reference of the second commit.

    Returns:
        str: A string representing the diff between the two commits in
             unified diff format.
    """
    commit = repo.commit(commit1)
    diffs = commit.diff(commit2, create_patch=True)

    txt = io.StringIO()

    for diff in diffs:
        txt.write('diff --git a/'+diff.a_path+' b/'+diff.b_path+"\n")
        txt.write('--- a/'+diff.a_path+"\n")
        txt.write('+++ b/'+diff.b_path+"\n")
        txt.write(diff.diff.decode('utf-8'))

    str = txt.getvalue()
    txt.close()
    return str

def get_git_diff(repo, commit1, commit2):
    diff_text = git_diff(repo, commit1, commit2)

    parser = diffutil.GitDiffParser()
    diffs = parser.parse(diff_text)

    # TODO: C/C++ 파일과 나머지 파일의 처리를 분리해야 함.
    # 빌드 관련 파일, 문서, 리소스 파일, 소스 코드 등으로 분리 가능.
    code_diffs = [
        diff for diff in diffs 
        if diff.new_path.endswith((".c", ".cpp"))
    ]

    return (code_diffs, diffutil.changed_line_numbers(code_diffs))

def find_functions(compile_commands, rootdir, changd_lines):
    functions = {}
    index = Index.create()
    for file in changd_lines.keys():
        file_path = os.path.join(rootdir, file)

        cmd = compile_commands[file_path]
        c = bu.extract_args(cmd['command'])

        tu = index.parse(cmd['file'], c)
        function_list = bu.find_functions_in_file(
            tu, file_path, changd_lines[file]
        )
        functions[file] = function_list

    return functions

def find_dependents(functions):
    """
    System resource 등을 통한 간접적인 의존성을 갖는 함수를 찾자.
    """
    dependents = {}
    for file in functions:
        for file_path, line_no, function_name in functions[file]:
            print(f"Changed Function: %s, File: %s, Line: %s" % 
                  (function_name, file, line_no))
                  
   
    return dependents

def generate_prompt(repo, commit, diff, functions, dependents):
    prompt = io.StringIO()

    prompt.write(f"# {diff.new_path} 코드 리뷰 요청\n")

    prompt.write("## 수정된 파일 내용입니다:\n")

    prompt.write(repo.git.show(commit+":"+diff.new_path)+"\n")

    prompt.write(f"## 변경 내용에 대한 Unified Diff입니다:\n")
    prompt.write(f"```diff\n{diff.diff_text}\n```\n")

    prompt.write(f"## 수정된 함수 목록입니다:\n")
    for file in functions:
        for file_path, line_no, function_name in functions[diff.new_path]:
            prompt.write(f" * %s, File: %s, Line: %s\n" % 
                          (function_name, file, line_no))

    prompt.write(f"## Indirect Dependents:\n")
    for function, calls in dependents.items():
        prompt.write(f"%s 호출: %s\n" % 
                     (function, ', '.join(calls) if calls else '없음'))

    str = prompt.getvalue()
    prompt.close()
    return str

def ai_code_review(repo, commit, code_diffs, functions, dependents):
        
    client = OpenAI()

    for diff in code_diffs:
        prompt = generate_prompt(repo, commit, diff, functions, dependents)
        print("Prompt:\n")
        print(prompt)
        
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                    {"role": "system", 
                     "content": "당신은 30년 경력의 Software 프로그래머입니다."},
                    {"role": "user", "content": f"{prompt}"}
                ]
            )

        # 응답 출력
        print("Code review response for file:", diff.new_path)
        print(completion.choices[0].message.content)

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--compile-commands",
        help="Path to compile_commands.json",
        required=True
    )
    parser.add_argument(
        "--rootdir",
        help="Absolute Path to project root directory",
        required=True
    )

    parser.add_argument(
        "--commit1",
        help="Commit ID 1",
        required=True
    )

    parser.add_argument(
        "--commit2",
        help="Commit ID 2",
        required=True
    )

    args = parser.parse_args()
 
    if not os.path.exists(args.rootdir):
        print(f"Error: {args.rootdir} not found.", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    if not os.path.isabs(args.rootdir):
        args.rootdir = os.path.abspath(args.rootdir)

    if not os.path.isfile(args.compile_commands):
        print(f"Error: {args.compile_commands} not found.", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    return args

def main():
    args = parse_arguments()
    
    compile_commands = bu.compile_commands_by_file(args.compile_commands)

    repo = Repo(args.rootdir)

    code_diffs, changed_lines = get_git_diff(repo, args.commit1, args.commit2)

    functions = find_functions(compile_commands, args.rootdir, changed_lines)
    dependents = find_dependents(functions)
    ai_code_review(repo, args.commit2, code_diffs, functions, dependents)

if __name__ == "__main__":
    main()
