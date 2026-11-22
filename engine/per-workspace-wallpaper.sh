#!/bin/bash
# per-workspace-wallpaper.sh — a different wallpaper on each named workspace.
#
# ⚠️ REBUILT FOR QUATTRO, 2026-08-09. The original (T78/T83) drove **swaybg** directly — `pkill` +
# relaunch with `-c #RRGGBB` or `-i <path>` — and rewrote the per-workspace waybar tint on the way.
# Quattro retired swaybg AND waybar, so both halves of that script died at once. `git show
# 3ebc40c9:omarchy/workspace-backgrounds/per-workspace-wallpaper.sh` is the old one.
#
# The replacement is better, not just different: Quickshell owns the background and exposes it over
# IPC (`omarchy-shell background set|setInstant|transition|refresh`), so there is no process to kill,
# no flicker, and a real cross-fade available for free.
#
# ⚠️ IT PICKS FROM THE CURRENT THEME BY DEFAULT, AND THAT IS THE POINT. Omarchy themes ship several
# backgrounds; workspace N takes the Nth of them. Change theme and all six follow, with no
# per-workspace config to re-point — which is exactly what broke repeatedly on the old one, where a
# theme change or an `omarchy update` silently reset the named workspaces back to the theme image.
#
# To pin a specific image to a workspace, drop a file next to this script named `ws<N>.<ext>`
# (e.g. `ws4.png`). That is the strongest of the three rules — nothing else can override it.
#
# To fill every workspace that has NO image of its own, drop `all.<ext>` next to this script. It
# stands in for the theme's list, not for the per-workspace files. ⚰️ The plain-black `all.png`
# that sat here from 2026-08-10 was retired on 2026-09-01 (Dave: "move away from the universal
# all.png") — nothing installs one any more; the rule stays for a hand-dropped file.
#
# ⚠️ THE ORDER OF THOSE TWO WAS THE OTHER WAY ROUND UNTIL 2026-08-11, and it read as a broken
# feature: Dave dropped `ws3.png` in and nothing happened, because `all.png` was still winning. A
# blanket image is a mood he sets once; a per-workspace image is a deliberate choice about one
# desk, so the deliberate one has to win or adding a picture looks like it did not work.

set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/omarchy/current"
# `set` cross-fades, `setInstant` swaps immediately. Instant is the default because a fade on every
# workspace switch reads as lag when you are moving between them quickly.
METHOD="${WALLPAPER_METHOD:-setInstant}"

# Headless-safe: launched outside a graphical Hyprland session (self-heal, a systemd start before the
# session is fully up), derive the runtime env the socket path needs — otherwise the bare
# ${HYPRLAND_INSTANCE_SIGNATURE} expansion crashes under `set -u`.
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
if [ -z "${WAYLAND_DISPLAY:-}" ]; then
  for sock in "$XDG_RUNTIME_DIR"/wayland-*; do
    [ -S "$sock" ] && export WAYLAND_DISPLAY="$(basename "$sock")" && break
  done
fi
[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ] || \
  export HYPRLAND_INSTANCE_SIGNATURE="$(ls -t "$XDG_RUNTIME_DIR/hypr" 2>/dev/null | head -1)"

# The theme's backgrounds, sorted — Omarchy names them `0-…`, `1-…`, so sort order IS the intended
# order. Re-read on every lookup rather than cached at start: a theme change must take effect without
# restarting the watcher. WebP since Omarchy 4.5, which converted nearly every bundled image to it.
theme_backgrounds() {
  # Two folders, merged and sorted, exactly the list `omarchy theme bg next` cycles:
  # the user's own additions for this theme (~/.config/omarchy/backgrounds/<name> —
  # `omarchy theme bg install` opens it, Barbarian's + chip does too), then the theme's
  # shipped images.
  local dir user
  dir="$(readlink -f "$STATE/theme" 2>/dev/null)/backgrounds"
  user="$HOME/.config/omarchy/backgrounds/$(cat "$STATE/theme.name" 2>/dev/null)"
  find -L "$user" "$dir" -maxdepth 1 -type f \
    \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' \) 2>/dev/null | sort
}

