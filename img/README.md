Create a bootable raw disk image with persistent storage (read further below on how to increase storage capacity):

```
sudo pacman --sync mkosi
git clone https://github.com/flying-dude/efly
cd efly
./scripts/efly-img
./scripts/efly-qemu --uefi img/efly-live.img
```

# Increase Storage Capacity

The root partition `/` is an overlayfs with a read-only squashfs partition containing all the data of
the root partition and a read-write ext4 partition for making changes to the root partition.

The ext4 partition has initially a tiny size of 4MB but is programmed to grow to maximum available size at first
boot. This will probably be multiple GB depending on the size of your stick. If you want to boot the image
inside a virtual machine like qemu, you increase available size using the `truncate` command:

```
$ truncate --size=10G efly-live.img
```
