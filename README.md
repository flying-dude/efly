Create a graphical live medium suitable for installing Arch Linux or as a rescue system for computers without a working operating system.
How to [flash](docs/flash.md) a USB stick?

<p align="center">
<b><a href="https://github.com/flying-dude/efly/releases/download/latest/efly-live.iso">iso</a></b> | <b><a href="https://github.com/flying-dude/efly/releases/download/latest/efly-live.iso.b2sum">b2sum</a></b>
</p>

```
sudo pacman --sync archiso
git clone https://github.com/flying-dude/efly
cd efly
sudo mkarchiso -v iso
./scripts/efly-qemu out/efly-live-2022.05.08-x86_64.iso
```

![Efly Linux Live](screenshot.png)
