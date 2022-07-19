# Custom Profiles

`efly` provides the possibility to create custom profiles based on which to create disk images.
If no profile is specified, it will use the
[default](https://github.com/flying-dude/efly/tree/main/data/img)
profile automatically.
You can create your own profile and invoke `efly` using it with the `--profile` flag:

```
efly img --profile path/to/myprofile
```

The above command will place the build data into a subdirectory `./out` relative to the current working directory, from which you invoked `efly`.

A profile currently consists of the following components:

* [`packages.txt`](https://github.com/flying-dude/efly/blob/main/data/img/packages.txt): The list of packages to install on the image.
* [`extra`](https://github.com/flying-dude/efly/blob/main/data/img/extra): A folder with extra data that will be copied to location */* of the root filesystem after installing the specified packages with
[`pacstrap`](https://man.archlinux.org/man/pacstrap.8). You can put your personal configuration and additional scripts into that folder.
* [`postinst`](https://github.com/flying-dude/efly/blob/main/data/img/postinst): A script that will be executed inside a chroot after copying the `extra` files. Use this script for some additional tweaking of our disk image.