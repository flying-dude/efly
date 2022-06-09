Create a bootable raw disk image with persistent storage (read further below on how to increase storage capacity):

```
sudo pacman --sync python-docopt dosfstools e2fsprogs squashfs-tools gptfdisk
git clone https://github.com/flying-dude/efly
cd efly
./scripts/efly-img
ls img/out/efly-live.iso # location of the image
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
