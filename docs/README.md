**[Profiles](profiles.md) - [Flash](flash.md)**

## Creating Bootable Disk Images

The `efly` live system ships with its own command-line tool for creating bootable disk images.

```
$ efly --help
Usage: efly [subcommand] [options]
       efly <subcommand> --help

Version: 0.0.15

Create and manage bootable disk images based on Arch Linux.

Subcommands:
  efly dd        :: Install efly on a given block device.
  efly qemu      :: Boot a disk image using qemu.
  efly vncserver :: Launch a VNC server using TigerVNC.
```

```
$ efly dd --help
Usage: efly dd [options] <block-device>

Version: 0.0.15

Put efly on a given specified block device or raw disk image.
The created system will have two partitions. One EFI boot partition and one
ext4 root partition. Default EFI size is 128M und root will use the remaining availabe
disk space. Root can be made smaller with option --root-size.

Note that this command will wipe all data on that block device before installing efly on it.

General Options:
  -h --help                  Show this screen.
  -v --version               Print version info.

  --profile <profile-dir>    Use a custom profile instead of default profile.

  --nocolor                  Deactivate colored output.
  --shell                    Launch an interactive shell after running the postinst script.
                             Useful for doing some manual tweaking or for debuggung.

Size Options:                Unit in M, G or T (KiB, MiB, GiB, TiB resp.) - Example: 128M
  --efi-size <size>          Set size of the EFI boot partition.
  --root-size <size>         Assign a size for the root partition, rather than to simply
                             use all remaining available storage for root partition.

Examples:
  Wipe block device sdx and install efly:
  $ efly dd /dev/sdx

  Create a raw disk image with efly installed on it:
  $ truncate --size=10G myimage.img
  $ efly dd myimage.img
  $ efly qemu myimage.img

  Use your own, custom profile:
  $ efly dd --profile path/to/myprofile /dev/sdx
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
