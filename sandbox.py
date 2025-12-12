from RestrictedPython import compile_restricted, safe_globals, utility_builtins

def run_code(user_code: str) -> str:
    try:
        byte_code = compile_restricted(user_code, '<string>', 'exec')
        restricted_globals = safe_globals.copy()
        restricted_globals['__builtins__'].update(utility_builtins)
        restricted_locals = {}
        exec(byte_code, restricted_globals, restricted_locals)
        if 'result' in restricted_locals:
            return str(restricted_locals['result'])
        else:
            return "Код выполнен успешно. Нет переменной result для вывода."
    except Exception as e:
        return f"Ошибка: {e}"

def run_tests(user_code: str, tests: list) -> str:
    results = []
    for i, test in enumerate(tests, 1):
        code = user_code + f"\nresult = {test['input']}"
        output = run_code(code)
        if output == str(test['expected']):
            results.append(f"Тест {i}: ✅ OK")
        else:
            results.append(f"Тест {i}: ❌ Ошибка, ожидается {test['expected']}, получено {output}")
    return "\n".join(results)