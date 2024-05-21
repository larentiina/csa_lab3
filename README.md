# Лабораторная работа №3. Отчёт

Кузенина Валерия Николаевна, P3232

`alg | acc | harv | hw | tick | struct | stream | port | pstr | prob1 |`

Базовый вариант (без усложнения)
## Синтаксис
``` ebnf
<program> ::= { <statement> }

<statement> ::= "if" <cond-expr> <statement> |
                "if" <cond-expr> <statement> "else" <statement> |
                "while" <cond-expr> <statement> |
                "{" { <statement> } "}" |
                <expr> ";" |
                <input-expr> ";" |
                <output-expr> ";" |
                <declaration> |
                <variable_assignment> |
                ";"

<declaration> ::= type <id> "=" <expr>

<variable_assignment> ::= <id> "=" <expr>

<cond-expr> ::= "(" <expr> ( "==" | "<" | ">" ) <expr> ")"

<type> ::= "int" | "string"

<input-expr> ::= "input" "(" <id> ")" |  "input_char" "(" <id> ")"

<output-expr> ::= "print" ( <id> | <string> ) | "print_char" ( <id> | <letter> )

<expr> ::= <id> |
           <digit> |
           <string> |
           <expr> "%" <expr> |
           <expr> "+" <expr> |
           <expr> "-" <expr>

<id> ::= <letter>

<string> ::= <letter> | <string> <letter>


<letter> ::= [a-zA-Z]

<digit> ::= "0" | "1" | ... | "9"
```
### Особенности
- У переменных глобальная область видимости
- Статическая строгая типизация
- Поддерживаемые типы: `string`, `int`
  - `int` - числовой тип, используется всегда по значению. Может принимать значение любого числа, помещающегося в 1 слово.
  - `string` - строковый тип. Память под строки выделяется статически. Строки immutable. При присваивании переменной типа string новой строки в памяти меняется указатель на данную переменную.
- Поддерживаются математические операции: `+`, `-`,`%`
- Все операторы левоасоциативные, кроме операторов сравнения: `<`, `>`,`==` - они имеют высший приоритет
- Сигнатуры всех методов: `(int,int) -> int`. Исключение условия в циклах, в них возможно сравнение строки длинной 1 с int
- Поддерживаются функции: `print(string| var) , print_char(var), input(var), input_char(var)':
  - print_char(var) и  input_char(var) - выводят и считывают только один символ
  - print(string| var) и input(var) - выводят и считывают всю строку целиком


## Организация памяти
### Память инструкций
Память для хранения инструкций выполнения программы. Реализуется списком объектов класса Opcode. 

Инструкция состоит из названия команды, аргумента (опционально), вида адресации (опционально).

Виды адресации представлены в классе AddressMode.

Размер машинного слова для инструкций не определен.

Классы `Opcode` и `AddressMode` представлены в файле [isa.py](./isa.py)
### Память данных
- Размер машинного слова 16 бит. В памяти данных хранятся статические данные - числа и строки. Число занимает одну ячейку памяти. Строки распределяются по одному символу в одну ячейку памяти, в начале строки - её длина.

Вывод данных из памяти осуществляется в data register по адресу в data address. Ввод данных в память осуществляется и аккумулятора по сигналу oe по адресу в data address
### Модель данных
Обращение к переменной всегда осуществляется через прямую адресацию. 

Временные константы не сохраняются в статическую память и обращение к ним проиходит через непосредственную адресацию

## Система команд
### Набор инструкций

| Opcode | ARG   | Кол-во тактов | Описание                                                    |
|:-----|:----    |:--------------|:------------------------------------------------------------|
| ST   | +   | 2                 | сохранить значение в указанной ячейке из acc                  |
| LD   | +   | 1                 | загрузить значение в acc                   |
| CMP  | +   | 2                | установить флаги z и n по операции acc - arg                           |
| HLT  | -   | 0               | остановка                                |
| ADD  | +   | 2               | сложить значение из аккумулятора со значением, переданным в аргументе          |
| SUB  | +   | 2               | вычесть из аккумулятора значение, переданное в аргументе |
| DIV  | +`  | 2               | посчитать модуль числа от деления аккумулятора на значение, переданное в аргументе                                     |
| OUT  | -   | 1               | вывести значение из аккумулятора на устройство вывода                          |
|  IN  | -   | 1               | ввести значение в аккумулятор с устройства ввода                                                  |
|  JNZ | +   | 1               | переход если флаг z не установлен                                                  |
|  JZ  | +   | 1               | переход если флаг z установлен                                                  |
|  JN  | +   | 1               | переход если флаг n установлен                                                  |
|  JLE | +   | 1               | переход если флаг z установлен или n установлен (переход если меньше либо равно)                                                 |
|  JGE | +   | 1               | переход если флаг z установлен или n не установлен (переход если больше либо равно)                                                 |
|  JMP | +   | 1               | безусловный переход                                         |