# ⚠️ OMARCHY 4.5 BROKE OLD PINS, AND THIS REPAIRS THEM (14 Nov 2026). Two changes upstream did it:
# nearly every bundled image was renamed (most to .webp, some themes lost theirs outright), and
# current/theme stopped being a symlink to the shipped theme and became a generated directory. A
# pin made before that points through that directory, so it either dangles, or — worse — silently
# resolves into whatever theme is CURRENT now, showing the wrong theme's picture. At startup and
# on every one-shot apply, each pin is re-resolved against its OWN theme: Dave's additions for
# that theme first (the engine's own list puts them first), then the shipped folder. The
# generated directory is deliberately NOT a base: it is rewritten on every theme change, so a
# pin into it is never stable, and an image found only there is treated as gone. Found under a
# new extension: the pin is repointed and keeps working. Found nowhere: the image has left the
# machine, the pin is dropped with a line in repair-log, and the desk falls back down the chain
# (all.<ext>, then Auto) — a pin to nothing was never showing anyway. The same carries a
# hidden-images entry across a rename, or the hidden image would come back from the dead the
# first time the theme listed its new name.
repair_pin() { # <pin file> <theme name>
  local pin="$1" theme="$2" target stem found base ext
  target="$(readlink "$pin")"
  if [ -e "$pin" ]; then
    case "$target" in "$STATE"/theme/*) ;; *) return 0 ;; esac
  fi
  stem="${target##*/}"; stem="${stem%.*}"
  found=""
  for base in "$HOME/.config/omarchy/backgrounds/$theme" \
              "${OMARCHY_THEMES_DIR:-/usr/share/omarchy/themes}/$theme/backgrounds"; do
    for ext in webp jpg jpeg png; do
      if [ -f "$base/$stem.$ext" ]; then found="$base/$stem.$ext"; break 2; fi
    done
  done
  # 4.5 also RENUMBERED some themes ("0-winding-road" became "1-winding-road" when Liftoff
  # took the lead), and an exact stem cannot see that. Fall back to the name with its leading
  # number stripped — the same move Omarchy's own migration makes for its selection — so a pin
  # follows its picture to the new number instead of being dropped for a renumbering.
  if [ -z "$found" ] && [[ "$stem" == [0-9]*-* ]]; then
    local slug="${stem#*-}" cand
    for base in "$HOME/.config/omarchy/backgrounds/$theme" \
                "${OMARCHY_THEMES_DIR:-/usr/share/omarchy/themes}/$theme/backgrounds"; do
      for cand in "$base"/*-"$slug".*; do
        if [ -f "$cand" ]; then found="$cand"; break 2; fi
      done
    done
  fi
  if [ -n "$found" ]; then
    [ "$found" = "$target" ] && return 0
    rm -f "$pin"
    ln -sfn "$found" "${pin%.*}.${found##*.}"
  else
    rm -f "$pin"
    printf '%s %s dropped %s -> %s (the image is gone from the theme)\n' \
      "$(date '+%F %T')" "$theme" "${pin##*/}" "$target" >> "$HERE/repair-log"
  fi
}

repair_pins() {
  local theme_dir theme pin name replaced found stem ext base
  for theme_dir in "$HERE"/*/; do
    [ -d "$theme_dir" ] || continue
    theme="${theme_dir%/}"; theme="${theme##*/}"
    [ "$theme" = "solids" ] && continue
    for pin in "$theme_dir"ws*.* "$theme_dir"all.*; do
      [ -L "$pin" ] || continue
      repair_pin "$pin" "$theme"
    done
    if [ -f "$theme_dir/hidden-images" ]; then
      replaced=""
      while IFS= read -r name || [ -n "$name" ]; do
        [ -n "$name" ] || continue
        stem="${name%.*}"
        found=""
        for base in "$HOME/.config/omarchy/backgrounds/$theme" \
                    "${OMARCHY_THEMES_DIR:-/usr/share/omarchy/themes}/$theme/backgrounds"; do
          for ext in webp jpg jpeg png; do
            if [ -f "$base/$stem.$ext" ] && [ ! -f "$base/$name" ]; then
              found="$stem.$ext"; break 2
            fi
          done
        done
        replaced+="${found:-$name}"$'\n'
      done < "$theme_dir/hidden-images"
      printf '%s' "$replaced" > "$theme_dir/hidden-images"
    fi
  done
  # A universal hand-dropped blanket (all.<ext> at the top level) is repaired against the
  # current theme, the one whose images it stands in for.
  for pin in "$HERE"/all.*; do
    [ -L "$pin" ] || continue
    repair_pin "$pin" "$(cat "$STATE/theme.name" 2>/dev/null)"
  done
}

