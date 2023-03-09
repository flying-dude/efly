**[Profiles](profiles.md) - [Flash](flash.md)**

## Creating Bootable Disk Images

The `efly` live system ships with its own command-line tool for creating bootable disk images.

```
Usage: efly [subcommand] [options]
       efly <subcommand> --help

Version: 0.0.7

Create and manage bootable disk images based on Arch Linux.

Subcommands:
  efly dd        :: Create an efly system directly on a given block device.
  efly rom       :: Create a read-only disk image.

  efly qemu      :: Boot a disk image using qemu.
  efly vncserver :: Launch a VNC server using TigerVNC.
```

```
$ efly rom --help
Usage: efly rom [options]

Create a read-only, bootable raw disk image. File system changes are written to a temporary file system
in RAM, when booting the system. Data will reset to a clean state, when rebooting (changes made are then lost).

Currently requires a UEFI system for booting. Hybrid boot including BIOS is planned.

General Options:
  -h --help                  Show this screen.
  -v --version               Print version info.

  --out <out-dir>            Choose output directory instead of out/ inside current working directory.
  --profile <profile-dir>    Use a custom profile instead of default profile.

  --nocolor                  Deactivate colored output.
  --shell                    Launch an interactive shell after running the postinst script.
                             Useful for doing some manual tweaking or for debuggung.

Example:
    efly rom # create a bootable disk image in folder ./out
    efly qemu out/efly-live.rom # boot using qemu
```

## Install `efly` Command Using PKGBUILD

To obtain the `efly` command-line tool, you can use the available [PKGBUILD](https://github.com/flying-dude/curated-aur/blob/main/pkg/efly/PKGBUILD):

```
wget https://raw.githubusercontent.com/flying-dude/curated-aur/main/pkg/efly/PKGBUILD
makepkg --syncdeps --install
efly --help
```

## Clone `git` Repository to Obtain the `efly` Command 

Alternatively, you can simply clone the git repository:

```
sudo pacman --sync python-colorama dosfstools e2fsprogs squashfs-tools gptfdisk
git clone https://github.com/flying-dude/efly
cd efly/src/efly
./efly --help
```

## Set up an Efly System on a Block Devick

You can use `efly dd` to set up efly directly on a given block device (keep in mind that this will wipe all data on that block device):

```
efly dd /dev/sdX # wipe sdX and install efly
```

It doesn't have to be a block device. You can also target a raw disk image:

```
truncate --size=10G myimage.img
efly dd myimage.img
efly qemu myimage.img
```

## Links

* [USB flash installation medium](https://wiki.archlinux.org/title/USB_flash_installation_medium)
