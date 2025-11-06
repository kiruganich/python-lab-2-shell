import shlex    # Для корректной обработки кавычек
import platform

def parse_command(command_line):
    try:
        if platform.system() == "Windows":
            command_line = command_line.replace("\\", "/")
        parts = shlex.split(command_line.strip())
        if not parts:
            return None, []
        cmd = parts[0].lower()
        args = parts[1:]
        return cmd, args
    except ValueError as e:
        error_msg = str(e)
        if "No closing quotation" in error_msg:
            error_msg = "Ошибка: Незакрытые кавычки в команде"
        return None, [error_msg]