from __future__ import annotations

import enum
import re
import sys
from enum import Enum, auto
from typing import ClassVar

from isa import AddressMode, Opcode, write_code


class TokensName(Enum):
    KEY_WORDS = auto()
    INT = enum.auto()
    STRING = enum.auto()
    OPERATOR = enum.auto()
    SEPARATOR = enum.auto()
    ID = enum.auto()
    LBRA = enum.auto()
    RBRA = enum.auto()
    FUNC = enum.auto()
    TYPE = enum.auto()

    def __str__(self):
        return f"{self.value}"


class Lexer:
    token_exprs: ClassVar[list] = [
        (r"[ \n\t]+", None),
        (r"#[^\n]*", None),
        (r"if", TokensName.KEY_WORDS),
        (r"else", TokensName.KEY_WORDS),
        (r"while", TokensName.KEY_WORDS),
        (r"int", TokensName.TYPE),
        (r"string", TokensName.TYPE),
        (r"[0-9]+", TokensName.INT),
        (r"input_char", TokensName.FUNC),
        (r"print_char", TokensName.FUNC),
        (r"\"[A-Za-z0-9_?!\s,]*\"", TokensName.STRING),
        (r"input", TokensName.FUNC),
        (r"print", TokensName.FUNC),
        (r"\+", TokensName.OPERATOR),
        (r"\-", TokensName.OPERATOR),
        (r"\%", TokensName.OPERATOR),
        (r"==", TokensName.OPERATOR),
        (r"<", TokensName.OPERATOR),
        (r">", TokensName.OPERATOR),
        (r"\=", TokensName.OPERATOR),
        (r"\(", TokensName.SEPARATOR),
        (r"\)", TokensName.SEPARATOR),
        (r"\{", TokensName.LBRA),
        (r"\}", TokensName.RBRA),
        (r";", TokensName.SEPARATOR),
        (r"[A-Za-z][A-Za-z0-9_]*", TokensName.ID),
    ]

    def lex(self, characters):
        pos = 0
        tokens = []
        while pos < len(characters):
            match = None
            for token_expr in self.token_exprs:
                pattern, tag = token_expr
                regex = re.compile(pattern)
                match = regex.match(characters, pos)
                if match:
                    text = match.group(0)
                    if tag:
                        token = (text, tag)
                        tokens.append(token)
                    break
            if not match:
                sys.stderr.write("Illegal character: {}\n".format(characters[pos]))
                sys.exit(1)
            else:
                pos = match.end(0)
        return tokens


class Node:
    def __init__(self, kind, value=None, op1=None, op2=None, op3=None):
        self.type = kind
        self.value = value
        self.op1 = op1
        self.op2 = op2
        self.op3 = op3

    def __str__(self):
        return f'Node(type={self.type}, value="{self.value}")'


