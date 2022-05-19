This folder contains configuration data used to create iso image for the efly live system. It uses the [Archiso](https://wiki.archlinux.org/title/Archiso) tool to convert this configuration into a bootable iso image:

```
sudo pacman -S archiso
git clone https://github.com/flying-dude/efly
cd efly
sudo mkarchiso -v iso
./run_archiso_efly out/efly-live-2022.05.08-x86_64.iso
```
