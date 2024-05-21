import logging
import sys
from enum import Enum

from isa import AddressMode, Opcode, read_code


class AccMuxSignals(Enum):
    ALU = 0
    IN = 1


class DAMuxSignals(Enum):
    DR = 0
    CU = 1


class DRMuxSignals(Enum):
    DM = 0
    CU = 1


class DataPath:
    data_memory_size = None
    data_memory = None
    data_address = None
    acc = None
    input_buffer = None
    output_buffer = None
    data_register = None
    alu = None
    MAX_WORD_SIZE = 2147483647
    MIN_WORD_SIZE = -2147483648

    def __init__(self, data, data_memory_size, input_buffer):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.data_memory_size = data_memory_size
        self.data_memory = data
        self.data_address = 0
        self.acc = 0
        self.input_buffer = input_buffer
        self.output_buffer = []
        self.data_register = 0
        self.input_buffer_counter = 0

    def signal_latch_data_address(self, sel: DAMuxSignals, val: int):
        assert sel in {
            DAMuxSignals.DR,
            DAMuxSignals.CU,
        }, "internal error, incorrect selector: {}".format(sel)
        if sel == DAMuxSignals.DR:
            self.data_address = self.data_register
        elif sel == DAMuxSignals.CU:
            self.data_address = val
        assert 0 <= self.data_address < self.data_memory_size, "out of memory: {}".format(self.data_address)

    def signal_latch_data_reg(self, sel: DRMuxSignals, val: int):
        assert sel in {
            DRMuxSignals.DM,
            DRMuxSignals.CU,
        }, "internal error, incorrect selector: {}".format(sel)
        if sel == DRMuxSignals.DM:
            self.data_register = int(val)
        elif sel == DRMuxSignals.CU:
            self.data_register = int(val)

    def signal_latch_acc(self, sel: AccMuxSignals):
        assert sel in {
            AccMuxSignals.ALU,
            AccMuxSignals.IN,
        }, "internal error, incorrect selector: {}".format(sel)
        if sel == AccMuxSignals.ALU:
            self.acc = self.alu
            if self.acc > self.MAX_WORD_SIZE:
                self.acc = self.MIN_WORD_SIZE
            elif self.acc < self.MIN_WORD_SIZE:
                self.acc = self.MAX_WORD_SIZE
        elif sel == AccMuxSignals.IN:
            if len(self.input_buffer) == 0:
                raise EOFError()
            symbol = ord(self.input_buffer[self.input_buffer_counter])
            self.input_buffer_counter += 1
            self.acc = symbol
            logging.debug("input: %s", repr(symbol))

    def signal_wr_to_memory(self):
        self.data_memory[self.data_address] = self.acc

    def signal_oe_memory(self):
        return self.data_memory[int(self.data_address)]

    def zero_flag(self):
        return self.acc == 0

    def neg_flag(self):
        return self.acc < 0

    def signal_alu_add(self):
        self.alu = self.acc + self.data_register

    def signal_alu_sub(self):
        self.alu = self.acc - self.data_register

    def signal_alu_div(self):
        assert self.data_register != 0, "internal error, incorrect data: {}".format(self.data_register)
        self.alu = self.acc % self.data_register

    def signal_alu_only_right_in(self):
        self.alu = self.data_register

    def signal_latch_out(self):
        symbol = chr(self.acc)
        logging.debug("output: %s << %s", repr("".join(self.output_buffer)), repr(symbol))
        self.output_buffer.append(symbol)