class Parser:
    VAR_INT = "VAR_INT"
    VAR_STRING = "VAR_STRING"
    VAR = "VAR"
    SET = "SET"
    PROG = "PROG"
    EMPTY = "EMPTY"
    ADD = "ADD"
    OPERATOR = "OPERATOR"
    KEY_WORDS = "KEY_WORDS"
    SEQ = "SEQ"
    INT_CONST = "INT_CONST"
    STRING_CONST = "STRING_CONST"
    FUNC = "FUNC"

    def __init__(self, lexer, tokens):
        self.lexer = lexer
        self.tokens = tokens
        self.i = 0

    def next_token(self):
        self.i = self.i + 1

    def get_token_type(self):
        return self.tokens[self.i][1]

    def get_token_text(self):
        return self.tokens[self.i][0]

    def get_token(self):
        return self.tokens[self.i]

    def expression(self, node):
        self.next_token()
        text_token = self.get_token_text()
        if node.type == Parser.FUNC:
            node = self.kind_of_node(self.get_token())
        elif self.get_token_type() == TokensName.OPERATOR:
            self.next_token()
            node = Node(Parser.OPERATOR, value=text_token, op1=node, op2=self.statement())
        return node

    def cond_expression(self):
        n = Node(Parser.EMPTY)
        self.next_token()
        if self.get_token_type() == TokensName.SEPARATOR:
            self.next_token()
            node = self.statement()
            n = self.change_node(node)
        elif self.get_token_type() == TokensName.LBRA:
            n = self.statement()
        return n

    def change_node(self, node):
        new_node = node
        if node.value != "==" and node.value != "<" and node.value != ">":
            temp = node.op2
            print(temp.value)
            while temp.value != "==" and temp.value != "<" and temp.value != ">":
                temp = temp.op2
            new_node = temp
            temp = temp.op1
            node.op2 = temp
            new_node.op1 = node
        return new_node

    def kind_of_node(self, token):
        kind = token[1]
        node = None
        if kind == TokensName.ID:
            if self.tokens[self.i - 1][0] == "int":
                node = Node(Parser.VAR_INT, self.get_token_text())
            elif self.tokens[self.i - 1][0] == "string":
                node = Node(Parser.VAR_STRING, self.get_token_text())
            else:
                node =  Node(Parser.VAR, self.get_token_text())
        elif kind == TokensName.INT:
            node = Node(Parser.INT_CONST, self.get_token_text())
        else:
            node = Node(Parser.STRING_CONST, self.get_token_text().replace('"', ""))
        return node

    def statement(self):
        n = None
        if (
            self.get_token_type() == TokensName.ID
            or self.get_token_type() == TokensName.INT
            or self.get_token_type() == TokensName.STRING
        ):
            node = self.kind_of_node(self.get_token())
            n = self.expression(node)
        elif self.get_token_type() == TokensName.KEY_WORDS:
            if self.get_token_text() != "else":
                n = Node(Parser.KEY_WORDS, self.get_token_text(), op1=self.cond_expression())
                n.op2 = self.cond_expression()
                self.next_token()
            if self.get_token_text() == "else":
                self.next_token()
                n.op3 = self.statement()
            else:
                self.i = self.i - 1
        elif self.get_token_type() == TokensName.FUNC:
            n = Node(Parser.FUNC, self.get_token_text())
            self.next_token()
            n.op1 = self.expression(n)
            self.next_token()
            self.next_token()
        elif self.get_token_type() == TokensName.LBRA:
            n = Node(Parser.EMPTY)
            self.next_token()
            while self.get_token_type() != TokensName.RBRA:
                n = Node(Parser.SEQ, op1=n, op2=self.statement())
                self.next_token()
        elif self.get_token_type() == TokensName.TYPE:
            self.next_token()
            n = self.statement()
        return n

    def print_tree(self, node, level=0):
        if node is None:
            return
        print("  " * level + str(node))
        self.print_tree(node.op1, level + 1)
        self.print_tree(node.op2, level + 1)
        self.print_tree(node.op3, level + 1)

    def parse(self):
        node = Node(Parser.PROG)
        node.op1 = self.statement()
        self.print_tree(node)
        return node


class MemoryManager:
    def __init__(self):
        self.memory_counter = 0
        self.variables_address: dict[str, int] = {}
        self.variables_types: dict[str, int] = {}
        self.memory = []


