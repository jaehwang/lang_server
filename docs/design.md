# 코드 분석

* Cross reference는 clangd를 쓰자.
* AST는 libclang을 쓰자.


```
 B  diff A B
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

## parse and find changed functions

수정된 Function을 찾아서 분석 대상으로 선정한다. Method도 찾아야 한다.

Class, Type 변경은 어떻게 처리할 것인가?

Reference를 찾아서 Call Graph를 만들 수 있다.

## find callers

수정된 함수를 호출하는 함수를 찾아서 분석 대상으로 선정한다.

Caller들을 찾아서 Call Graph를 만들어야 한다.

## find specs

Call Graph를 구성하는 함수들의 Spec을 찾는다.

함수들의 Effect를 분석해서 Spec을 만들어야 한다.

SDD, Doxygen, Comment, ... 등을 고려하자.

## Indirect dependency via external entity

수정된 함수와 reference 외의 방식으로 의존성을 갖는 함수를 찾아야 한다.

## coverity, clang-tidy, ...

<!--
vim:nospell
-->