# Which image workspace N should show. An explicit ws<N>.<ext> beats everything; failing that
# `all.<ext>` covers whatever is left; otherwise index into the theme's list, wrapping if the theme
# ships fewer images than there are workspaces.
wallpaper_for() {
  local ws="$1" override theme
  # PINS ARE PER-THEME since 2026-09-01 (Dave: a theme change should bring back the set
  # you built under that theme, or start everything at Auto): a pin lives in a folder
  # named after the theme it was picked under, so switching themes switches sets for
  # free. The theme-set.d/workspace-background hook repaints the desk you are on the
  # moment the theme changes.
  theme="$(cat "$STATE/theme.name" 2>/dev/null)"
  # A picture chosen for ONE desk is the most deliberate thing anyone can say here, so it wins.
  # ⚠️ The name must be exactly `ws<N>.<ext>` — `ws2-blue.png` does NOT match `ws2.*`. Two files
  # named that way sat in the folder doing nothing from June until Dave deleted them on 11 Aug.
  if [ -n "$theme" ]; then
    for override in "$HERE/$theme/ws$ws".*; do
      [ -f "$override" ] && { printf '%s' "$override"; return 0; }
    done
  fi
  # ⚠️ ONE FILE FILLS EVERY REMAINING WORKSPACE, and that is the point. "The rest all the same" is a
  # thing David asks for as a mood rather than a setting, so it has to be one file to add and one
  # file to delete — not an edit here, which would be a change he cannot make or undo himself.
  # A theme-scoped blanket beats the universal one.
  for override in "$HERE/$theme"/all.* "$HERE"/all.*; do
    [ -f "$override" ] && { printf '%s' "$override"; return 0; }
  done

  local -a list
  mapfile -t list < <(theme_backgrounds)
  [ "${#list[@]}" -gt 0 ] || return 0
  local image dir pick i
  image="$(auto_image "$ws")"
  # ⚠️ A HIDDEN IMAGE HANDS ITS DESK ON TO THE NEXT ONE, AND NO OTHER DESK MOVES. Barbarian's × on
  # one of the theme's own images (2026-09-25) names it in `<theme>/hidden-images` rather than
  # deleting it. Taking it out of the list would renumber everything after it, so hiding image 1
  # would change every Auto desk at once; counting against the whole list and skipping forward
  # past hidden ones changes only the desk that was showing it.
  dir="$(readlink -f "$STATE/theme" 2>/dev/null)/backgrounds"
  for (( i = 0; i < ${#list[@]}; i++ )); do
    pick="${list[$(( (image - 1 + i) % ${#list[@]} ))]}"
    [ "${pick%/*}" = "$dir" ] && grep -qxF -- "${pick##*/}" "$HERE/$theme/hidden-images" 2>/dev/null && continue
    printf '%s' "$pick"
    return 0
  done
}

# Which of the theme's images desk N shows on Auto: the Nth, unless the desk has been moved.
# ⚠️ A MOVED DESK TAKES ITS IMAGE NUMBER WITH IT. Barbarian's desk reordering (bin/ws-renumber,
# 2026-09-19) writes `auto-index` here — lines of "desk image" — so an Auto desk that moves from 5
# to 3 keeps the picture it had instead of taking the one that belonged to its new number.
auto_image() {
  local ws="$1" desk image
  if [ -f "$HERE/auto-index" ]; then
    while read -r desk image; do
      [ "$desk" = "$ws" ] && case "$image" in ''|*[!0-9]*) ;; *) printf '%s' "$image"; return 0 ;; esac
    done < "$HERE/auto-index"
  fi
  printf '%s' "$ws"
}

# ⚰️ THE ACTIVE-WINDOW BORDER HALF WAS REMOVED 2026-08-30, on Dave's word: the border is
# theme-standard again, not per-workspace. It existed from 2026-08-11 ("can one make that
# highlight match the bar color") and read the bar plugin's tints map — which the slimmed
# widget no longer has. `git show d9933c7:omarchy/workspace-backgrounds/per-workspace-wallpaper.sh`
# is the bordered era, including the AARGGBB-vs-RRGGBBAA rotation trap and the Quattro
# `hyprctl eval` form, if a per-workspace border is ever wanted back.

apply() {
  local ws="$1" force="${2:-}" want shown
  # ⚠️ THE v2 EVENT IS `ID,NAME` AND ONLY THE ID IS WANTED. Passed through whole, the id lands in an
  # arithmetic expression as `2,Webscape` — bash reads the comma as the sequence operator, evaluates
  # `Webscape` as a variable name, and dies on `set -u`. Strip at the first comma.
  ws="${ws%%,*}"
  case "$ws" in ''|*[!0-9]*) return 0 ;; esac
  want="$(wallpaper_for "$ws")" || return 0
  [ -n "$want" ] || return 0
  # ⚠️ DE-DUPE OR IT REPAINTS ON EVERY SWITCH. Two workspaces can resolve to the same image (a theme
  # with fewer backgrounds than workspaces wraps, or two desks pinned to one picture), and `setInstant`
  # reloads even the image already on screen, a visible flicker for no change.
  #
  # ⚠️ COMPARE THE IMAGES, NOT THE PATHS. Each desk's pin is its own link (ws1.webp, ws2.webp) and the
  # theme folder is a link too, so two desks showing one picture hand over different strings: both
  # sides are resolved before they are compared. When the picture is the same, only the link moves,
  # so a later re-pin of the desk left behind cannot change what a shell restart or the lock screen
  # reads for this one. One-shot `apply` passes "force": a pin or theme has just changed under the
  # link, and the shell, which cannot be asked what it shows, must be told.
  #
  # ⚠️ COMPARE AGAINST THE SYMLINK, NOT A REMEMBERED LAST VALUE. A remembered value says what THIS
  # script last set; the link says what is actually on screen, and the two part company the moment
  # anything else writes it — `omarchy theme set`, `omarchy theme bg next`. With one image for every
  # workspace (the `all.<ext>` rule above) a remembered value would match forever, so the wallpaper
  # would stay on whatever the theme change left behind and never come back.
  shown="$(readlink -f "$want" 2>/dev/null)"
  [ -n "$shown" ] || shown="$want"
  if [ -z "$force" ] && [ "$shown" = "$(readlink -f "$STATE/background" 2>/dev/null)" ]; then
    [ "$(readlink "$STATE/background" 2>/dev/null)" = "$want" ] || ln -nsf "$want" "$STATE/background" 2>/dev/null
    return 0
  fi

  # ⚠️ TELL THE SHELL, AND MOVE THE LINK. Omarchy 4.5's shell reads the link only when it starts, after
  # its own picker and on `background refresh`, so the IPC call is what changes the screen and the link
  # is what a shell restart, the lock screen and `omarchy-theme-bg-set` read back. One instant call per
  # change: each one reloads the image, so the second "repair" call this script made for the 100ms poll
  # of earlier shells (gone in 4.5) only showed the same picture loading twice.
  omarchy-shell -q background "$METHOD" "$shown" >/dev/null 2>&1
  ln -nsf "$want" "$STATE/background" 2>/dev/null || return 0
}

