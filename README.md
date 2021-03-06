**[Docs](docs/README.md) - [Packages](https://github.com/flying-dude/curated-aur)**

A graphical live system based on Arch Linux.
Suitable for installing Arch Linux or as a rescue system for computers without a working operating system.
How to [flash](docs/flash.md) a USB stick?

The image in [iso format](https://en.wikipedia.org/wiki/Optical_disc_image) has a volatile root file system, which deletes all changes on reboot.
The second option is a [raw disk image](https://en.wikipedia.org/wiki/IMG_(file_format)) with persistent storage.
It will retain changes among reboots.

<p align="center">
<b><a href="https://github.com/flying-dude/efly/releases/download/latest/efly-live.iso">iso</a></b> | <b><a href="https://github.com/flying-dude/efly/releases/download/lat
est/efly-live.img">img</a></b>
</p>

```
wget https://raw.githubusercontent.com/flying-dude/curated-aur/main/pkg/efly/PKGBUILD
makepkg --syncdeps --install
efly img --overlay-size 10G # create a bootable disk image
efly qemu --uefi out/efly-live.img
```

![Efly Linux Live](data/screenshot.png)
