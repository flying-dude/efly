# modified fish prompt adapted from the default prompt function: https://github.com/fish-shell/fish-shell/blob/master/share/functions/fish_prompt.fish
function fish_prompt --description 'Write out the prompt, efly style.'
    set -l last_pipestatus $pipestatus
    set -lx __fish_last_status $status # Export for __fish_print_pipestatus.
    set -l normal (set_color normal)
    set -q fish_color_status
    or set -g fish_color_status --background=red white

    # suffix is '$' for non-root and '#' for root.
    set -l suffix '$'
    if functions -q fish_is_root_user; and fish_is_root_user
        set suffix '#'
    end

    # Write pipestatus
    # If the status was carried over (if no command is issued or if `set` leaves the status untouched), don't bold it.
    set -l bold_flag --bold
    set -q __fish_prompt_status_generation; or set -g __fish_prompt_status_generation $status_generation
    if test $__fish_prompt_status_generation = $status_generation
        set bold_flag
    end
    set __fish_prompt_status_generation $status_generation
    set -l status_color (set_color $fish_color_status)
    set -l statusb_color (set_color $bold_flag $fish_color_status)
    set -l prompt_status (__fish_print_pipestatus "[" "] " "|" "$status_color" "$statusb_color" $last_pipestatus)

    ### output starts here

    echo -n [

    # uncomment this if you want to print the time. will only print termination time of previous command, tho.
    # echo -n -s (date +"%H:%M") ' '

    # print the user name, with the color different depending on permission level.
    if functions -q fish_is_root_user; and fish_is_root_user
        set_color brred # user root is red
    else if groups | grep wheel > /dev/null
        set_color brmagenta # users in group wheel are magenta
    else
        set_color brcyan # all other users are printed in cyan
    end
    echo -n -s $USER $normal '@' $hostname '] '

    # print name of current directory.
    set_color $fish_color_cwd
    if [ (pwd) = ~ ]
        echo -n '~' # abbreviate home dir as tilde.
    else if [ (pwd) = '/' ]
        echo -n '/' # file system root
    else
        # only printing basename. not the full path.
        echo -n -s (basename (pwd)) '/'
    end
    echo -n $normal

    echo -n -s (fish_vcs_prompt) $normal
    echo -n -s ' ' $prompt_status
    echo -n -s (set_color bryellow) $suffix ' '

    ### output ends here

    # for reference: this is how the default prompt is generated
    # echo -n -s (prompt_login)' ' (set_color $color_cwd) (prompt_pwd) $normal (fish_vcs_prompt) $normal " "$prompt_status $suffix " "
end
