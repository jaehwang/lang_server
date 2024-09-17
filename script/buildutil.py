import json
import re

from clang.cindex import CursorKind

def read_compile_commands(filename):
    if filename.endswith('.json'):
        with open(filename) as compdb:
            return json.load(compdb)
    else:
        return [{'command': '', 'file': filename}]

# read_compile_commands의 리턴 값을 받아서 file이 키인 hash로 변환
def compile_commands_by_file(filename):
    compile_commands = read_compile_commands(filename)
    return {cmd['file']: cmd for cmd in compile_commands}

def extract_args(command):
    # 공백으로 문자열 분리
    parts = command.split()
    
    # 정규 표현식 패턴 정의
    pattern = re.compile(r'^-I|-D|-isysroot|-isystem|-std=')
    
    # 패턴에 맞는 인자 추출
    extracted_args = []
    i = 0
    while i < len(parts):
        if pattern.match(parts[i]):
            extracted_args.append(parts[i])
            # -sysroot와 -system는 다음 인자도 포함해야 함
            if (parts[i] == '-isysroot' or parts[i] == '-isystem') and i + 1 < len(parts):
                extracted_args.append(parts[i + 1])
                i += 1
        i += 1
    
    return extracted_args

def find_functions_at_lines(cursor, file_path, line_numbers, result):
    """주어진 커서에서 해당 파일의 여러 라인 번호가 속한 함수명을 찾음"""
    if cursor.location.file and cursor.location.file.name == file_path:
        start_line = cursor.extent.start.line
        end_line = cursor.extent.end.line
        
        # 커서가 함수 선언인 경우, 해당 함수가 line_numbers 중 어느 라인에 속하는지 확인
        if cursor.kind == CursorKind.FUNCTION_DECL:
            # 함수 범위 내에 있는 라인 번호에 대해 함수 이름을 기록
            for line_no in line_numbers.copy():  # set은 반복 중 제거를 위해 copy 필요
                if start_line <= line_no <= end_line:
                    result[line_no] = cursor.spelling
                    line_numbers.remove(line_no)  # 처리된 라인은 제거
        elif cursor.kind == CursorKind.CXX_METHOD:
            for line_no in line_numbers.copy():
                if start_line <= line_no <= end_line:
                    result[line_no] = cursor.spelling
                    line_numbers.remove(line_no)

    # 모든 자식 커서 순회
    for child in cursor.get_children():
        if not line_numbers:  # 모든 라인이 처리되면 더 이상 순회할 필요 없음
            break
        find_functions_at_lines(child, file_path, line_numbers, result)

def find_functions_in_file(tu, file_path, line_numbers):

    # 결과를 저장할 딕셔너리 (라인 번호 -> 함수 이름)
    result = {}

    # Translation Unit에서 root cursor 가져옴
    root_cursor = tu.cursor

    # root cursor부터 시작하여 한 번만 순회
    find_functions_at_lines(root_cursor, file_path, line_numbers, result)

    # 결과 리스트 생성
    results = []
    for line_no in sorted(result.keys()):
        results.append((file_path, line_no, result[line_no]))
    for line_no in sorted(line_numbers):  # 함수가 없는 경우도 포함
        results.append((file_path, line_no, "No function found"))

    return results