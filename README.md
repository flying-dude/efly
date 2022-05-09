Create a graphical live medium suitable for installing Arch Linux or as a rescue system for computers without a working operating system.

```
sudo pacman -S archiso
git clone https://github.com/flying-dude/efly
cd efly
sudo mkarchiso -v efly-live
run_archiso -i out/efly-linux-2022.05.08-x86_64.iso
```

![Efly Linux Live](screenshot.png)