class ControlUnit:
    def __init__(self, program, data_path):
        self.program = program
        self.program_counter = 0
        self.data_path = data_path
        self._tick = 0

    def tick(self):
        self._tick += 1
        logging.debug("%s", self)

    def current_tick(self):
        return self._tick

    def signal_latch_program_counter(self, sel_next):
        if sel_next:
            self.program_counter += 1
        else:
            instr = self.program[self.program_counter]
            assert "arg" in instr, "internal error"
            self.program_counter = instr["arg"]

    def operand_fetch(self, instr):
        value = instr["arg"]
        if instr["addr_mode"] == AddressMode.IMMEDIATE.value:
            self.data_path.signal_latch_data_reg(DRMuxSignals.CU, value)
            self.tick()
        elif instr["addr_mode"] == AddressMode.DIRECT.value:
            self.data_path.signal_latch_data_address(DAMuxSignals.CU, value)
            val = self.data_path.signal_oe_memory()
            self.tick()
            self.data_path.signal_latch_data_reg(DRMuxSignals.DM, val)
            self.tick()
        elif instr["addr_mode"] == AddressMode.INDIRECT.value:
            self.data_path.signal_latch_data_address(DAMuxSignals.CU, value)
            val = self.data_path.signal_oe_memory()
            self.tick()
            self.data_path.signal_latch_data_reg(DRMuxSignals.DM, val)
            self.tick()
            self.data_path.signal_latch_data_address(DAMuxSignals.DR, value)
            val = self.data_path.signal_oe_memory()
            self.tick()
            self.data_path.signal_latch_data_reg(DRMuxSignals.DM, val)
            self.tick()

    def decode_and_execute_instruction(self):
        instr = self.program[self.program_counter]
        opcode = instr["opcode"]
        logging.info("instruction: %s", instr)
        if opcode == Opcode.LD:
            self.operand_fetch(instr)
            self.signal_latch_program_counter(sel_next=True)
            self.data_path.signal_alu_only_right_in()
            self.data_path.signal_latch_acc(AccMuxSignals.ALU)
            self.tick()
        elif opcode == Opcode.ST:
            self.operand_fetch(instr)
            self.signal_latch_program_counter(sel_next=True)
            self.data_path.signal_latch_data_address(sel=DAMuxSignals.DR, val=None)
            self.tick()
            self.data_path.signal_wr_to_memory()
            self.tick()
        elif opcode in [Opcode.SUB, Opcode.CMP, Opcode.ADD, Opcode.DIV]:
            self.operand_fetch(instr)
            self.signal_latch_program_counter(sel_next=True)
            if opcode == Opcode.ADD:
                self.data_path.signal_alu_add()
            elif opcode == Opcode.DIV:
                self.data_path.signal_alu_div()
            else:
                self.data_path.signal_alu_sub()
            self.tick()
            self.data_path.signal_latch_acc(AccMuxSignals.ALU)
            self.tick()
        elif opcode == Opcode.JMP:
            self.signal_latch_program_counter(sel_next=False)
            self.tick()
        elif opcode == Opcode.JNZ:
            self.signal_latch_program_counter(self.data_path.zero_flag())
            self.tick()
        elif opcode == Opcode.JZ:
            self.signal_latch_program_counter(not self.data_path.zero_flag())
            self.tick()
        elif opcode == Opcode.JN:
            self.signal_latch_program_counter(not self.data_path.neg_flag())
            self.tick()
        elif opcode == Opcode.JLE:
            self.signal_latch_program_counter(
                not (self.data_path.neg_flag() or (not self.data_path.neg_flag() and self.data_path.zero_flag()))
            )
            self.tick()
        elif opcode == Opcode.JGE:
            self.signal_latch_program_counter((not self.data_path.zero_flag()) and self.data_path.neg_flag())
            self.tick()
        elif opcode == Opcode.IN:
            self.data_path.signal_latch_acc(AccMuxSignals.IN)
            self.signal_latch_program_counter(sel_next=True)
            self.tick()
        elif opcode == Opcode.OUT:
            self.data_path.signal_latch_out()
            self.signal_latch_program_counter(sel_next=True)
            self.tick()
        elif opcode == Opcode.HLT:
            raise StopIteration()

    def __repr__(self):
        return "{{TICK: {}, PC: {}, ADDR: {}, ACC: {}, DR: {}, DA {}}}".format(
            self._tick,
            self.program_counter,
            self.data_path.data_address,
            self.data_path.acc,
            self.data_path.data_register,
            self.data_path.data_address,
        )


def simulation(data, code, input_tokens, data_memory_size, limit):
    data_path = DataPath(data, data_memory_size, input_tokens)
    control_unit = ControlUnit(code, data_path)
    instr_counter = 0
    try:
        while instr_counter < limit:
            control_unit.decode_and_execute_instruction()
            instr_counter += 1

    except StopIteration:
        pass
    except AssertionError as e:
        print("Error: {}".format(e))
    output = ""
    for i in control_unit.data_path.output_buffer:
        output += i
    print("".join(output))
    print("instr_counter: ", instr_counter, "ticks:", control_unit.current_tick())
    if instr_counter >= limit:
        logging.warning("Limit exceeded!")


def main(code_file, input_file):
    data, code = read_code(code_file)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)
        input_token.append("\x00")

    simulation(
        data,
        code,
        input_tokens=input_token,
        data_memory_size=256,
        limit=1000,
    )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
