**[Install](https://github.com/flying-dude/efly/blob/main/docs/README.md#install-efly-command-using-pkgbuild) -
[Docs](docs/README.md) - [Packages](https://github.com/flying-dude/curated-aur)**

A graphical live system based on Arch Linux.
Installs a Linux system either on a given block device or on a raw disk image.
The disk images can be booted with qemu.

```
# minimum python 3.11 required
python3 --version

# arch linux / manjaro
sudo pacman -S dosfstools e2fsprogs gptfdisk sudo arch-install-scripts

# debian / ubuntu
sudo apt install python3-tqdm python3-platformdirs

# fedora
sudo dnf install python3-tqdm python3-platformdirs

git clone https://github.com/flying-dude/efly
./efly/efly/efly dd --help
./efly/efly/efly dd efly-live.img
```

![Efly Linux Live](data/screenshot.png)
