import os, subprocess, atexit, sys, re, math, pathlib
from pathlib import Path
import Reflector as reflector
import distro, platformdirs

__all__ = [
    "version", "log", "info", "error", "parse_size", "r", "sudo", "chroot", "get", "du", "colored_output",
    "pacstrap_base", "pacstrap_pkg", "reflector"
]

version = "UNKNOWN_VERSION"
colored_output = True

# colored output, if corresponding python module is available
try:
    import colorama
    from colorama import Fore, Back, Style
    colorama.init()
    yellow = lambda s: Fore.YELLOW + s + Style.RESET_ALL if colored_output else s
    green = lambda s: Fore.GREEN + s + Style.RESET_ALL if colored_output else s
    red = lambda s: Fore.RED + s + Style.RESET_ALL if colored_output else s
    light_cyan = lambda s: Fore.LIGHTCYAN_EX + s + Style.RESET_ALL if colored_output else s
    light_green = lambda s: Fore.LIGHTGREEN_EX + s + Style.RESET_ALL if colored_output else s
    light_magenta = lambda s: Fore.LIGHTMAGENTA_EX + s + Style.RESET_ALL if colored_output else s
    light_red = lambda s: Fore.LIGHTRED_EX + s + Style.RESET_ALL if colored_output else s
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

from shutil import which
import subprocess
def get_chroot_cmd():
    # check if systemd is running: https://superuser.com/questions/1017959/how-to-know-if-i-am-using-systemd-on-linux
    #if which("systemd-nspawn") and subprocess.getoutput("ps --no-headers -o comm 1") == "systemd":
        #return "systemd-nspawn"
    if which("arch-chroot"):
        return "arch-chroot"
    if which("chroot"):
        return "chroot"
    return None

# run a command inside chroot. note that we don't pass **kwargs to python subcommand.
# instead, we use **kwargs here to define environment variables to be used inside chroot. if we were
# to define **kwargs and pass that verbatim to python subcommand, then env would only be passed to "arch-chroot"
# but not available inside the actual chroot (which is what we want).
import atexit
chroot_initialized = False
def chroot(path, args, **kwargs):
    path = Path(path) # make sure path is an actual Path() object

    global chroot_initialized
    if not chroot_initialized:
        match get_chroot_cmd():
            case "chroot":
                sudo(["cp", "/etc/resolv.conf", path / "etc"])

                for mnt in ["proc", "sys", "dev"]:
                    sudo(["mount", "--bind", f"/{mnt}", path / mnt])
                    atexit.register(sudo, ["umount", "--lazy", "--quiet", path / mnt], ignore_error=True)

            case "arch-chroot":
                # safety unmount, since unmount of arch-chroot is not 100% reliable
                for mnt in ["proc", "sys", "dev"]:
                    atexit.register(sudo, ["umount", "--lazy", "--quiet", path / mnt], ignore_error=True)

        chroot_initialized = True

    # assign optional environment variables to command, passed as **kwargs
    env = []
    for key, value in kwargs.items():
        print(f"{key}={value}")
        env += [f"{key}={value}"]

    match get_chroot_cmd():
        case "systemd-nspawn":
            return sudo(env + ["systemd-nspawn", "--quiet", "-D"] + [path] + args)
        case "arch-chroot":
            return sudo(env + ["arch-chroot", path] + args)
        case "chroot":
            return sudo(env + ["chroot", path] + args)
        case _:
            # this should never happen since we check at program start that a command is available
            raise RuntimeError("Could not find chroot command. Either of: arch-chroot chroot")

def get(args, **kwargs):
    log(light_cyan("get"), ' '.join(str(arg) for arg in args))
    return subprocess.check_output(args, **kwargs).decode('utf-8').rstrip()

# obtain disk usage in bytes
def du(path, **kwargs):
    return int(get(['sudo', 'du','--summarize', '--bytes', path], **kwargs).split()[0])

