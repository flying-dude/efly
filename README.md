**[Install](https://github.com/flying-dude/efly/blob/main/docs/README.md#install-efly-command-using-pkgbuild) -
[Docs](docs/README.md) - [Packages](https://github.com/flying-dude/curated-aur)**

A graphical live system based on Arch Linux.
Installs a Linux system either on a given block device or on a raw disk image.
The disk images can be booted with qemu.

```
wget https://raw.githubusercontent.com/flying-dude/curated-aur/main/pkg/efly/PKGBUILD
makepkg --syncdeps --install
efly --help
```

Usage on Linux distributions other than Arch Linux.

```
# minimum python 3.11 required
python3 --version

# debian / ubuntu
sudo apt install python3-tqdm python3-platformdirs

# fedora
sudo dnf install python3-tqdm python3-platformdirs

git clone https://github.com/flying-dude/efly
./efly/efly/efly dd efly-live.img
```

![Efly Linux Live](data/screenshot.png)
