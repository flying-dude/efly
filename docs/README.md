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
