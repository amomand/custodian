"""PyInstaller entry script for the Custodian desktop app.

The real logic lives in custodian.app_shell; PyInstaller just needs a
script (not a module) to anchor the build.
"""

from custodian.app_shell import main

if __name__ == "__main__":
    main()
