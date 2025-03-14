import sys
import os

class Tee:
    def __init__(self, filename, mode="w"):
        self.file = open(filename, mode, encoding="utf-8")
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self

    def write(self, message):
        self.stdout.write(message)
        self.file.write(message)

    def flush(self):
        self.stdout.flush()
        self.file.flush()

    def close(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        self.file.close()

# Configurar el log
log_file = "output.log"

# Borra el log anterior si existe
if os.path.exists(log_file):
    os.remove(log_file)

# Inicia el registro de logs
log_manager = Tee(log_file)