Реализовано 3 вида адресации операнда:
- IMMEDIATE -  аргумент содержит данные. 
- DIRECT - операнд указывает на ячейку памяти, содержащую данные. 
- INDIRECT - операнд содержит адрес памяти, по которому находится фактический адрес данных.

## Транслятор
Реализован в [translator](./translator.py)
Интерфейс командной строки: `.\translator.py <input_file> <target_file>`
Этапы трансляции:
- Код разбивается на токены в классе `Lexer`. У токена есть - текст и тип токена. Типы токенов представлены в классе `TokensName`. В классе `Lexer` метод `lex()` - выполняется лексический анализ входной строки, тип токена определяется согласно совпадению с регулярным выражением из списка `token_exprs`. Если не удается найти соответствие для символа, выводится сообщение об ошибке.
- В классе `Parser `строится AST дерево в соответствии с BNF. У каждого узла дерева - объект класса Node есть ссылки на 3 дочерних узла и в зависимости от типа родительского узла используется нужное их количество. Парсер реализован по LL принципу - анализирует токены слева направо. Метод `statement()` - рекурсивный метод анализирующий типы токенов и исходя из этого создаёт узлы. Метод `cond_expression()` - генерирует узлы для условный выражений. Метод `kind_of_node()` - создаёт узел для токенов, которые являются константами или названием переменных.
- В классе `Compiler` генерируется машинный код согласно AST дереву последовательно компилируя его узлы. В этом классе происходит заполнение статической памяти, находящейся в классе `MemoryManager`. Метод `compile()` - основной рекурсивный метод, в котором проиходит анализ типов узлов и генерация на этом основании послеовательности машинных инструкций.
- После этапа трансляции в `<target_file>`записывается последовательность машинных инструкций, которая пойдет в память инструкций в процессор, а в файл `data_section.txt` записывается заполненная статическая память, которая пойдет в память данных в процессоре.

### Пример
Пример AST дерева для программы:
```
{
  int a = 2;
  int b = a + 2 - 3 + 10;
  int c = a + b;
}
PROG: None
  SEQ: None
    SEQ: None
      SEQ: None
        EMPTY: None
        OPERATOR: =
          VAR_INT: a
          INT_CONST: 2
      OPERATOR: =
        VAR_INT: b
        OPERATOR: +
          VAR: a
          OPERATOR: -
            INT_CONST: 2
            OPERATOR: +
              INT_CONST: 3
              INT_CONST: 10
    OPERATOR: =
      VAR_INT: c
      OPERATOR: +
        VAR: a
        VAR: b


```
## Модель процессора
Реализован в [machine](./machine.py)
Интерфейс командной строки: `.\machine <input_code_file> <input_buffer>`
### Схема
![data_path.svg](./model/data_path.svg) ![cu.svg](./model/cu.svg)

Control Unit:
- Моделирование на уровне тактов
- Instruction Decoder - декодировщик инструкций, отправляет в память данные в регистры `DA`/`DR` и необходимые сигналы в `Data Path`