# https://stackoverflow.com/questions/15644964/python-progress-bar-and-downloads
import requests, tqdm
def download(url: str, dest: pathlib.Path, chunk_size=1024):
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))
    with dest.open('wb') as file, tqdm.tqdm(
        desc=dest.absolute().as_posix(),
        total=total,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in resp.iter_content(chunk_size=chunk_size):
            size = file.write(data)
            bar.update(size)

import hashlib
def hash_download(url: str, dest: pathlib.Path, b2sum: str=None):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        download(url=url, dest=dest)
    if b2sum:
        with open(dest, "rb") as f:
            b2sum_digest = hashlib.file_digest(f, "blake2b").hexdigest()
            if not (b2sum_digest == b2sum):
                error("failure in b2sum check:")
                error(f"expected: {b2sum}")
                error(f"found:    {b2sum_digest}")
                raise RuntimeError("checksum fail")
            else:
                info("checksum: OK")

cache_dir = pathlib.Path(platformdirs.user_cache_dir("efly")) / "dd"
boot_version = "2024.05.01"
bootstrap_dir = cache_dir / f"archlinux-bootstrap-{boot_version}" / "root.x86_64"

# only install the base system
def pacstrap_base(chroot_fs, tmp):
    if distro.id() == "arch":
        sudo(["pacstrap", "-c", chroot_fs])
    else:
        # download bootstrap tarball
        dest = cache_dir / f"archlinux-bootstrap-{boot_version}-x86_64.tar.zst"
        hash_download(
            url = f"https://ftp.snt.utwente.nl/pub/os/linux/archlinux/iso/{boot_version}/archlinux-bootstrap-{boot_version}-x86_64.tar.zst",
            dest = dest,
            b2sum = "fbc9f2e9bdadae804901ff63bbf6ba7d98ce95e98ea37e9d3f5de1fc0fbefdf0714c0d75a6f05aad4c45f85aa4cc27dad1d9b1c817c93c96e8c60f62659d82bb"
        )

        # unpack the archive
        if not bootstrap_dir.exists():
            # bootstrap an arch system inside .cache folder
            os.mkdir(bootstrap_dir.parent)
            sudo(["tar", "-C", bootstrap_dir.parent, "--numeric-owner", "--xattrs", "--xattrs-include='*'", "-xpf", dest])

            # obtain pacman mirror list
            mirrorlist = reflector.get_mirrors(latest=10, sort="rate")
            print(mirrorlist)
            with open(cache_dir / "mirrorlist", 'w', encoding='utf-8') as handle:
                handle.write(mirrorlist)

            # move mirror list to the correct location
            sudo(["mv", cache_dir / "mirrorlist", bootstrap_dir / "etc" / "pacman.d"])
            sudo(["chown", "root:root", bootstrap_dir / "etc" / "pacman.d" / "mirrorlist"])

            # init pacman keyring and update packages
            sudo(["systemd-nspawn", "-qD", bootstrap_dir, "pacman-key", "--init"])
            sudo(["systemd-nspawn", "-qD", bootstrap_dir, "pacman-key", "--populate"])
            sudo(["systemd-nspawn", "-qD", bootstrap_dir, "pacman", "--sync", "--refresh", "--refresh", "--sysupgrade", "--sysupgrade", "--noconfirm"])

        # bind-mount image partitions into bootstrapped arch
        sudo(["mkdir", "--parents", bootstrap_dir / tmp.name])
        atexit.register(sudo, ["rmdir", bootstrap_dir / tmp.name])
        sudo(["mount", "--bind", chroot_fs, bootstrap_dir / tmp.name])
        atexit.register(sudo, ["umount", "--lazy", bootstrap_dir / tmp.name])

        # finally run pacstrap to init arch inside the image
        sudo(["systemd-nspawn", "-qD", bootstrap_dir, "pacstrap", "-c", tmp.name])

# install user-defined packages
def pacstrap_pkg(chroot_fs, packages, tmp):
    if distro.id() == "arch":
        sudo(["pacstrap", "-c", chroot_fs] + packages)
    else:
        bootstrap_dir = cache_dir / f"archlinux-bootstrap-{boot_version}" / "root.x86_64"
        sudo(["systemd-nspawn", "-qD", bootstrap_dir, "pacstrap", "-c", tmp.name] + packages)
    chroot(chroot_fs, ["pacman", "--sync", "--refresh", "--refresh", "--sysupgrade", "--sysupgrade", "--noconfirm"])
