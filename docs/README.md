**[Profiles](profiles.md) - [Flash](flash.md)**

## Creating Bootable Disk Images

The `efly` live system ships with its own command-line tool for creating bootable disk images.

```
Usage: efly [subcommand] [options]
       efly <subcommand> --help

Version: 0.0.7

Create and manage bootable disk images based on Arch Linux.

Subcommands:
  efly dd        :: Install an efly system directly on a given block device.
  efly img       :: Create a read-write disk image with expanding root partition.
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
    efly qemu --uefi out/efly-live.rom # boot in UEFI mode using qemu
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

You can use `efly dd` to install a preconfigured Arch Linux system directly on a given block device (keep in mind that this will wipe all data on that block device):

```
efly dd /dev/sdX # wipe sdX and install efly
```

It doesn't have to be a block device. You can also target a raw disk image:

```
truncate --size=10G myimage.img
efly dd myimage.img
```

Installations created using `efly dd` have only two partitions: One EFI boot partition and one `ext4` root partition.

## Packaging

The created images are based on the Arch Linux operating system. You can install binary packages using [`pacman`](https://wiki.archlinux.org/title/Pacman).
In addition to packages provided by mainline Arch Linux repositories, the [`ymerge`](https://github.com/flying-dude/ymerge) package manager provides extra packages available for install.
These extra packages are compiled from source using [PKGBUILD](https://wiki.archlinux.org/title/PKGBUILD) package recipes.

## UUIDs and Multiple Efly Devices

Efly generates a
[random uuid](https://github.com/flying-dude/efly/blob/a3a28b554b04e83987c33f8e0820a4688a5a306f/src/efly/efly-img#L295)
for each partition, when it creates a disk image.
That means each created disk image has its own unique partition
[UUIDs](https://en.wikipedia.org/wiki/Universally_unique_identifier).

The purpose of this procedure is to avoid name clashes between multiple images.
However, there will still be name clashes when you put the *same* image on multiple devices, since these devices use the same UUIDs for their partitions.

If you want to place efly on multiple devices (let's say you have multiple USB sticks with efly installed on them), it is recommended to generate a different disk image for each stick. Something like this should work:

```
efly img --out stick1
efly img --out stick2
```

The disk images inside folders `stick1` and `stick2` will have the same software installed on them and use the same configuration, which means they are identical in a practical sense.
But the randomly-generated portions during image creation will be different, so that a checksum algorithm would produce different results for both images.

Randomly-generated portions includes at least the generated partition UUIDs and the
[pacman keyring](https://wiki.archlinux.org/title/Pacman/Package_signing#Initializing_the_keyring).
There are possibly other factors, that make the created disk images intentionally or unintentionally non-deterministic.
But these two are guaranteed to make `efly img` produce a uniquely-identifiable result on each run.

What exactly happens, when you place the same image on multiple USB sticks?
That has not been tested for UUIDs.
But in the case of identical partition labels, the kernel will happily boot from one device and use the root partition from another one.
So at least there is no runtime error in that case. :-)

## Links

* [USB flash installation medium](https://wiki.archlinux.org/title/USB_flash_installation_medium)