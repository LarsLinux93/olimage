import os
import importlib
import inspect

from .base import SetupAbstract

from .apt import SetupApt
from .blueman import SetupBlueman
from .boot import SetupBoot
from .console import SetupConsole
from .fstab import SetupFstab
from .hostname import SetupHostname
from .kernel import SetupKernel
from .locales import SetupLocales
from .network import SetupNetwork
from .timezone import SetupTimezone
from .user import SetupUser
from .extra import SetupExtra
from .displaymanager import SetupDisplayManager

pool = None


class SetupMeta(type):
    def __getattribute__(self, item):

        global pool
        if pool is None:
            for (path, dirs, files) in os.walk(os.path.dirname(__file__)):
                # Don't walk subdirectories
                if path != os.path.dirname(__file__):
                    continue

                for file in files:
                    file = str(file)
                    if file.endswith('.py'):
                        module = os.path.splitext(file)[0]

                        if module == '__init__' or module == 'setup':
                            continue

                        # Import module
                        obj = importlib.import_module('olimage.core.setup.' + module)

                        # Check if there is class with SetupAbstract as base
                        for _, cls in inspect.getmembers(obj, inspect.isclass):
                            if cls != SetupAbstract:
                                for t in inspect.getmro(cls):
                                    if t == SetupAbstract:
                                        if pool is None:
                                            pool = {}
                                        pool[module] = cls

        if pool and item in pool:
            return pool[item]().setup

        return type.__getattribute__(self, item)


class Setup(metaclass=SetupMeta):
    apt: SetupApt
    blueman: SetupBlueman
    boot: SetupBoot
    console: SetupConsole
    fstab: SetupFstab
    hostname: SetupHostname
    kernel: SetupKernel
    locales: SetupLocales
    network: SetupNetwork
    timezone: SetupTimezone
    user: SetupUser
    extra: SetupExtra
    displaymanager: SetupDisplayManager
