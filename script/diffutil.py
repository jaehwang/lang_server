# diffutil.py

import re
import sys

# git diff -U0 ... | python diffutil.py

class DiffFile:
    def __init__(self, old_path, new_path):
        self.old_path = old_path
        self.new_path = new_path
        self.hunks = []

    def add_hunk(self, hunk):
        self.hunks.append(hunk)

class DiffHunk:
    def __init__(self, old_start, old_lines, new_start, new_lines, changes):
        self.old_start = old_start
        self.old_lines = old_lines
        self.new_start = new_start
        self.new_lines = new_lines
        self.changes = changes

class GitDiffParser:
    def parse(self, diff_text):
        files = []
        lines = diff_text.split('\n')
        i = 0
        while i < len(lines):
            if lines[i].startswith('diff --git'):
                file, i = self.parse_header(lines, i)
                files.append(file)
            elif lines[i].startswith('@@'):
                hunk, i = self.parse_hunk(lines, i)
                files[-1].add_hunk(hunk)
            else:
                i += 1
        return files

    def parse_header(self, lines, i):
        old_path = re.search(r'a/(.+?) ', lines[i]).group(1)
        new_path = re.search(r'b/(.+?)$', lines[i]).group(1)
        file = DiffFile(old_path, new_path)
        i += 1
        return file, i

    def parse_hunk(self, lines, i):
        header = lines[i]
        match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', header)
        old_start = int(match.group(1))
        old_lines = int(match.group(2)) if match.group(2) else 1
        new_start = int(match.group(3))
        new_lines = int(match.group(4)) if match.group(4) else 1
        i += 1
        changes = []
        while i < len(lines) and not lines[i].startswith('@@') and not lines[i].startswith('diff --git'):
            changes.append(lines[i])
            i += 1
        hunk = DiffHunk(old_start, old_lines, new_start, new_lines, changes)
        return hunk, i

    # def summary(self, diffs):
    #     files = {}

    #     for diff in diffs:
    #         #print(f"New Path: {diff.new_path}")
    #         curr_file = diff.new_path
    #         for hunk in diff.hunks:
    #             #print(f"New Start: {hunk.new_start}")
    #             #print(f"New Lines: {hunk.new_lines}")
    #             lineno = hunk.new_start
    #             for change in hunk.changes:
    #                 if change.startswith(("+", "-")):
    #                     #print(f"{lineno:5}: {change}")
    #                     if curr_file not in files:
    #                         files[curr_file] = set()
    #                     files[curr_file].add(lineno)
    #                 if not change.startswith("-"):
    #                     lineno += 1
    #     return files

def summary(diffs):
        files = {}

        for diff in diffs:
            #print(f"New Path: {diff.new_path}")
            curr_file = diff.new_path
            for hunk in diff.hunks:
                #print(f"New Start: {hunk.new_start}")
                #print(f"New Lines: {hunk.new_lines}")
                lineno = hunk.new_start
                for change in hunk.changes:
                    if change.startswith(("+", "-")):
                        #print(f"{lineno:5}: {change}")
                        if curr_file not in files:
                            files[curr_file] = set()
                        files[curr_file].add(lineno)
                    if not change.startswith("-"):
                        lineno += 1
        return files
    
# Sample test code
if __name__ == '__main__':
    diff_text = sys.stdin.read()

    parser = GitDiffParser()
    files = parser.parse(diff_text)

    for file in files:
        print(f"Old Path: {file.old_path}")
        print(f"New Path: {file.new_path}")
        for hunk in file.hunks:
            print(f"Old Start: {hunk.old_start}")
            print(f"Old Lines: {hunk.old_lines}")
            print(f"New Start: {hunk.new_start}")
            print(f"New Lines: {hunk.new_lines}")
            print("Changes:")
            for change in hunk.changes:
                print(change)
        print()           
    