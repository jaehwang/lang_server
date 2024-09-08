# Language Server & Generative AI

## 개요
이 프로젝트는 `clangd`를 사용하여 C/C++ 프로젝트의 언어 서버 기능을 제공하고, OpenAI의 ChatGPT API를 사용하여 코드 리뷰를 수행하는 Python 스크립트를 포함합니다.

## 사용 방법

### 의존성 설치
프로젝트를 실행하기 전에 필요한 의존성을 설치해야 합니다:
```sh
pip install openai
```

### 실행 방법 예

```sh
python example.py --compile-commands-dir=/path/to/compile-commands-dir
```