# One-shot mode: `per-workspace-wallpaper.sh apply [N]` resolves one desk's image NOW and
# exits — Barbarian's background picker (the plugin's bin/ws-bg-pick) calls this after
# moving a pin, because the watcher half below only wakes on workspace SWITCHES. Same
# rules, same code — the resolution logic lives only here.
if [ "${1:-}" = "apply" ]; then
  repair_pins
  apply "${2:-$(hyprctl activeworkspace -j 2>/dev/null | grep -oP '"id":\s*\K[0-9]+' | head -1)}" force
  exit 0
fi

# The pin repair runs before the first paint so a desk is never left showing a stale or wrong
# image while its pin is silently broken (see repair_pins for what Omarchy 4.5 did).
repair_pins

# Paint the workspace we start on, so the wallpaper is right before the first switch rather than
# after it.
apply "$(hyprctl activeworkspace -j 2>/dev/null | grep -oP '"id":\s*\K[0-9]+' | head -1)" force

# ⚠️ socket2, NOT a poll. It is the event stream Hyprland already emits; polling `activeworkspace`
# would be a wake-up every second for something that changes a few times an hour.
#
# ⚠️ `workspacev2`, NOT `workspace`. The plain event carries the workspace's NAME, and every
# workspace here is named — so it would deliver "Webscape" where this script needs "2". The v2 event
# is `workspacev2>>ID,NAME`, which is the only form that gives the id directly.
socat -U - "UNIX-CONNECT:$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock" 2>/dev/null |
  while read -r line; do
    case "$line" in
      workspacev2\>\>*) apply "${line#workspacev2>>}" ;;
    esac
  done
