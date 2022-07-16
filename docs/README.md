## Creating Bootable Disk Images

The efly live system ships with its own command-line tool for creating bootable disk images.
These images have persistent storage and will auto-expand the file system to full storage capacity on first boot, if you place them on a USB stick (on slow sticks this can take a few minutes).

```
$ efly img --help
Usage: efly img [options]

Create raw disk images for live systems bootable from a USB flash drive.
The live system has persistent storage and will retain changes among reboots.

General Options:
  -h --help                  Show this screen.
  --out <out-dir>            Choose output directory instead of out/ inside current working directory.
  --profile <profile-dir>    Use a custom profile instead of default profile.

  --shell                    Launch an interactive shell after running the postinst script.
                             Useful for doing some manual tweaking or for debuggung.

Size Options:                Unit in M, G or T (KiB, MiB, GiB, TiB resp.) - Example: 128M
  --efi-size <size>          Set size of the EFI boot partition.
  --overlay-size <size>      Set initial size of overlay partition. Will still auto-expand on first boot.
```

## Install the Disk Image Tool

To obtain the efly command-line tool, you can use the available [PKGBUILD](https://github.com/flying-dude/curated-aur/blob/main/pkg/efly/PKGBUILD):

```
wget https://raw.githubusercontent.com/flying-dude/curated-aur/main/pkg/efly/PKGBUILD
makepkg --syncdeps --install
efly --help
```

Alternatively, you can simply clone the git repository:

```
sudo pacman --sync python-colorama dosfstools e2fsprogs squashfs-tools gptfdisk
git clone https://github.com/flying-dude/efly
cd efly/src/efly
./efly --help
```

## Packaging

The created images use the Arch Linux operating system. You can install binary packages using the [`pacman`](https://wiki.archlinux.org/title/Pacman) tool. In addition to packages provided by mainline Arch Linux repositories, the [`ymerge`](https://github.com/flying-dude/ymerge) package manager provides extra packages available for install. These extra packages are compiled from source using [PKGBUILD](https://wiki.archlinux.org/title/PKGBUILD) package recipes.

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