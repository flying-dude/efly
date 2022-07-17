import os, subprocess, atexit, sys, re, math
from pathlib import Path

__all__ = ["version", "log", "info", "error", "parse_size", "r", "sudo", "chroot", "get", "du"]

version = "UNKNOWN_VERSION"

# colored output, if corresponding python module is available
try:
    import colorama
    from colorama import Fore, Back, Style
    colorama.init()
    yellow = lambda s: Fore.YELLOW + s + Style.RESET_ALL
    green = lambda s: Fore.GREEN + s + Style.RESET_ALL
    red = lambda s: Fore.RED + s + Style.RESET_ALL
    light_cyan = lambda s: Fore.LIGHTCYAN_EX + s + Style.RESET_ALL
    light_green = lambda s: Fore.LIGHTGREEN_EX + s + Style.RESET_ALL
    light_magenta = lambda s: Fore.LIGHTMAGENTA_EX + s + Style.RESET_ALL
    light_red = lambda s: Fore.LIGHTRED_EX + s + Style.RESET_ALL
except ImportError:
    yellow = lambda s: s
    green = lambda s: s
    red = lambda s: s
    light_cyan = lambda s: s
    light_green = lambda s: s
    light_magenta = lambda s: s
    light_red = lambda s: s

def log(prefix, msg):
    print(f"[{prefix}] {msg}")

def info(msg):
    log(yellow("info"), msg)

def error(msg):
    log(light_red("error"), msg)

# https://stackoverflow.com/questions/33341000/extract-numbers-and-size-information-kb-mb-etc-from-a-string-in-python
size_regex = re.compile(r'(\d+(?:\.\d+)?)\s*([bkmgtp]?)', re.IGNORECASE)
size_order = ['b', 'k', 'm', 'g', 't', 'p']
def parse_size(size_string): # parse size string and return size in bytes
    match = size_regex.findall(size_string)
    if not match:
            raise Exception(f'invalid size: "{size_string}"')
    value, unit = match[0]
    unit = unit if unit else "b" # unit is optional. default is byte.
    return int(float(value) * (1024**size_order.index(unit.lower())))

elib_exiting = False
def r(args, ignore_error=False, **kwargs):
    global elib_exiting
    cmd = ' '.join(str(arg) for arg in args)
    log(light_cyan("exec"), cmd)

    returncode = subprocess.run(args, **kwargs).returncode
    if not returncode == 0 and not ignore_error:
        error(f'command failed: {red(cmd)}')

        # exit on error. but don't call exit again, if we are already exiting (this could happen, if we have another error during cleanup).
        if not elib_exiting:
            elib_exiting = True
            exit(1)
    else:
        return returncode

def sudo(args, **kwargs):
        return r(["sudo"] + args, **kwargs)

# run a command inside chroot. note that we don't pass **kwargs to python subcommand.
# instead, we use **kwargs here to define environment variables to be used inside chroot. if we were
# to define **kwargs and pass that verbatim to python subcommand, then env would only be passed to "arch-chroot"
# but not available inside the actual chroot (which is what we want).
def chroot(path, args, **kwargs):
    path = Path(path) # make sure path is an actual Path()

    # assign optional environment variables to command, passed as **kwargs
    cmd = []
    for key, value in kwargs.items():
        print(f"{key}={value}")
        cmd += [f"{key}={value}"]

    cmd += ["arch-chroot", path] + args
    returncode = sudo(cmd)

    # do a safety lazy umount:
    # umount after chroot often does not go smoothly/reliably. try lazy umount here to umount stuff that is still mounted.
    # umount will error, in case path in question has already been umounted successfully.
    # this is actually what we want anyway, so not really an error. therefore, we can ignore umount error here.
    sudo(["umount", "--lazy", "--quiet", path / "dev"], ignore_error=True)
    sudo(["umount", "--lazy", "--quiet", path / "proc"], ignore_error=True)
    sudo(["umount", "--lazy", "--quiet", path / "sys"], ignore_error=True)

    return returncode

def get(args, **kwargs):
    log(light_cyan("get"), ' '.join(str(arg) for arg in args))
    return subprocess.check_output(args, **kwargs).decode('utf-8').rstrip()

# obtain disk usage in bytes
def du(path, **kwargs):
    return int(get(['sudo', 'du','--summarize', '--bytes', path], **kwargs).split()[0])
