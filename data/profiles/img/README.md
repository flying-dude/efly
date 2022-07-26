## Create a Bootable Raw Disk Image With Persistent Storage

```
sudo pacman --sync python-colorama dosfstools e2fsprogs squashfs-tools gptfdisk
git clone https://github.com/flying-dude/efly
cd efly/src/efly
./efly-img
ls out/efly-live.img # location of the image
```

## Increase Storage Capacity

The root partition `/` is an overlayfs with a read-only squashfs partition containing all the data of
the root partition and a read-write ext4 partition for making changes to the root partition.

The ext4 partition has initially a tiny size of 4MB but is programmed to grow to maximum available size at first
boot. This will probably be multiple GB depending on the size of your stick. If you want to boot the image
inside a virtual machine like qemu, you increase available size using the `truncate` command:

```
truncate --size=10G efly-live.img
```