Сигналы (обрабатываются за 1 такт, реализованы в виде методов класса):
- latch_acc - защелкнуть выбранное значение в `ACC`
- latch_data_reg - защелкнуть выбранное значение в `DR`
- latch_data_address - защелкнуть выбранное значение в `DA`
- signal_wr_to_memory - записать значение в память по адресу из `DA`
- signal_oe_memory - сигнал памяти достать из неё значение по адресу из `DA`
- signal_latch_program_counter- защелкнуть выбранное значение в `PC`

Флаги:
- `Z` (Zero) - отражает наличие нулевого значения в ACC
- `N` (Negative) - отражает наличие отрицательного значения в ACC

Особенности работы модели:
- Команды, которые имеют аргумент проходят цикл выборки операнда - `operand_fetch` в связи с несколькими видами адресации
- Остановка симуляции осуществляется при помощи исключений:
  - StopIteration - при достижении HLT инструкции
  - AssertionError - при возникновении рантайм-ошибок (деление на 0, слишком большая программа, нерпавильные значения регистров и т.д.)
  - EOFException - при ошибке Buffer is empty

## Тестирование
В качестве тестов использовано 4 алгоритма согласно заданию:
- [hello_world](./golden/hello_world.yml)
- [hello_user](./golden/hello_user.yml)
- [cat](./golden/cat.yml)
- [prob1](./golden/prob1.yml)
### Пример работы программы
```
 {
      string c = "a";
      input_char(c);
      while(c>0){
          print_char(c);
          input_char(c);
      }
  }
```
AST:
```
  PROG: None
    SEQ: None
      SEQ: None
        SEQ: None
          EMPTY: None
          OPERATOR: =
            VAR_STRING: c
            STRING_CONST: a
        FUNC: input_char
          VAR: c
      KEY_WORDS: while
        OPERATOR: >
          VAR: c
          INT_CONST: 0
        SEQ: None
          SEQ: None
            EMPTY: None
            FUNC: print_char
              VAR: c
          FUNC: input_char
            VAR: c
```
Входной буффер
```
lera\x00
```
  
