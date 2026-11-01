# Optional custom-release updates. No device operations and no upstream fallback.
kit_update_check() {
    [[ $no_version_check != 1 ]] || return 0
    [[ -s ../resources/update-repository ]] || return 0
    local updater_python root result
    updater_python="$(command -v python3)"
    if [[ -z $updater_python ]] || ! "$updater_python" -c 'import sys; sys.exit(sys.version_info < (3, 7))'; then
        warn "Automatic update checks require Python 3.7 or newer. Continuing with this version."
        return 0
    fi
    root="$(cd .. && pwd)" || return 0
    log "Checking this fork's GitHub releases for updates..."
    "$updater_python" ../resources/updater/update.py check --root "$root" --plan "$PWD/custom-update.json"
    result=$?
    case "$result" in
        0) return 0;;
        2) ;;
        *)
            warn "The update check could not finish. Continuing with this version."
            print "* No functionality is disabled. Online features will still try to connect."
            return 0;;
    esac
    print "* Updates are optional. Choosing No keeps all functionality available."
    print "* If an internet-dependent feature fails, an update may include a fix for service changes."
    select_yesno "Install this update now?" 1
    if [[ $? != 1 ]]; then
        log "Update declined. Continuing with this version."
        print "* No functionality is disabled. Offline operations remain accessible; online operations still require a connection."
        print "* If an online feature fails, relaunch and accept an available update."
        return 0
    fi
    if "$updater_python" ../resources/updater/update.py install --root "$root" --plan "$PWD/custom-update.json"; then
        log "Update complete. Please run the script again to use the new version."
        return 2
    fi
    warn "The update was not installed. Continuing with the existing version."
    return 0
}
