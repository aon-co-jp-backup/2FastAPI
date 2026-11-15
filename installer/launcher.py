# PyInstaller entry point: no argument -> GUI wizard, "web" -> local browser wizard, other args -> CLI.
import sys
from tofastapi.cli import main

if __name__ == "__main__":
    argv = sys.argv[1:] or ["gui"]
    raise SystemExit(main(argv))
