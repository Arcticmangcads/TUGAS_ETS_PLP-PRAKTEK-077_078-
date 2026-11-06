from crud.lexer import tokenize

for t in tokenize("/* a * b */ select 1 <> 2"):
    print(t)