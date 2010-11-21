#!/usr/bin/env python
import os
import sys

from django.core.management import execute_manager, setup_environ

try:
    import settings_local as settings
except ImportError:
    try:
        import settings
    except ImportError:
        import sys
        sys.stderr.write(
            "Error: Tried importing 'settings_local.py' and 'settings.py' "
            "but neither could be found (or they're throwing an ImportError)."
            " Please come back and try again later.")
        raise

if __name__ == "__main__":
    execute_manager(settings)
