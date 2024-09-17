# 설계 고려 사항

## 빌드 환경 구성

빌드 환경은 다음과 같은 요구 사항을 만족해야 한다.

* 프로젝트 소스 트리는 Git 저장소를 통해 공유 된다.
* 빌드 시스템을 통해 `compile_commands.json` 파일을 생성한다.
* 빌드 서버 간에 `compile_commands.json` 파일을 공유할 수 있어야 한다.
    - 같은 프로젝트는 여러 빌드 서버에서 동일한 경로에 저장되어 있어야 한다. 
* 빌드 서버에서 빌드 뿐 아니라 파싱, 정적분석 등도 수행할 수 있어야 한다.
    - 용도 별로 서버를 분리하더라도 소스 트리, 빌드 결과물의 경로는 동일해야 한다.

## Workflow

```
 B  diff -Naur A B
 |  |   |
 |  |  [parse and find changed functions]
 |  |   |
 |  |   v
 |  |  containing functions --+
 |  |           |             |          
 |  |   [find callers]   [coverity, clang-tidy, ...]
 |  |           |             |          
 |  |           v             v          
 |  |     call graph        defects    
 |  |      |      |           |          
 |  |      |  [find specs]    |          
 |  |      |      |           |          
 |  |      |    specs         |          
 |  |      |      |           |          
 v  v      v      v           v          
 +------------+---------------+         
              |
              V
[Syntheize intputs to generate prompt]
              |
              V
            [LLM]
              |
              v
            review
```

### parse and find changed functions

수정된 Function을 찾아서 분석 대상으로 선정한다. Method도 찾아야 한다.

Class, Type 변경은 어떻게 처리할 것인가?

Reference를 찾아서 Call Graph를 만들 수 있다.

### find callers

수정된 함수를 호출하는 함수를 찾아서 분석 대상으로 선정한다.

Caller들을 찾아서 Call Graph를 만들어야 한다.

### find specs

Call Graph를 구성하는 함수들의 Spec을 찾는다.

함수들의 Effect를 분석해서 Spec을 만들어야 한다.

SDD, Doxygen, Comment, ... 등을 고려하자.

### Indirect dependency via external entity

수정된 함수와 reference 외의 방식으로 의존성을 갖는 함수를 찾아야 한다.

TODO: 함수가 어떤 Effect를 만드는지를 AI로 분석할 수 있을까야?

### coverity, clang-tidy, ...

## Tools

* Cross reference는 clangd를 쓰자.
* AST는 libclang을 쓰자.
* Remote clang indexer를 쓰자.

<!--
vim:nospell
-->
