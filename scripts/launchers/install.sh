#!/bin/sh
# Python performs all platform-dependent work; this launcher also accepts old bash commands.
case "$0" in
  */*) im_writing_script_dir=${0%/*} ;;
  *) im_writing_script_dir=. ;;
esac
for im_writing_python in python3 python; do
  if command -v "$im_writing_python" >/dev/null 2>&1 &&
     "$im_writing_python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
    exec "$im_writing_python" "$im_writing_script_dir/install.py" "$@"
  fi
done
echo 'Python 3.10 or newer is required.' >&2
exit 1
