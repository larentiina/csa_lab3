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
            if match:
                pos = match.end(0)
            else:

                raise ValueError("Illegal character: {}".format(characters[pos]))
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
    CMP_OP: ClassVar[list[str]] = ["<", "==", ">"]

    def __init__(self, lexer, tokens):
        self.lexer = lexer
        self.tokens = tokens
        self.token_index = 0

    def next_token(self):
        self.token_index = self.token_index + 1

    def get_token_type(self):
        return self.tokens[self.token_index][1]

    def get_token_text(self):
        return self.tokens[self.token_index][0]

    def get_token(self):
        return self.tokens[self.token_index]

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
        if node.value not in Parser.CMP_OP:
            temp = node.op2
            while temp.value not in Parser.CMP_OP:
                temp = temp.op2
            new_node = temp
            temp = temp.op1
            node.op2 = temp
            new_node.op1 = node
        return new_node

    def kind_of_node(self, token):
        kind = token[1]
        if kind == TokensName.ID:
            if self.tokens[self.token_index - 1][0] == "int":
                node = Node(Parser.VAR_INT, self.get_token_text())
            elif self.tokens[self.token_index - 1][0] == "string":
                node = Node(Parser.VAR_STRING, self.get_token_text())
            else:
                node = Node(Parser.VAR, self.get_token_text())
        elif kind == TokensName.INT:
            node = Node(Parser.INT_CONST, self.get_token_text())
        else:
            node = Node(Parser.STRING_CONST, self.get_token_text().replace('"', ""))
        return node

    def statement(self):
        n = None
        if self.get_token_type() == TokensName.KEY_WORDS:
            if self.get_token_text() != "else":
                n = Node(Parser.KEY_WORDS, self.get_token_text(), op1=self.cond_expression())
                n.op2 = self.cond_expression()
                self.next_token()
            if self.get_token_text() == "else":
                self.next_token()
                n.op3 = self.statement()
            else:
                self.token_index = self.token_index - 1
        elif self.get_token_type() == TokensName.FUNC:
            n = Node(Parser.FUNC, self.get_token_text())
            self.next_token()
            assert self.get_token_type() == TokensName.SEPARATOR, 'Expected "("'
            n.op1 = self.expression(n)
            self.next_token()
            assert self.get_token_type() == TokensName.SEPARATOR, 'Expected ")"'
            self.next_token()
            assert self.get_token_type() == TokensName.SEPARATOR, 'Expected ";"'
        elif self.get_token_type() == TokensName.LBRA:
            n = Node(Parser.EMPTY)
            self.next_token()
            while self.get_token_type() != TokensName.RBRA:
                n = Node(Parser.SEQ, op1=n, op2=self.statement())
                self.next_token()
        elif self.get_token_type() == TokensName.TYPE:
            self.next_token()
            n = self.statement()
        else:
            node = self.kind_of_node(self.get_token())
            n = self.expression(node)
        return n

    def parse(self):
        node = Node(Parser.PROG)
        node.op1 = self.statement()
        return node


