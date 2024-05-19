
import json
from collections import namedtuple
from enum import Enum
import enum

class Opcode(str, Enum):

    ST = "ST"
    LD = "LD"
    ADD = "ADD"
    SUB = "SUB"
    DIV = "DIV"
    JNZ = "JNZ"
    JZ = "JZ"
    JN = "JN"
    JMP = "JMP"
    CMP = "CMP"
    HLT = "HLT"
    OUT = "OUT"
    IN = "IN"
    JGE = "JGE"

    def __str__(self):
        return str(self.value)

class AddressMode(str, enum.Enum):
    IMMEDIATE = "IMMEDIATE"
    DIRECT = "DIRECT"
    INDIRECT = "INDIRECT"

    def __str__(self):
        return str(self.value)


class Term(namedtuple("Term", "opcode arg addr_mode")):
    """Описание выражения из исходного текста программы.

    Сделано через класс, чтобы был docstring.
    """


def write_code(filename, code):
    """Записать машинный код в файл."""
    with open(filename, 'w', encoding="utf-8") as file:
        json.dump(code, file, indent=4)
        file.write('\n')


def read_code(filename):
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        # Конвертация строки в Opcode
        instr["opcode"] = Opcode(instr["opcode"])

        if 'arg' in instr:
            instr['addr_mode'] = AddressMode(instr['addr_mode'])

    return code