class Compiler:
    def __init__(self, memory_manager, nodes):
        self.program = list()
        self.memory_manager = memory_manager
        self.nodes = nodes
        self.pc = 0

    def gen(self, command):
        self.program.append(command)
        self.pc = self.pc + 1

    def pre_compile(self, node):
        if node.type == Parser.VAR:
            self.gen(
                {
                    "opcode": Opcode.LD,
                    "arg": self.memory_manager.variables_address[node.value],
                    "addr_mode": AddressMode.DIRECT,
                }
            )
            return False
        return True

    def compile(self, node):
        if node.type == Parser.PROG:
            self.compile(node.op1)
            self.gen({"opcode": Opcode.HLT})
        elif node.type == Parser.SEQ:
            self.compile(node.op1)

            self.compile(node.op2)
        elif node.type == Parser.EMPTY:
            pass
        elif node.type == Parser.OPERATOR:
            if node.value == "=":
                if node.op2.type == Parser.STRING_CONST:
                    self.compile(node.op1)
                    self.compile(node.op2)
                else:
                    op2 = self.pre_compile(node.op2)
                    if op2:
                        self.compile(node.op2)
                    self.compile(node.op1)
            elif node.value == "<" or node.value == "==":
                op1 = self.pre_compile(node.op1)
                if op1:
                    self.compile(node.op1)
                if node.op2.type == Parser.VAR:
                    self.gen(
                        {
                            "opcode": Opcode.CMP,
                            "arg": self.memory_manager.variables_address[node.op2.value],
                            "addr_mode": AddressMode.DIRECT,
                        }
                    )
                elif node.op2.type == Parser.INT_CONST:
                    self.gen(
                        {
                            "opcode": Opcode.CMP,
                            "arg": node.op2.value,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                else:
                    self.compile(node.op2)
            elif node.value == "+":
                op1 = self.pre_compile(node.op1)
                if op1:
                    self.compile(node.op1)
                if node.op2.type == Parser.VAR:
                    self.gen(
                        {
                            "opcode": Opcode.ADD,
                            "arg": self.memory_manager.variables_address[node.op2.value],
                            "addr_mode": AddressMode.DIRECT,
                        }
                    )
                elif node.op2.type == Parser.INT_CONST:
                    self.gen(
                        {
                            "opcode": Opcode.ADD,
                            "arg": node.op2.value,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                else:
                    self.compile(node.op2)
            elif node.value == "%":
                op1 = self.pre_compile(node.op1)
                if op1:
                    self.compile(node.op1)
                if node.op2.type == Parser.VAR:
                    self.gen(
                        {
                            "opcode": Opcode.DIV,
                            "arg": self.memory_manager.variables_address[node.op2.value],
                            "addr_mode": AddressMode.DIRECT,
                        }
                    )
                elif node.op2.type == Parser.INT_CONST:
                    self.gen(
                        {
                            "opcode": Opcode.DIV,
                            "arg": node.op2.value,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                else:
                    self.compile(node.op2)
            elif node.value == "-":
                op1 = self.pre_compile(node.op1)
                if op1:
                    self.compile(node.op1)
                if node.op2.type == Parser.VAR:
                    self.gen(
                        {
                            "opcode": Opcode.SUB,
                            "arg": self.memory_manager.variables_address[node.op2.value],
                            "addr_mode": AddressMode.DIRECT,
                        }
                    )
                elif node.op2.type == Parser.INT_CONST:
                    self.gen(
                        {
                            "opcode": Opcode.SUB,
                            "arg": node.op2.value,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )

                else:
                    self.compile(node.op2)

        elif node.type == Parser.VAR_INT:
            self.gen(
                {
                    "opcode": Opcode.ST,
                    "arg": self.memory_manager.memory_counter,
                    "addr_mode": AddressMode.IMMEDIATE,
                }
            )
            self.memory_manager.variables_address[node.value] = self.memory_manager.memory_counter
            self.memory_manager.variables_types[node.value] = "int"
            self.memory_manager.memory_counter += 1

        elif node.type == Parser.VAR_STRING:
            self.memory_manager.variables_address[node.value] = self.memory_manager.memory_counter
            self.memory_manager.variables_types[node.value] = "string"
        elif node.type == Parser.INT_CONST:
            self.gen(
                {
                    "opcode": Opcode.LD,
                    "arg": node.value,
                    "addr_mode": AddressMode.IMMEDIATE,
                }
            )

        elif node.type == Parser.STRING_CONST:
            value = node.value
            self.gen(
                {
                    "opcode": Opcode.LD,
                    "arg": len(value),
                    "addr_mode": AddressMode.IMMEDIATE,
                }
            )
            self.gen(
                {
                    "opcode": Opcode.ST,
                    "arg": self.memory_manager.memory_counter,
                    "addr_mode": AddressMode.IMMEDIATE,
                }
            )
            self.memory_manager.memory_counter += 1
            for i in range(len(value)):
                self.gen(
                    {
                        "opcode": Opcode.LD,
                        "arg": ord(value[i]),
                        "addr_mode": AddressMode.IMMEDIATE,
                    }
                )
                self.gen(
                    {
                        "opcode": Opcode.ST,
                        "arg": self.memory_manager.memory_counter,
                        "addr_mode": AddressMode.IMMEDIATE,
                    }
                )
                self.memory_manager.memory_counter += 1

        elif Parser.VAR == node.type:
            if self.memory_manager.variables_types[node.value] == "int":
                self.gen(
                    {
                        "opcode": Opcode.ST,
                        "arg": self.memory_manager.variables_address[node.value],
                        "addr_mode": AddressMode.IMMEDIATE,
                    }
                )
            else:
                self.memory_manager.variables_address[node.value] = self.memory_manager.memory_counter

        elif node.type == Parser.KEY_WORDS:
            if node.value == "if":
                self.compile(node.op1)
                index = self.pc
                is_else = node.op3 is not None
                if node.op1.value == "<":
                    self.gen(
                        {
                            "opcode": Opcode.JGE,
                            "arg": 0,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )

                elif node.op1.value == "==":
                    self.gen(
                        {
                            "opcode": Opcode.JNZ,
                            "arg": 0,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )

                self.compile(node.op2)
                if node.op1.value == "<":
                    self.program[index] = {
                        "opcode": Opcode.JGE,
                        "arg": self.pc + 1 if is_else else self.pc,
                        "addr_mode": AddressMode.IMMEDIATE,
                    }

                elif node.op1.value == "==":
                    self.program[index] = {
                        "opcode": Opcode.JNZ,
                        "arg": self.pc + 1 if is_else else self.pc,
                        "addr_mode": AddressMode.IMMEDIATE,
                    }

                if node.op3 is not None:
                    index = self.pc
                    self.gen(
                        {
                            "opcode": Opcode.JMP,
                            "arg": 0,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                    self.compile(node.op3)
                    self.program[index] = {
                        "opcode": Opcode.JMP,
                        "arg": self.pc,
                        "addr_mode": AddressMode.IMMEDIATE,
                    }
            elif node.value == "while":
                cond_pc = self.pc
                self.compile(node.op1)
                index = self.pc
                if node.op1.value == "<":
                    self.gen(
                        {
                            "opcode": Opcode.JGE,
                            "arg": 0,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                elif node.op1.value == "==":
                    self.gen(
                        {
                            "opcode": Opcode.JNZ,
                            "arg": 0,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                elif node.op1.value == ">":
                    self.gen(
                        {
                            "opcode": Opcode.JN,
                            "arg": 0,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                self.compile(node.op2)
                self.gen(
                    {
                        "opcode": Opcode.JMP,
                        "arg": cond_pc,
                        "addr_mode": AddressMode.IMMEDIATE,
                    }
                )
                if node.op1.value == "<":
                    self.program[index] = {
                        "opcode": Opcode.JGE,
                        "arg": self.pc,
                        "addr_mode": AddressMode.IMMEDIATE,
                    }

                elif node.op1.value == "==":
                    self.program[index] = {
                        "opcode": Opcode.JNZ,
                        "arg": self.pc,
                        "addr_mode": AddressMode.IMMEDIATE,
                    }
                elif node.op1.value == ">":
                    self.program[index] = {
                        "opcode": Opcode.JLE,
                        "arg": self.pc,
                        "addr_mode": AddressMode.IMMEDIATE,
                    }
        elif node.type == Parser.FUNC:
            if node.value == "print":
                if node.op1.type == Parser.INT_CONST:
                    self.gen({"opcode": Opcode.OUT})
                elif (
                    node.op1.type == Parser.STRING_CONST
                    or self.memory_manager.variables_types[node.op1.value] == "string"
                ):
                    value = node.op1.value
                    if node.op1.type == Parser.STRING_CONST:
                        self.memory_manager.variables_address[node.value] = self.memory_manager.memory_counter
                        self.memory_manager.variables_types[node.value] = "string"
                        self.compile(node.op1)
                        value = node.value
                    var_addr = self.memory_manager.variables_address[value]
                    print(var_addr)

                    self.gen(
                        {
                            "opcode": Opcode.LD,
                            "arg": self.memory_manager.variables_address[value],
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )

                    self.memory_manager.variables_address["ptr"] = 100
                    self.gen(
                        {
                            "opcode": Opcode.ST,
                            "arg": self.memory_manager.variables_address["ptr"],
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                    self.memory_manager.variables_address["temp_count"] = 101
                    self.gen(
                        {
                            "opcode": Opcode.LD,
                            "arg": self.memory_manager.variables_address[value],
                            "addr_mode": AddressMode.DIRECT,
                        }
                    )
                    self.gen(
                        {
                            "opcode": Opcode.ST,
                            "arg": self.memory_manager.variables_address["temp_count"],
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )

                    temp = self.pc
                    self.gen(
                        {
                            "opcode": Opcode.LD,
                            "arg": self.memory_manager.variables_address["ptr"],
                            "addr_mode": AddressMode.DIRECT,
                        }
                    )
                    self.gen(
                        {
                            "opcode": Opcode.ADD,
                            "arg": 1,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                    self.gen(
                        {
                            "opcode": Opcode.ST,
                            "arg": self.memory_manager.variables_address["ptr"],
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )

                    self.gen(
                        {
                            "opcode": Opcode.LD,
                            "arg": self.memory_manager.variables_address["temp_count"],
                            "addr_mode": AddressMode.DIRECT,
                        }
                    )
                    self.gen(
                        {
                            "opcode": Opcode.SUB,
                            "arg": 1,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                    self.gen(
                        {
                            "opcode": Opcode.ST,
                            "arg": self.memory_manager.variables_address["temp_count"],
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )

                    self.gen(
                        {
                            "opcode": Opcode.JN,
                            "arg": self.pc + 4,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                    self.gen(
                        {
                            "opcode": Opcode.LD,
                            "arg": self.memory_manager.variables_address["ptr"],
                            "addr_mode": AddressMode.INDIRECT,
                        }
                    )
                    self.gen({"opcode": Opcode.OUTC})
                    self.gen(
                        {
                            "opcode": Opcode.JMP,
                            "arg": temp,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                elif self.memory_manager.variables_types[node.op1.value] == "int":
                    self.gen(
                        {
                            "opcode": Opcode.LD,
                            "arg": self.memory_manager.variables_address[node.op1.value],
                            "addr_mode": AddressMode.DIRECT,
                        }
                    )
                    self.gen({"opcode": Opcode.OUT})

            elif node.value == "input":
                if self.memory_manager.variables_types[node.op1.value] == "string":
                    var = node.op1.value

                    addr_ptr = self.memory_manager.memory_counter
                    self.memory_manager.memory_counter += 1
                    self.memory_manager.variables_address[var] = self.memory_manager.memory_counter
                    addr_length = self.memory_manager.memory_counter
                    self.gen(
                        {
                            "opcode": Opcode.LD,
                            "arg": 0,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                    self.gen(
                        {
                            "opcode": Opcode.ST,
                            "arg": self.memory_manager.memory_counter,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                    self.memory_manager.memory_counter += 1
                    self.gen(
                        {
                            "opcode": Opcode.LD,
                            "arg": self.memory_manager.memory_counter,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                    self.gen(
                        {
                            "opcode": Opcode.ST,
                            "arg": addr_ptr,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                    temp = self.pc
                    self.gen({"opcode": Opcode.IN})
                    self.gen(
                        {
                            "opcode": Opcode.JZ,
                            "arg": self.pc + 9,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                    self.gen(
                        {
                            "opcode": Opcode.ST,
                            "arg": addr_ptr,
                            "addr_mode": AddressMode.DIRECT,
                        }
                    )

                    self.gen(
                        {
                            "opcode": Opcode.LD,
                            "arg": addr_length,
                            "addr_mode": AddressMode.DIRECT,
                        }
                    )
                    self.gen(
                        {
                            "opcode": Opcode.ADD,
                            "arg": 1,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                    self.gen(
                        {
                            "opcode": Opcode.ST,
                            "arg": addr_length,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )

                    self.gen(
                        {
                            "opcode": Opcode.LD,
                            "arg": addr_ptr,
                            "addr_mode": AddressMode.DIRECT,
                        }
                    )
                    self.gen(
                        {
                            "opcode": Opcode.ADD,
                            "arg": 1,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                    self.gen(
                        {
                            "opcode": Opcode.ST,
                            "arg": addr_ptr,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )

                    self.gen(
                        {
                            "opcode": Opcode.JMP,
                            "arg": temp,
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
                    self.memory_manager.memory_counter += 20
                elif self.memory_manager.variables_types[node.op1.value] == "int":
                    var = node.op1.value
                    self.gen({"opcode": Opcode.IN})
                    self.gen(
                        {
                            "opcode": Opcode.ST,
                            "arg": self.memory_manager.variables_address[var],
                            "addr_mode": AddressMode.IMMEDIATE,
                        }
                    )
            elif node.value == "input_char":
                var = node.op1.value
                self.gen({"opcode": Opcode.IN})
                self.gen(
                    {
                        "opcode": Opcode.ST,
                        "arg": self.memory_manager.variables_address[var] + 1,
                        "addr_mode": AddressMode.IMMEDIATE,
                    }
                )
            elif node.value == "print_char":
                self.gen(
                    {
                        "opcode": Opcode.LD,
                        "arg": self.memory_manager.variables_address[node.op1.value] + 1,
                        "addr_mode": AddressMode.DIRECT,
                    }
                )
                self.gen({"opcode": Opcode.OUTC})

        return self.program


def main(source, target):
    with (source, "r") as file:
        data = file.read().replace("\n", "")

    print(data)
    parser = Parser(Lexer(), Lexer().lex(data))
    node = parser.parse()
    mm = MemoryManager()

    compiler = Compiler(mm, node)
    program = compiler.compile(node)
    count = 0
    for i in program:
        print(f"{count}. {i}")
        count += 1
    write_code(target, program)


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