class MemoryManager:
    def __init__(self):
        self.memory_counter = 0
        self.variables_address: dict[str, int] = {}
        self.variables_types: dict[str, int] = {}
        self.memory = [0] * 256


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
            if self.memory_manager.variables_types[node.value] == "int":
                self.gen(
                    {
                        "opcode": Opcode.LD,
                        "arg": self.memory_manager.variables_address[node.value],
                        "addr_mode": AddressMode.DIRECT,
                    }
                )
            elif (
                    self.memory_manager.variables_types[node.value] == "string"
                    and self.memory_manager.memory[self.memory_manager.variables_address[node.value]] == 1
            ):
                self.gen(
                    {
                        "opcode": Opcode.LD,
                        "arg": self.memory_manager.variables_address[node.value] + 1,
                        "addr_mode": AddressMode.DIRECT,
                    }
                )
        else:
            self.compile(node)

    def gen_op2_for_operator(self, opcode, node):
        if node.type == Parser.VAR:
            self.gen(
                {
                    "opcode": opcode,
                    "arg": self.memory_manager.variables_address[node.value],
                    "addr_mode": AddressMode.DIRECT,
                }
            )

        elif node.type == Parser.INT_CONST:
            self.gen(
                {
                    "opcode": opcode,
                    "arg": node.value,
                    "addr_mode": AddressMode.IMMEDIATE,
                }
            )
        else:
            self.compile(node)

    def compile(self, node):
        if node.type == Parser.PROG:
            self.compile(node.op1)
            self.gen({"opcode": Opcode.HLT})
        elif node.type == Parser.SEQ:
            self.compile(node.op1)
            self.compile(node.op2)
        elif node.type == Parser.EMPTY:
            pass

        elif node.type == Parser.VAR_INT:
            self.gen(
                {"opcode": Opcode.ST, "arg": self.memory_manager.memory_counter, "addr_mode": AddressMode.IMMEDIATE}
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
            self.memory_manager.memory[self.memory_manager.memory_counter] = len(value)
            self.memory_manager.memory_counter += 1
            for i in range(len(value)):
                self.memory_manager.memory[self.memory_manager.memory_counter] = ord(value[i])
                self.memory_manager.memory_counter += 1
            self.memory_manager.memory_counter += 20 - len(value)

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

        elif node.type == Parser.OPERATOR:
            if node.value == "=":
                if node.op2.type == Parser.STRING_CONST:
                    self.compile(node.op1)
                    self.compile(node.op2)
                else:
                    self.pre_compile(node.op2)
                    self.compile(node.op1)
            elif node.value in ["+", "-", "%"]:
                self.pre_compile(node.op1)
                if node.value == "+":
                    opcode = Opcode.ADD
                elif node.value == "-":
                    opcode = Opcode.SUB
                elif node.value == "%":
                    opcode = Opcode.DIV

                self.gen_op2_for_operator(opcode, node.op2)

            elif node.value in Parser.CMP_OP:
                self.pre_compile(node.op1)
                self.gen_op2_for_operator(Opcode.CMP, node.op2)

        elif node.type == Parser.KEY_WORDS:
            if node.value == "if":
                self.compile(node.op1)
                index = self.pc
                is_else = node.op3 is not None
                if node.op1.value == "<":
                    opcode = Opcode.JGE
                elif node.op1.value == "==":
                    opcode = Opcode.JNZ
                elif node.op1.value == ">":
                    opcode = Opcode.JLE

                self.gen({"opcode": opcode, "arg": 0, "addr_mode": AddressMode.IMMEDIATE})

                self.compile(node.op2)
                self.program[index] = {
                    "opcode": opcode,
                    "arg": self.pc + 1 if is_else else self.pc,
                    "addr_mode": AddressMode.IMMEDIATE,
                }

                if is_else:
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
                    opcode = Opcode.JGE
                elif node.op1.value == "==":
                    opcode = Opcode.JNZ
                elif node.op1.value == ">":
                    opcode = Opcode.JLE
                self.gen(
                    {
                        "opcode": opcode,
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
                self.program[index] = {
                    "opcode": opcode,
                    "arg": self.pc,
                    "addr_mode": AddressMode.IMMEDIATE,
                }

        elif node.type == Parser.FUNC:
            if node.value == "print":
                value = node.op1.value
                if node.op1.type == Parser.STRING_CONST:
                    value = node.value
                    self.memory_manager.variables_address[value] = self.memory_manager.memory_counter
                    self.memory_manager.variables_types[value] = "string"
                    self.compile(node.op1)

                var_addr = self.memory_manager.variables_address[value]
                self.memory_manager.memory[self.memory_manager.memory_counter + 20] = var_addr
                self.memory_manager.variables_address["ptr"] = self.memory_manager.memory_counter + 20
                self.memory_manager.memory_counter += 1
                self.memory_manager.variables_address["temp_count"] = self.memory_manager.memory_counter + 20
                self.memory_manager.memory_counter += 1
                self.gen(
                    {
                        "opcode": Opcode.LD,
                        "arg": self.memory_manager.variables_address["ptr"],
                        "addr_mode": AddressMode.INDIRECT,
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
                self.gen({"opcode": Opcode.OUT})
                self.gen(
                    {
                        "opcode": Opcode.JMP,
                        "arg": temp,
                        "addr_mode": AddressMode.IMMEDIATE,
                    }
                )
            elif node.value == "input":
                var = node.op1.value
                addr_ptr = self.memory_manager.memory_counter
                self.memory_manager.memory[addr_ptr] = addr_ptr + 2
                self.memory_manager.memory_counter += 1
                self.memory_manager.variables_address[var] = self.memory_manager.memory_counter
                addr_length = self.memory_manager.memory_counter
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
                var = node.op1.value
                self.gen(
                    {
                        "opcode": Opcode.LD,
                        "arg": self.memory_manager.variables_address[var] + 1,
                        "addr_mode": AddressMode.DIRECT,
                    }
                )
                self.gen({"opcode": Opcode.OUT})

        return self.program


def main(source, target):
    with open(source) as file:
        data = file.read()
    parser = Parser(Lexer(), Lexer().lex(data.replace("\n", "")))
    node = parser.parse()
    mm = MemoryManager()

    compiler = Compiler(mm, node)
    program = compiler.compile(node)
    write_code(target, program, mm.memory)
    print("source LoC:", data.count("\n"), "code instr:", len(program))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
