# How to Flash a USB Stick?

One way to turn a USB stick into a bootable device is to place a suitable [disk image](https://en.wikipedia.org/wiki/Disk_image) on the stick.

But it is not sufficient to just *copy* a disk image to the file system of the stick. The disk image has its own partition table, file systems and boot facilities. Therefore, it needs to overwrite the data on the stick at [block device](https://unix.stackexchange.com/questions/259193/what-is-a-block-device) level.

The image needs to be copied *verbatim* to the stick; starting the very first byte (or bit) of the USB stick. This facilitates for the hardware firmware ([UEFI](https://en.wikipedia.org/wiki/Unified_Extensible_Firmware_Interface) or [BIOS](https://en.wikipedia.org/wiki/BIOS)) to correctly interact with the boot code placed on the disk image.

This section describes ways how to interact with block devices directly, so that we can properly install disk images on them.

## Using the Linux Command Line
*(Note: This may work on other Unix platforms too, like macOS or FreeBSD.)*

On Linux, you first identify the correct device name of your USB stick.
And then write the image to the corresponding [device node](https://en.wikipedia.org/wiki/Device_file).
You would typically determine the device name with the following workflow:

1) List the available block devices *before* plugging in your USB stick.
2) Plug in your USB stick and list the available block devices again. The newly listed device is the USB stick you have just plugged in.

The **`lsblk`** command from the **`util-linux`** package is very useful for this task.
However, the "old-school" way of doing this relies only on the **`ls`** command.
Here we simply list all devices starting with the **`sd`**-prefix
[[1](https://superuser.com/questions/558156/what-does-dev-sda-in-linux-mean), [2](https://man7.org/linux/man-pages/man4/sd.4.html)]:

```
$ ls /dev/sd*
/dev/sda  /dev/sda1  /dev/sda2  /dev/sda3  /dev/sdb
```

Now we plug in the USB stick and use **`ls`** again, to list the available block devices:

```
$ ls /dev/sd*
/dev/sda  /dev/sda1  /dev/sda2  /dev/sda3  /dev/sdb /dev/sdc /dev/sdc1 /dev/sdc2
```

The USB stick we have just plugged in carries the device name **`sdc`**. The entries **`sdc1`** and **`sdc2`** are partitions, which we are going to overwrite (the iso image has its own partitioning).

Next we are going to write the iso image to the stick. This will erase all data currently on the stick:

```
$ sudo cp efly-live.iso /dev/sdc
$ sync # wait for I/O to finish
```

The **`cp`** command will terminate before the data is fully written to the stick.
Run **`sync`** afterwards to see when the writes are finished.

```
$ man sync
sync - Synchronize cached writes to persistent storage
```

## Links

* Graphical Tools for Flashing USB Sticks:
  * balenaEtcher: https://www.balena.io/etcher/
     * [\[Wikipedia\]](https://en.wikipedia.org/wiki/Etcher_\(software\))
  * Ubuntu Startup Disk Creator: https://ubuntu.com/tutorials/create-a-usb-stick-on-ubuntu
     * [\[Wikipedia\]](https://en.wikipedia.org/wiki/Startup_Disk_Creator) ---
  [\[AUR\]](https://aur.archlinux.org/packages/usb-creator)
  * Fedora Media Writer: https://github.com/FedoraQt/MediaWriter
     * [\[Wikipedia\]](https://en.wikipedia.org/wiki/Fedora_Media_Writer) ---
  [\[AUR\]](https://aur.archlinux.org/packages/mediawriter)
