Configuration data for creating a bootable iso image. Use the [Archiso](https://wiki.archlinux.org/title/Archiso) tool to convert this configuration into an iso file:

```
sudo pacman --sync archiso
git clone https://github.com/flying-dude/efly
cd efly
sudo mkarchiso -v iso
./scripts/efly-qemu out/efly-live-2022.05.08-x86_64.iso
```
