#!/bin/sh
# OFFLINE CANDIDATE ONLY: current Kata policy rejects shell exec. Do not broaden
# the policy to run this; use a reviewed built-in metadata interface instead.
# No arguments or path overrides.
# CAP enclava-init defaults: canonical marker contents are one line plus newline.
# Conservative: missing, noncanonical, symlink or unreadable markers are unknown/false.
set +x
exec 2>/dev/null
PATH=/usr/bin:/bin
export PATH
if [ "$#" -ne 0 ] || ! command -v cmp >/dev/null; then
    printf '%s\n' '{"phase":"unknown","ready":false}'
    exit 2
fi
phase_file=/run/enclava/init-stage
ready_file=/run/enclava/init-ready
phase=unknown
ready=false
if [ -f "$phase_file" ] && [ ! -L "$phase_file" ]; then
    while IFS='|' read -r marker label; do
        if printf '%s\n' "$marker" | cmp -s "$phase_file" -; then
            phase=$label
            break
        fi
    done <<'PHASES'
loading config|loading_config
validating signed config|validating_signed_config
waiting for owner seed|waiting_for_owner_seed
opening luks volumes|opening_luks_volumes
preparing mount ownership|preparing_mount_ownership
verifying trustee policy|verifying_trustee_policy
provisioning static tls certificate|provisioning_static_tls_certificate
writing component seeds|writing_component_seeds
waiting for workload containers|waiting_for_workload_containers
binding workload mount namespaces|binding_workload_mount_namespaces
seeding caddy runtime handoff|seeding_caddy_runtime_handoff
marking ready|marking_ready
PHASES
fi
if [ -f "$ready_file" ] && [ ! -L "$ready_file" ] &&
    printf 'ready\n' | cmp -s "$ready_file" -; then
    ready=true
fi
printf '{"phase":"%s","ready":%s}\n' "$phase" "$ready"