После трансляции получаем машинный код:
```
[
      {
          "opcode": "IN"
      },
      {
          "opcode": "ST",
          "arg": 1,
          "addr_mode": "IMMEDIATE"
      },
      {
          "opcode": "JLE",
          "arg": 8,
          "addr_mode": "IMMEDIATE"
      },
      {
          "opcode": "LD",
          "arg": 1,
          "addr_mode": "DIRECT"
      },
      {
          "opcode": "OUT"
      },
      {
          "opcode": "IN"
      },
      {
          "opcode": "ST",
          "arg": 1,
          "addr_mode": "IMMEDIATE"
      },
      {
          "opcode": "JMP",
          "arg": 2,
          "addr_mode": "IMMEDIATE"
      },
      {
          "opcode": "HLT"
      }
  ]
```
Журнал работы процессора:
```
 INFO     root:machine.py:166 instruction: {'opcode': <Opcode.IN: 'IN'>}
  DEBUG    root:machine.py:84 input: 108
  DEBUG    root:machine.py:127 {TICK: 1, PC: 1, ADDR: 0, ACC: 108, DR: 0, DA 0}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.ST: 'ST'>, 'arg': 1, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 2, PC: 1, ADDR: 0, ACC: 108, DR: 1, DA 0}
  DEBUG    root:machine.py:127 {TICK: 3, PC: 2, ADDR: 1, ACC: 108, DR: 1, DA 1}
  DEBUG    root:machine.py:127 {TICK: 4, PC: 2, ADDR: 1, ACC: 108, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.JLE: 'JLE'>, 'arg': 8, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 5, PC: 3, ADDR: 1, ACC: 108, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.LD: 'LD'>, 'arg': 1, 'addr_mode': <AddressMode.DIRECT: 'DIRECT'>}
  DEBUG    root:machine.py:127 {TICK: 6, PC: 3, ADDR: 1, ACC: 108, DR: 1, DA 1}
  DEBUG    root:machine.py:127 {TICK: 7, PC: 3, ADDR: 1, ACC: 108, DR: 108, DA 1}
  DEBUG    root:machine.py:127 {TICK: 8, PC: 4, ADDR: 1, ACC: 108, DR: 108, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.OUT: 'OUT'>}
  DEBUG    root:machine.py:114 output: '' << 'l'
  DEBUG    root:machine.py:127 {TICK: 9, PC: 5, ADDR: 1, ACC: 108, DR: 108, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.IN: 'IN'>}
  DEBUG    root:machine.py:84 input: 101
  DEBUG    root:machine.py:127 {TICK: 10, PC: 6, ADDR: 1, ACC: 101, DR: 108, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.ST: 'ST'>, 'arg': 1, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 11, PC: 6, ADDR: 1, ACC: 101, DR: 1, DA 1}
  DEBUG    root:machine.py:127 {TICK: 12, PC: 7, ADDR: 1, ACC: 101, DR: 1, DA 1}
  DEBUG    root:machine.py:127 {TICK: 13, PC: 7, ADDR: 1, ACC: 101, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.JMP: 'JMP'>, 'arg': 2, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 14, PC: 2, ADDR: 1, ACC: 101, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.JLE: 'JLE'>, 'arg': 8, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 15, PC: 3, ADDR: 1, ACC: 101, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.LD: 'LD'>, 'arg': 1, 'addr_mode': <AddressMode.DIRECT: 'DIRECT'>}
  DEBUG    root:machine.py:127 {TICK: 16, PC: 3, ADDR: 1, ACC: 101, DR: 1, DA 1}
  DEBUG    root:machine.py:127 {TICK: 17, PC: 3, ADDR: 1, ACC: 101, DR: 101, DA 1}
  DEBUG    root:machine.py:127 {TICK: 18, PC: 4, ADDR: 1, ACC: 101, DR: 101, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.OUT: 'OUT'>}
  DEBUG    root:machine.py:114 output: 'l' << 'e'
  DEBUG    root:machine.py:127 {TICK: 19, PC: 5, ADDR: 1, ACC: 101, DR: 101, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.IN: 'IN'>}
  DEBUG    root:machine.py:84 input: 114
  DEBUG    root:machine.py:127 {TICK: 20, PC: 6, ADDR: 1, ACC: 114, DR: 101, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.ST: 'ST'>, 'arg': 1, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 21, PC: 6, ADDR: 1, ACC: 114, DR: 1, DA 1}
  DEBUG    root:machine.py:127 {TICK: 22, PC: 7, ADDR: 1, ACC: 114, DR: 1, DA 1}
  DEBUG    root:machine.py:127 {TICK: 23, PC: 7, ADDR: 1, ACC: 114, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.JMP: 'JMP'>, 'arg': 2, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 24, PC: 2, ADDR: 1, ACC: 114, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.JLE: 'JLE'>, 'arg': 8, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 25, PC: 3, ADDR: 1, ACC: 114, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.LD: 'LD'>, 'arg': 1, 'addr_mode': <AddressMode.DIRECT: 'DIRECT'>}
  DEBUG    root:machine.py:127 {TICK: 26, PC: 3, ADDR: 1, ACC: 114, DR: 1, DA 1}
  DEBUG    root:machine.py:127 {TICK: 27, PC: 3, ADDR: 1, ACC: 114, DR: 114, DA 1}
  DEBUG    root:machine.py:127 {TICK: 28, PC: 4, ADDR: 1, ACC: 114, DR: 114, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.OUT: 'OUT'>}
  DEBUG    root:machine.py:114 output: 'le' << 'r'
  DEBUG    root:machine.py:127 {TICK: 29, PC: 5, ADDR: 1, ACC: 114, DR: 114, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.IN: 'IN'>}
  DEBUG    root:machine.py:84 input: 97
  DEBUG    root:machine.py:127 {TICK: 30, PC: 6, ADDR: 1, ACC: 97, DR: 114, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.ST: 'ST'>, 'arg': 1, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 31, PC: 6, ADDR: 1, ACC: 97, DR: 1, DA 1}
  DEBUG    root:machine.py:127 {TICK: 32, PC: 7, ADDR: 1, ACC: 97, DR: 1, DA 1}
  DEBUG    root:machine.py:127 {TICK: 33, PC: 7, ADDR: 1, ACC: 97, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.JMP: 'JMP'>, 'arg': 2, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 34, PC: 2, ADDR: 1, ACC: 97, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.JLE: 'JLE'>, 'arg': 8, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 35, PC: 3, ADDR: 1, ACC: 97, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.LD: 'LD'>, 'arg': 1, 'addr_mode': <AddressMode.DIRECT: 'DIRECT'>}
  DEBUG    root:machine.py:127 {TICK: 36, PC: 3, ADDR: 1, ACC: 97, DR: 1, DA 1}
  DEBUG    root:machine.py:127 {TICK: 37, PC: 3, ADDR: 1, ACC: 97, DR: 97, DA 1}
  DEBUG    root:machine.py:127 {TICK: 38, PC: 4, ADDR: 1, ACC: 97, DR: 97, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.OUT: 'OUT'>}
  DEBUG    root:machine.py:114 output: 'ler' << 'a'
  DEBUG    root:machine.py:127 {TICK: 39, PC: 5, ADDR: 1, ACC: 97, DR: 97, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.IN: 'IN'>}
  DEBUG    root:machine.py:84 input: 0
  DEBUG    root:machine.py:127 {TICK: 40, PC: 6, ADDR: 1, ACC: 0, DR: 97, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.ST: 'ST'>, 'arg': 1, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 41, PC: 6, ADDR: 1, ACC: 0, DR: 1, DA 1}
  DEBUG    root:machine.py:127 {TICK: 42, PC: 7, ADDR: 1, ACC: 0, DR: 1, DA 1}
  DEBUG    root:machine.py:127 {TICK: 43, PC: 7, ADDR: 1, ACC: 0, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.JMP: 'JMP'>, 'arg': 2, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 44, PC: 2, ADDR: 1, ACC: 0, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.JLE: 'JLE'>, 'arg': 8, 'addr_mode': <AddressMode.IMMEDIATE: 'IMMEDIATE'>}
  DEBUG    root:machine.py:127 {TICK: 45, PC: 8, ADDR: 1, ACC: 0, DR: 1, DA 1}
  INFO     root:machine.py:166 instruction: {'opcode': <Opcode.HLT: 'HLT'>}
```
Выходной буффер
```
lera
```
Статистика
```
instr_counter:  27 ticks: 45
```
## Настройки CI
В файле [python.yml](./.github/workflows/python.yml)
```
name: Python CI

on:
  push:
    branches:
      - master
  pull_request:
    branches:
      - master

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.10.7

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Run tests and collect coverage
        run: |
          poetry run coverage run -m pytest .
          poetry run coverage report -m
        env:
          CI: true

  lint:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Check code formatting with Ruff
        run: poetry run ruff format --check .

      - name: Run Ruff linters
        run: poetry run ruff check .

```

### Общая статистика
```text
| ФИО                            | алг         | LoC | code байт | code инстр. | инстр. | такт. | вариант |
| Кузенина Валерия Николаевна    | hello_world | 7   | -         | 13          | 129    | 339   | alg | acc | harv | hw | tick | struct | stream | port | pstr | prob1 |     |
| Кузенина Валерия Николаевна    | hello_user  | 1   | -         | 47          | 349    | 911   | alg | acc | harv | hw | tick | struct | stream | port | pstr | prob1 |     |
| Кузенина Валерия Николаевна    | cat         | 8   | -         | 9           | 27     | 45    | alg | acc | harv | hw | tick | struct | stream | port | pstr | prob1 |     |
| Кузенина Валерия Николаевна    | prob1       | 14  | -         | 25          | >1000  | >1000 | alg | acc | harv | hw | tick | struct | stream | port | pstr | prob1 |     |
```
