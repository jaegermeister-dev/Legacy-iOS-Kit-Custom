# Optional host transcript. Source before platform checks or device operations.
kit_diagnostics_start() {
    local answer folder
    kit_diagnostics_enabled=0
    print " *** Legacy iOS Kit (Custom) ***"
    input "Enable diagnostic logging for troubleshooting and bug reports?"
    print "* Saves Terminal output locally. Nothing is uploaded automatically."
    print "* Logs may contain device identifiers and local paths; review before sharing."
    print "* Restore records needed for image reuse and failure diagnosis are saved regardless."
    # A plain read keeps this first prompt usable before terminal/device setup.
    while true; do
        printf '%s[Input] Enable diagnostics? (y/N): %s' "$color_Y" "$color_N"
        IFS= read -r answer || answer=n
        case "$answer" in
            y|Y) kit_diagnostics_enabled=1; break;;
            n|N|'') log "Optional diagnostic logging disabled."; return 0;;
        esac
    done
    folder="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/saved/diagnostics"
    if ! (umask 077; mkdir -p "$folder"); then
        kit_diagnostics_enabled=0
        warn "Cannot create the diagnostic log folder. Continuing without optional logging."
        return 0
    fi
    kit_diagnostics_log="$(umask 077; mktemp "$folder/session-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")" || {
        kit_diagnostics_enabled=0
        warn "Cannot create a diagnostic log. Continuing without optional logging."
        return 0
    }
    # Keep stdin attached to the user's terminal. Do not record keystrokes.
    [[ ! -t 1 ]] || export LIK_DIAGNOSTICS_TTY=1
    if ! (umask 077; mkfifo "$kit_diagnostics_log.pipe"); then
        kit_diagnostics_enabled=0
        warn "Cannot start diagnostic capture. Continuing without optional logging."
        return 0
    fi
    exec 7>&1 8>&2
    (trap '' INT TERM; exec tee -ia "$kit_diagnostics_log" < "$kit_diagnostics_log.pipe" >&7) &
    kit_diagnostics_pid=$!
    exec > "$kit_diagnostics_log.pipe" 2>&1
    rm -f "$kit_diagnostics_log.pipe"
    log "Diagnostic logging enabled: $kit_diagnostics_log"
    print "* Nothing is uploaded automatically. Include this log when reporting an issue."
}

kit_diagnostics_finish() {
    [[ $kit_diagnostics_enabled == 1 && -n $kit_diagnostics_pid ]] || return 0
    print "* Diagnostic log: $kit_diagnostics_log"
    exec 1>&7 2>&8 7>&- 8>&-
    # Normal cleanup has already stopped the Kit's background services. Bound
    # the drain wait in case a surviving external process still holds stdout.
    local count=0 result
    while kill -0 "$kit_diagnostics_pid" 2>/dev/null && [[ $count -lt 30 ]]; do
        sleep 0.1
        count=$((count + 1))
    done
    if kill -0 "$kit_diagnostics_pid" 2>/dev/null; then
        kill -KILL "$kit_diagnostics_pid" 2>/dev/null
        warn "Diagnostic capture did not close normally; its final lines may be incomplete."
    fi
    wait "$kit_diagnostics_pid"
    result=$?
    [[ $result == 0 ]] || warn "Diagnostic capture stopped with an error; review the saved log."
    kit_diagnostics_pid=
    return 0
}

kit_exit() {
    local result=$?
    "$1"
    kit_diagnostics_finish
    return "$result"
}
