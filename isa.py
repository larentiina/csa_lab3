import enum
import json
from enum import Enum


class Opcode(str, Enum):
    ST = "ST"
    LD = "LD"
    ADD = "ADD"
    SUB = "SUB"
    DIV = "DIV"
    JNZ = "JNZ"
    JZ = "JZ"
    JN = "JN"
    JLE = "JLE"
    JMP = "JMP"
    CMP = "CMP"
    HLT = "HLT"
    OUT = "OUT"
    OUTC = "OUTC"
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


def write_code(filename, code, data):
    """Записать машинный код в файл."""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(code, file, indent=4)
        file.write("\n")
    with open("data_section.txt", "w", encoding="utf-8") as file:
        file.write(json.dumps(data, indent=4))


def read_code(filename):
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        # Конвертация строки в Opcode
        instr["opcode"] = Opcode(instr["opcode"])

        if "arg" in instr:
            instr["addr_mode"] = AddressMode(instr["addr_mode"])

    with open("data_section.txt", encoding="utf-8") as file:
        data_section = json.loads(file.read())

    return data_section, code
