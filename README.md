# Language Server & Generative AI

## 개요
이 프로젝트는 `clangd`를 사용하여 C/C++ 프로젝트의 언어 서버 기능을 제공하고, OpenAI의 ChatGPT API를 사용하여 코드 리뷰를 수행하는 Python 스크립트를 포함합니다.

## 사용 방법

### 의존성 설치
프로젝트를 실행하기 전에 필요한 의존성을 설치해야 합니다:
```sh
pip install openai
```

Python clang package 버전은 14를 안 쓰면 `index.parse()` 후에 diagnostics에 stddef.h가 없다는 error이 나올 수 있다.

### config.json 작성

`script/config.sample.json`을 수정해서 config.json을 만들자.
```json
{
    "libclang_dir": "/home/linuxbrew/.linuxbrew/Cellar/llvm/18.1.8/lib",
    "python_clang_package_dir": "/home/linuxbrew/.linuxbrew/opt/llvm/lib/python3.12/site-packages"
}
```

`pip`로 clang을 설치하지 않고 llvm에서 같이 설치된 package를 쓰고 싶다면 `python_clang_package_dir`을 지정하자.


### 실행 방법 예

clangd, compile\_commands.json 파일이 있는 디렉토리를 지정하여 코드 리뷰를 수행할 수 있습니다.

```sh
python example.py --compile-commands-dir=/path/to/compile-commands-dir
```

### HTTP 서버 실행

```sh
node server.js
```

http://localhost:3000/ 에 접속하여 코드 리뷰를 수행할 수 있습니다.


<!--
vim:nospell
-->
