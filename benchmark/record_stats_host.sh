#!/bin/bash
set -euo pipefail
trap cleanup SIGINT SIGTERM

########################################
# Configuration
########################################
PIDFILE=/tmp/record_stats_host.pid
PGID=$(ps -o pgid= -p $$ | tr -d ' ')

echo "$PGID" > $PIDFILE
cleanup() {
    # 再入防止（trap が再度走らないように）
    trap - INT TERM

    # グループ全体に送る（自分 + dool を同時終了）
    kill -TERM -"$PGID" 2>/dev/null || true

    rm -f "$PIDFILE"
    exit 0
}

########################################
# Variables
########################################
INTERVAL="${INTERVAL:-5}"

########################################
# Arguments
########################################
OUTPUT=$1

########################################
# Varidation
########################################

########################################
# Main
########################################
dool --cpu --mem --net --disk --nocolor --noheaders --ascii --output=$OUTPUT $INTERVAL &

wait
