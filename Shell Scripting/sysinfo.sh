#!/usr/bin/env bash
#
# sysinfo.sh - print a short system summary, then dump the full process
# list to a file the user names.
#
# Practises: variables, command substitution, read prompts, mkdir/touch,
# and output redirection with >.

# -e  stop on the first failing command
# -u  treat an unset variable as an error instead of an empty string
# -o pipefail  a pipeline fails if any stage in it fails, not just the last
set -euo pipefail

# Width the on-screen process table is trimmed to so it fits a normal
# terminal. Kept in one place instead of repeated at each cut call.
readonly TABLE_WIDTH=110

# Defaults used when the user just presses Enter at a prompt.
readonly DEFAULT_DIR="reports"
readonly DEFAULT_FILE="processes.txt"

# heading <text> - print a section heading with a blank line above it.
heading() {
    printf '\n--- %s ---\n' "$1"
}

# Every value is captured once up front with $(...) command substitution, so
# the summary is a snapshot of a single moment rather than of several.
run_date=$(date)
host_name=$(hostname)
user_name=$(whoami)
# awk NR==2 skips the df header row and keeps the percentage and total size.
root_usage=$(df -h / | awk 'NR==2 {print $5 " used of " $2}')
# wc counts the ps header line too, so subtract 1 for the real process count.
process_total=$(($(ps aux | wc -l) - 1))

printf '=== System summary ===\n'
# printf reuses its format string until the arguments run out, so one call
# lays out every row. %-12s pads each label to a fixed width, which keeps the
# colons aligned without padding the labels by hand.
printf '%-12s: %s\n' \
    "Date" "$run_date" \
    "Host" "$host_name" \
    "User" "$user_name" \
    "Root disk" "$root_usage" \
    "Processes" "$process_total running"

heading "Disk usage (df -h)"
df -h

heading "Top 10 processes by CPU"
# The header row is printed on its own. Piping all of ps into sort would sort
# the header along with the data and bury it in the middle of the table.
ps aux | head -n 1 | cut -c1-"$TABLE_WIDTH" || true
# Column 3 of ps aux is %CPU, so -k 3 sorts on it and -r makes that descending.
# tail -n +2 drops the header first. head closes the pipe early, so sort takes
# a SIGPIPE that pipefail would otherwise treat as a failure; || true keeps
# set -e from killing the run.
ps aux | tail -n +2 | sort -rk 3 | head -n 10 | cut -c1-"$TABLE_WIDTH" || true

# read -p writes the prompt without a trailing newline; -r keeps backslashes
# in the answer literal rather than treating them as escapes.
echo
read -r -p "Directory to save the report in: " report_dir
read -r -p "Report file name: " report_file

# Empty input would leave the path as a bare "/", so fall back to the
# defaults instead of failing further down.
: "${report_dir:=$DEFAULT_DIR}"
: "${report_file:=$DEFAULT_FILE}"

report_path="$report_dir/$report_file"

# -p creates parent directories as needed and stays quiet if they exist,
# which lets the script be re-run without error.
mkdir -p "$report_dir"
# touch creates the file up front, so the path exists before anything is
# written to it.
touch "$report_path"

# > truncates and writes; swap it for >> to append to an existing report.
ps aux > "$report_path"

saved_lines=$(wc -l < "$report_path" | tr -d ' ')
printf '\nSaved %s lines of process data to %s\n' "$saved_lines" "$report_path"
