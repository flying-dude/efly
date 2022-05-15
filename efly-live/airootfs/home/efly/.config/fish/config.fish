# Start X at login
if status is-login
    if test -z "$DISPLAY" -a "$XDG_VTNR" = 1
        echo (printf "fish: starting X server. standard error is written to: %s~/.cache/STARTX_ERROR_LOG.txt%s" (set_color cyan) (set_color normal))

        # https://wiki.archlinux.org/title/Xorg#Session_log_redirection
        mkdir --parents ~/.cache
        startx -- -keeptty 2> ~/.cache/STARTX_ERROR_LOG.txt

        # note: the output below is glitched when X server is hard-killed (or presumably otherwise crashes).
        # send SIGKILL to the X server to trigger the glitched behaviour: "killall -9 Xorg"

        echo
        echo the X server has terminated.
        echo (printf "standard error was written to: %s~/.cache/STARTX_ERROR_LOG.txt%s" (set_color cyan) (set_color normal))
        echo (printf "type %sstartx%s to start the X server again." (set_color brgreen) (set_color normal))
        echo

        echo (printf "use %slocalectl list-keymaps%s to list available keymaps" (set_color brgreen) (set_color normal))
        echo (printf "use %ssudo localectl set-keymap <keymap>%s to change keymap" (set_color brgreen) (set_color normal))
        echo
    end
end
