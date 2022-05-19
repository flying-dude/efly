Create a graphical live medium suitable for installing Arch Linux or as a rescue system for computers without a working operating system.

<p align="center">
<b><a href="https://github.com/flying-dude/efly/releases/download/latest/efly-live.iso">iso</a></b> | <b><a href="https://github.com/flying-dude/efly/releases/download/latest/efly-live.iso.b2sum">b2sum</a></b>
</p>

```
sudo pacman -S archiso
git clone https://github.com/flying-dude/efly
cd efly
sudo mkarchiso -v iso
./run_archiso_efly out/efly-live-2022.05.08-x86_64.iso
```

![Efly Linux Live](screenshot.png)
