import contextlib
import io
import logging
import os
import tempfile

import pytest

import machine
import translator


def print_ast(node, level=0):
    if node is None:
        return
    print("  " * level + str(node.type) + ": " + str(node.value))
    if node.op1:
        print_ast(node.op1, level + 1)
    if node.op2:
        print_ast(node.op2, level + 1)
    if node.op3:
        print_ast(node.op3, level + 1)


@pytest.mark.golden_test("golden/*.yml")
def test_parser(golden):
    with contextlib.redirect_stdout(io.StringIO()) as stdout:
        with io.StringIO(golden["in_source"]) as f:
            data = f.read().replace("\n", "")
            parser = translator.Parser(translator.Lexer(), translator.Lexer().lex(data))
            node = parser.parse()
            print_ast(node)

    assert stdout.getvalue() == golden.out["out_ast"]


@pytest.mark.golden_test("golden/*.yml")
def test_translator_and_machine(golden, caplog):
    # Установим уровень отладочного вывода на DEBUG
    caplog.set_level(logging.DEBUG)

    # Создаём временную папку для тестирования приложения.
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Готовим имена файлов для входных и выходных данных.
        source = os.path.join(tmpdirname, "source.txt")
        input_stream = os.path.join(tmpdirname, "input.txt")
        target = os.path.join(tmpdirname, "target.o")

        # Записываем входные данные в файлы. Данные берутся из теста.
        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_source"])
            # print(golden["in_source"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])
            # print(golden["in_stdin"])

        # Запускаем транслятор и собираем весь стандартный вывод в переменную
        # stdout
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main(source, target)
            print("============================================================")
            machine.main(target, input_stream)

        # Выходные данные также считываем в переменные.
        with open(target, encoding="utf-8") as file:
            code = file.read()

        # Проверяем, что ожидания соответствуют реальности.
        assert code == golden.out["out_code"]
        assert stdout.getvalue() == golden.out["out_stdout"]
        assert caplog.text == golden.out["out_log"]
