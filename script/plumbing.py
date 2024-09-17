
import sys
from diffutil import GitDiffParser

def get_git_diff():
    diff_text = sys.stdin.read()

    parser = GitDiffParser()
    diffs = parser.parse(diff_text)
    return diffs

def find_functions(diffs):
    for diff in diffs:
        print(f"Old Path: {diff.old_path}")
        print(f"New Path: {diff.new_path}")
        for hunk in diff.hunks:
            print(f"Old Start: {hunk.old_start}")
            print(f"Old Lines: {hunk.old_lines}")
            print(f"New Start: {hunk.new_start}")
            print(f"New Lines: {hunk.new_lines}")
    return []

def generate_call_graph(functions):
    call_graph = {}
    for function in functions:
        call_graph[function] = []  # 실제로는 함수 호출 관계를 분석해야 함
    return call_graph

def generate_review_request(call_graph):
    review_request = "다음은 함수 호출 그래프입니다:\n"
    for function, calls in call_graph.items():
        review_request += f"{function} 호출: {', '.join(calls) if calls else '없음'}\n"
    return review_request

def main():
    diffs = get_git_diff()
    # TODO: C/C++ 파일과 나머지 파일의 처리를 분리해야 함.
    # 빌드 관련 파일, 문서, 리소스 파일, 소스 코드 등으로 분리 가능.
    functions = find_functions(diffs)
    call_graph = generate_call_graph(functions)
    review_request = generate_review_request(call_graph)
    print(review_request)

if __name__ == "__main__":
    main()