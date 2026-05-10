"""Shell Commands - Comprehensive Linux command implementations for the virtual OS."""
import os
import re
import time
import math
import hashlib
import json
import base64
from datetime import datetime, timedelta
from collections import OrderedDict


class ShellEnvironment:
    """Environment variables storage."""

    def __init__(self):
        self.vars = {
            "HOME": "/home/user",
            "USER": "user",
            "SHELL": "/bin/bash",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "LANG": "en_US.UTF-8",
            "TERM": "xterm-256color",
            "HOSTNAME": "virtual-os",
            "EDITOR": "nano",
            "PWD": "/home/user",
            "LOGNAME": "user",
            "DISPLAY": ":0",
            "XDG_SESSION_TYPE": "wayland",
            "XDG_CURRENT_DESKTOP": "VirtualDE",
        }

    def get(self, key, default=""):
        return self.vars.get(key, default)

    def set(self, key, value):
        self.vars[key] = value

    def export_all(self):
        return [f"{k}={v}" for k, v in sorted(self.vars.items())]


class ShellPrivilege:
    """Track privilege level (sudo/su)."""

    def __init__(self):
        self.is_root = False
        self.sudo_timestamp = 0
        self.sudo_timeout = 300  # 5 minutes
        self.current_user = "user"

    def can_sudo(self):
        if self.is_root:
            return True
        return time.time() - self.sudo_timestamp < self.sudo_timeout

    def authenticate_sudo(self, password="password"):
        """In virtual OS, any non-empty password works."""
        self.sudo_timestamp = time.time()
        return True

    def switch_to_root(self):
        self.is_root = True
        self.current_user = "root"

    def switch_to_user(self, username="user"):
        self.is_root = False
        self.current_user = username


class ShellCommands:
    """Implements all Linux-like shell commands."""

    def __init__(self, kernel):
        self.kernel = kernel
        self.fs = kernel.filesystem
        self.pm = kernel.process_manager
        self.mm = kernel.memory_manager
        self.dm = kernel.device_manager
        self.env = ShellEnvironment()
        self.priv = ShellPrivilege()
        self.history = []
        self._jobs = {}
        self._next_job_id = 1
        self._bookmarks = {}
        self._aliases = {
            "ll": "ls -l",
            "la": "ls -a",
            "l": "ls -la",
            "cls": "clear",
            "dir": "ls",
            "..": "cd ..",
            "update": "sudo apt update && sudo apt upgrade",
            "upgrade": "sudo apt upgrade",
            "reboot": "sudo reboot",
        }
        self._man_pages = {}

    def execute(self, command_line):
        """Execute a command line string. Returns (output, exit_code)."""
        command_line = command_line.strip()
        if not command_line:
            return "", 0

        # Handle aliases
        first_word = command_line.split()[0]
        if first_word in self._aliases:
            command_line = self._aliases[first_word] + command_line[len(first_word):]

        # Handle pipes (simple)
        if "|" in command_line:
            return self._handle_pipe(command_line)

        # Handle redirects
        if ">>" in command_line:
            return self._handle_redirect(command_line, append=True)
        if ">" in command_line:
            return self._handle_redirect(command_line, append=False)

        # Handle && chaining
        if "&&" in command_line:
            return self._handle_chain(command_line)

        # Handle ; chaining
        if ";" in command_line:
            return self._handle_semicolon(command_line)

        # Handle background &
        if command_line.endswith(" &"):
            command_line = command_line[:-2].strip()

        # Parse command and args
        parts = self._parse_args(command_line)
        if not parts:
            return "", 0

        cmd = parts[0]
        args = parts[1:]

        self.history.append(command_line)

        # Command dispatch - ALL Linux commands
        commands = {
            # File operations
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "pwd": self.cmd_pwd,
            "cat": self.cmd_cat,
            "touch": self.cmd_touch,
            "mkdir": self.cmd_mkdir,
            "rm": self.cmd_rm,
            "rmdir": self.cmd_rmdir,
            "cp": self.cmd_cp,
            "mv": self.cmd_mv,
            "ln": self.cmd_ln,
            "rename": self.cmd_rename,
            "file": self.cmd_file,
            "stat": self.cmd_stat,
            "readlink": self.cmd_readlink,
            "basename": self.cmd_basename,
            "dirname": self.cmd_dirname,
            "realpath": self.cmd_realpath,
            # Text processing
            "echo": self.cmd_echo,
            "printf": self.cmd_printf,
            "grep": self.cmd_grep,
            "egrep": self.cmd_egrep,
            "fgrep": self.cmd_fgrep,
            "sed": self.cmd_sed,
            "awk": self.cmd_awk,
            "cut": self.cmd_cut,
            "paste": self.cmd_paste,
            "tr": self.cmd_tr,
            "wc": self.cmd_wc,
            "head": self.cmd_head,
            "tail": self.cmd_tail,
            "sort": self.cmd_sort,
            "uniq": self.cmd_uniq,
            "diff": self.cmd_diff,
            "cmp": self.cmd_cmp,
            "comm": self.cmd_comm,
            "join": self.cmd_join,
            "split": self.cmd_split,
            "fold": self.cmd_fold,
            "nl": self.cmd_nl,
            "tac": self.cmd_tac,
            "rev": self.cmd_rev,
            "column": self.cmd_column,
            "fmt": self.cmd_fmt,
            "expand": self.cmd_expand,
            "unexpand": self.cmd_unexpand,
            # System
            "ps": self.cmd_ps,
            "kill": self.cmd_kill,
            "killall": self.cmd_killall,
            "pkill": self.cmd_pkill,
            "nice": self.cmd_nice,
            "renice": self.cmd_renice,
            "uname": self.cmd_uname,
            "whoami": self.cmd_whoami,
            "who": self.cmd_who,
            "w": self.cmd_w,
            "uptime": self.cmd_uptime,
            "df": self.cmd_df,
            "du": self.cmd_du,
            "free": self.cmd_free,
            "top": self.cmd_top,
            "htop": self.cmd_htop,
            "vmstat": self.cmd_vmstat,
            "iostat": self.cmd_iostat_cmd,
            "lscpu": self.cmd_lscpu,
            "lsblk": self.cmd_lsblk,
            "lspci": self.cmd_lspci,
            "lsusb": self.cmd_lsusb,
            "lshw": self.cmd_lshw,
            "lsmod": self.cmd_lsmod,
            "lsof": self.cmd_lsof,
            "id": self.cmd_id,
            "groups": self.cmd_groups,
            "hostname": self.cmd_hostname,
            "dnsdomainname": self.cmd_dnsdomainname,
            "date": self.cmd_date,
            "cal": self.cmd_cal,
            "time": self.cmd_time,
            "timeout": self.cmd_timeout,
            # User/privilege
            "sudo": self.cmd_sudo,
            "su": self.cmd_su,
            "passwd": self.cmd_passwd,
            "useradd": self.cmd_useradd,
            "userdel": self.cmd_userdel,
            "usermod": self.cmd_usermod,
            "groupadd": self.cmd_groupadd,
            "groupdel": self.cmd_groupdel,
            "chmod": self.cmd_chmod,
            "chown": self.cmd_chown,
            "chgrp": self.cmd_chgrp,
            "umask": self.cmd_umask,
            "visudo": self.cmd_visudo,
            # Process/Job control
            "jobs": self.cmd_jobs,
            "bg": self.cmd_bg,
            "fg": self.cmd_fg,
            "nohup": self.cmd_nohup,
            "xargs": self.cmd_xargs,
            "wait": self.cmd_wait,
            # Network
            "ping": self.cmd_ping,
            "ifconfig": self.cmd_ifconfig,
            "ip": self.cmd_ip,
            "netstat": self.cmd_netstat,
            "ss": self.cmd_ss,
            "route": self.cmd_route,
            "traceroute": self.cmd_traceroute,
            "dig": self.cmd_dig,
            "nslookup": self.cmd_nslookup,
            "host": self.cmd_host,
            "wget": self.cmd_wget,
            "curl": self.cmd_curl,
            "scp": self.cmd_scp,
            "rsync": self.cmd_rsync,
            "ssh": self.cmd_ssh,
            "ftp": self.cmd_ftp,
            "telnet": self.cmd_telnet,
            "nc": self.cmd_nc,
            "nmap": self.cmd_nmap,
            "arp": self.cmd_arp,
            "iwconfig": self.cmd_iwconfig,
            "ethtool": self.cmd_ethtool,
            # I/O
            "io": self.cmd_io,
            "iostat": self.cmd_iostat,
            # Archive/compression
            "tar": self.cmd_tar,
            "zip": self.cmd_zip,
            "unzip": self.cmd_unzip,
            "gzip": self.cmd_gzip,
            "gunzip": self.cmd_gunzip,
            "bzip2": self.cmd_bzip2,
            "bunzip2": self.cmd_bunzip2,
            "xz": self.cmd_xz,
            "unxz": self.cmd_unxz,
            "7z": self.cmd_7z,
            # Hash/crypto
            "md5sum": self.cmd_md5sum,
            "sha1sum": self.cmd_sha1sum,
            "sha256sum": self.cmd_sha256sum,
            "sha512sum": self.cmd_sha512sum,
            "base64": self.cmd_base64,
            "gpg": self.cmd_gpg,
            # Package management
            "apt": self.cmd_apt,
            "apt-get": self.cmd_apt_get,
            "dpkg": self.cmd_dpkg,
            "yum": self.cmd_yum,
            "rpm": self.cmd_rpm,
            "pacman": self.cmd_pacman,
            "pip": self.cmd_pip,
            "pip3": self.cmd_pip3,
            "npm": self.cmd_npm,
            "gem": self.cmd_gem,
            "cargo": self.cmd_cargo,
            "snap": self.cmd_snap,
            "flatpak": self.cmd_flatpak,
            # System management
            "systemctl": self.cmd_systemctl,
            "service": self.cmd_service,
            "journalctl": self.cmd_journalctl,
            "dmesg": self.cmd_dmesg,
            "modprobe": self.cmd_modprobe,
            "insmod": self.cmd_insmod,
            "rmmod": self.cmd_rmmod,
            "mkfs": self.cmd_mkfs,
            "mount": self.cmd_mount,
            "umount": self.cmd_umount,
            "fdisk": self.cmd_fdisk,
            "parted": self.cmd_parted,
            "fsck": self.cmd_fsck,
            "reboot": self.cmd_reboot,
            "shutdown": self.cmd_shutdown,
            "poweroff": self.cmd_poweroff,
            "halt": self.cmd_halt,
            "init": self.cmd_init,
            "runlevel": self.cmd_runlevel,
            # Disk/memory
            "dd": self.cmd_dd,
            "sync": self.cmd_sync,
            "swapon": self.cmd_swapon,
            "swapoff": self.cmd_swapoff,
            "mkswap": self.cmd_mkswap,
            "ionice": self.cmd_ionice,
            "fstrim": self.cmd_fstrim,
            # Find/search
            "find": self.cmd_find,
            "locate": self.cmd_locate,
            "updatedb": self.cmd_updatedb,
            "which": self.cmd_which,
            "whereis": self.cmd_whereis,
            "whatis": self.cmd_whatis,
            "type": self.cmd_type,
            "grep": self.cmd_grep,
            # Text editors (simulated)
            "nano": self.cmd_nano,
            "vim": self.cmd_vim,
            "vi": self.cmd_vi,
            "emacs": self.cmd_emacs,
            "ed": self.cmd_ed,
            # Terminal
            "clear": self.cmd_clear,
            "reset": self.cmd_reset,
            "tput": self.cmd_tput,
            "stty": self.cmd_stty,
            "tty": self.cmd_tty,
            "script": self.cmd_script,
            # Shell builtins
            "alias": self.cmd_alias,
            "unalias": self.cmd_unalias,
            "set": self.cmd_set,
            "unset": self.cmd_unset,
            "env": self.cmd_env,
            "export": self.cmd_export,
            "source": self.cmd_source,
            "exit": self.cmd_exit,
            "return": self.cmd_return,
            "break": self.cmd_break,
            "continue": self.cmd_continue,
            "eval": self.cmd_eval,
            "exec": self.cmd_exec,
            "shift": self.cmd_shift,
            "test": self.cmd_test,
            "true": self.cmd_true,
            "false": self.cmd_false,
            "seq": self.cmd_seq,
            "yes": self.cmd_yes,
            "factor": self.cmd_factor,
            "bc": self.cmd_bc,
            "expr": self.cmd_expr,
            "let": self.cmd_let,
            "shuf": self.cmd_shuf,
            "xkcd": self.cmd_xkcd,
            # Fun/misc
            "help": self.cmd_help,
            "man": self.cmd_man,
            "info": self.cmd_info,
            "apropos": self.cmd_apropos,
            "history": self.cmd_history,
            "neofetch": self.cmd_neofetch,
            "screenfetch": self.cmd_screenfetch,
            "fastfetch": self.cmd_fastfetch,
            "cowsay": self.cmd_cowsay,
            "cowthink": self.cmd_cowthink,
            "fortune": self.cmd_fortune,
            "lolcat": self.cmd_lolcat,
            "sl": self.cmd_sl,
            "figlet": self.cmd_figlet,
            "toilet": self.cmd_toilet,
            "banner": self.cmd_banner,
            "yes": self.cmd_yes,
            "factor": self.cmd_factor,
            "cal": self.cmd_cal,
            "units": self.cmd_units,
            "look": self.cmd_look,
            "strings": self.cmd_strings,
            "xxd": self.cmd_xxd,
            "hexdump": self.cmd_hexdump,
            "od": self.cmd_od,
            "wall": self.cmd_wall,
            "mesg": self.cmd_mesg,
            "write": self.cmd_write,
            "talk": self.cmd_talk,
            "banner": self.cmd_banner,
            "rig": self.cmd_rig,
        }

        if cmd in commands:
            try:
                return commands[cmd](args)
            except Exception as e:
                return f"{cmd}: error: {str(e)}", 1
        else:
            return f"{cmd}: command not found", 127

    def _parse_args(self, cmd_line):
        """Parse command line respecting quotes."""
        parts = []
        current = ""
        in_quote = None
        for ch in cmd_line:
            if ch in ('"', "'") and in_quote is None:
                in_quote = ch
            elif ch == in_quote:
                in_quote = None
            elif ch == " " and in_quote is None:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += ch
        if current:
            parts.append(current)
        return parts

    def _handle_pipe(self, command_line):
        parts = command_line.split("|", 1)
        output, code = self.execute(parts[0].strip())
        if code != 0:
            return output, code
        second_parts = self._parse_args(parts[1].strip())
        cmd = second_parts[0]
        args = second_parts[1:] + ["--stdin-data=" + output]
        commands = {
            "grep": self.cmd_grep, "egrep": self.cmd_egrep, "fgrep": self.cmd_fgrep,
            "wc": self.cmd_wc, "head": self.cmd_head, "tail": self.cmd_tail,
            "sort": self.cmd_sort, "uniq": self.cmd_uniq, "cut": self.cmd_cut,
            "tr": self.cmd_tr, "sed": self.cmd_sed, "awk": self.cmd_awk,
            "nl": self.cmd_nl, "tac": self.cmd_tac, "rev": self.cmd_rev,
            "column": self.cmd_column, "fold": self.cmd_fold,
            "md5sum": self.cmd_md5sum, "sha256sum": self.cmd_sha256sum,
            "base64": self.cmd_base64, "xxd": self.cmd_xxd,
        }
        if cmd in commands:
            return commands[cmd](args)
        return output, 0

    def _handle_redirect(self, command_line, append):
        if ">>" in command_line:
            parts = command_line.split(">>", 1)
        else:
            parts = command_line.split(">", 1)
        cmd_part = parts[0].strip()
        file_path = parts[1].strip()
        output, code = self.execute(cmd_part)
        if code != 0 and cmd_part.strip():
            return output, code
        self.fs.write_file(file_path, output + "\n" if output else "", append=append)
        return "", 0

    def _handle_chain(self, command_line):
        parts = command_line.split("&&")
        for part in parts:
            output, code = self.execute(part.strip())
            if code != 0:
                return output, code
        return output if output else "", 0

    def _handle_semicolon(self, command_line):
        parts = command_line.split(";")
        all_output = []
        for part in parts:
            output, code = self.execute(part.strip())
            if output:
                all_output.append(output)
        return "\n".join(all_output), 0

    def _expand_path(self, path):
        path = path.replace("~", self.env.get("HOME", "/home/user"))
        if not path.startswith("/"):
            path = self.fs.get_cwd().rstrip("/") + "/" + path
        parts = []
        for part in path.split('/'):
            if part == '' or part == '.':
                continue
            elif part == '..':
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        return '/' + '/'.join(parts) if parts else '/'

    def _require_root(self):
        if not self.priv.is_root and not self.priv.can_sudo():
            return f"{self._current_user()}: permission denied. Use 'sudo' or 'su'."
        return None

    def _current_user(self):
        return self.priv.current_user

    @staticmethod
    def _human_size(size):
        for unit in ['B', 'K', 'M', 'G', 'T']:
            if size < 1024:
                return f"{size}{unit}"
            size /= 1024
        return f"{size:.1f}T"

    # ====== PRIVILEGE COMMANDS ======

    def cmd_sudo(self, args):
        """Execute command as superuser."""
        if not args:
            return "sudo: missing command", 1
        if not self.priv.can_sudo():
            # In virtual OS, accept any password
            self.priv.authenticate_sudo()
        old_user = self.priv.current_user
        self.priv.current_user = "root"
        cmd = args[0]
        cmd_args = args[1:]
        # Execute the command as root
        commands = {
            "ls": self.cmd_ls, "cat": self.cmd_cat, "rm": self.cmd_rm,
            "mkdir": self.cmd_mkdir, "touch": self.cmd_touch, "cp": self.cmd_cp,
            "mv": self.cmd_mv, "chmod": self.cmd_chmod, "chown": self.cmd_chown,
            "kill": self.cmd_kill, "killall": self.cmd_killall, "reboot": self.cmd_reboot,
            "shutdown": self.cmd_shutdown, "poweroff": self.cmd_poweroff,
            "mount": self.cmd_mount, "umount": self.cmd_umount, "fdisk": self.cmd_fdisk,
            "apt": self.cmd_apt, "apt-get": self.cmd_apt_get, "dpkg": self.cmd_dpkg,
            "yum": self.cmd_yum, "pacman": self.cmd_pacman, "systemctl": self.cmd_systemctl,
            "service": self.cmd_service, "passwd": self.cmd_passwd,
            "useradd": self.cmd_useradd, "userdel": self.cmd_userdel,
            "groupadd": self.cmd_groupadd, "groupdel": self.cmd_groupdel,
            "insmod": self.cmd_insmod, "rmmod": self.cmd_rmmod, "modprobe": self.cmd_modprobe,
            "mkfs": self.cmd_mkfs, "fsck": self.cmd_fsck, "dd": self.cmd_dd,
            "swapon": self.cmd_swapon, "swapoff": self.cmd_swapoff, "mkswap": self.cmd_mkswap,
            "visudo": self.cmd_visudo, "halt": self.cmd_halt, "init": self.cmd_init,
            "dmesg": self.cmd_dmesg,
        }
        if cmd in commands:
            try:
                output, code = commands[cmd](cmd_args)
            except Exception as e:
                output, code = f"sudo {cmd}: error: {str(e)}", 1
        else:
            output, code = f"sudo: {cmd}: command not found", 127
        self.priv.current_user = old_user
        return output, code

    def cmd_su(self, args):
        """Switch user or become root."""
        username = "root"
        if args:
            username = args[0]
        if username == "root":
            self.priv.switch_to_root()
            return "Switched to root user.", 0
        else:
            self.priv.switch_to_user(username)
            return f"Switched to user '{username}'.", 0

    def cmd_passwd(self, args):
        """Change user password."""
        err = self._require_root()
        if err:
            return err, 1
        return "passwd: password updated successfully.", 0

    def cmd_useradd(self, args):
        """Add a new user."""
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "useradd: missing username", 1
        username = args[0]
        return f"useradd: user '{username}' created.", 0

    def cmd_userdel(self, args):
        """Delete a user."""
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "userdel: missing username", 1
        return f"userdel: user '{args[0]}' deleted.", 0

    def cmd_usermod(self, args):
        """Modify a user account."""
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "usermod: missing username", 1
        return f"usermod: user '{args[-1]}' modified.", 0

    def cmd_groupadd(self, args):
        """Add a new group."""
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "groupadd: missing group name", 1
        return f"groupadd: group '{args[0]}' created.", 0

    def cmd_groupdel(self, args):
        """Delete a group."""
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "groupdel: missing group name", 1
        return f"groupdel: group '{args[0]}' deleted.", 0

    def cmd_visudo(self, args):
        """Edit the sudoers file."""
        err = self._require_root()
        if err:
            return err, 1
        return "visudo: sudoers file opened (simulated).", 0

    # ====== FILE COMMANDS ======

    def cmd_ls(self, args):
        show_hidden = "-a" in args or "--all" in args
        long_format = "-l" in args or "--long" in args
        human = "-h" in args or "--human" in args
        paths = [a for a in args if not a.startswith("-")]
        if not paths:
            paths = [self.fs.get_cwd()]
        results = []
        for path in paths:
            p = self._expand_path(path)
            success, items, error = self.fs.ls(p, long_format=True)
            if not success:
                results.append(error)
                continue
            if not items:
                continue
            filtered = items
            if not show_hidden:
                filtered = [i for i in items if not i["name"].startswith(".")]
            if long_format:
                results.append(f"total {len(filtered)}")
                for item in filtered:
                    ftype = "d" if item["is_dir"] else "-"
                    size = item["size"]
                    if human:
                        size = self._human_size(size)
                    modified = item["modified"]
                    name = item["name"]
                    results.append(f"{ftype}{item['permissions']}  {str(size):>10}  {modified}  {name}")
            else:
                names = [i["name"] for i in filtered]
                results.append("  ".join(names))
        return "\n".join(results), 0

    def cmd_cd(self, args):
        if not args:
            path = self.env.get("HOME", "/home/user")
        else:
            path = self._expand_path(args[0])
        success, error = self.fs.cd(path)
        if success:
            self.env.set("PWD", self.fs.get_cwd())
            return "", 0
        return error, 1

    def cmd_pwd(self, args):
        return self.fs.get_cwd(), 0

    def cmd_cat(self, args):
        if not args:
            return "cat: missing operand", 1
        show_numbers = "-n" in args
        files = [a for a in args if not a.startswith("-")]
        results = []
        for i, arg in enumerate(files):
            path = self._expand_path(arg)
            success, content, error = self.fs.read_file(path)
            if not success:
                results.append(error)
                continue
            if show_numbers:
                lines = content.split("\n")
                numbered = [f"  {j+1}\t{l}" for j, l in enumerate(lines)]
                results.append("\n".join(numbered))
            else:
                results.append(content.rstrip("\n"))
        return "\n".join(results), 0

    def cmd_touch(self, args):
        if not args:
            return "touch: missing operand", 1
        for arg in args:
            path = self._expand_path(arg)
            success, error = self.fs.create_file(path)
            if not success:
                return error, 1
        return "", 0

    def cmd_mkdir(self, args):
        parents = "-p" in args
        dirs = [a for a in args if not a.startswith("-")]
        if not dirs:
            return "mkdir: missing operand", 1
        for d in dirs:
            path = self._expand_path(d)
            success, error = self.fs.mkdir(path, parents=parents)
            if not success:
                return error, 1
        return "", 0

    def cmd_rmdir(self, args):
        if not args:
            return "rmdir: missing operand", 1
        for d in args:
            path = self._expand_path(d)
            success, error = self.fs.rm(path, recursive=False)
            if not success:
                return error, 1
        return "", 0

    def cmd_rm(self, args):
        recursive = "-r" in args or "-R" in args or "--recursive" in args
        force = "-f" in args or "--force" in args
        interactive = "-i" in args
        files = [a for a in args if not a.startswith("-")]
        if not files:
            return "rm: missing operand", 1
        for f in files:
            path = self._expand_path(f)
            if interactive:
                pass  # Skip confirmation in virtual OS
            success, error = self.fs.rm(path, recursive=recursive)
            if not success and not force:
                return error, 1
        return "", 0

    def cmd_cp(self, args):
        recursive = "-r" in args or "-R" in args or "-a" in args
        interactive = "-i" in args
        src_args = [a for a in args if not a.startswith("-")]
        if len(src_args) < 2:
            return "cp: missing operand", 1
        src = self._expand_path(src_args[0])
        dest = self._expand_path(src_args[1])
        success, error = self.fs.cp(src, dest, recursive=recursive)
        if not success:
            return error, 1
        return "", 0

    def cmd_mv(self, args):
        interactive = "-i" in args
        src_args = [a for a in args if not a.startswith("-")]
        if len(src_args) < 2:
            return "mv: missing operand", 1
        src = self._expand_path(src_args[0])
        dest = self._expand_path(src_args[1])
        success, error = self.fs.mv(src, dest)
        if not success:
            return error, 1
        return "", 0

    def cmd_ln(self, args):
        symbolic = "-s" in args
        files = [a for a in args if not a.startswith("-")]
        if len(files) < 2:
            return "ln: missing operand", 1
        return f"ln: {'symbolic' if symbolic else 'hard'} link created: {files[0]} -> {files[1]}", 0

    def cmd_rename(self, args):
        if len(args) < 2:
            return "rename: usage: rename <old> <new> <files...>", 1
        old, new = args[0], args[1]
        for f in args[2:]:
            path = self._expand_path(f)
            new_path = path.rsplit("/", 1)[0] + "/" + f.rsplit("/", 1)[-1].replace(old, new)
            self.fs.mv(path, new_path)
        return f"rename: {len(args)-2} file(s) renamed.", 0

    def cmd_file(self, args):
        if not args:
            return "file: missing operand", 1
        results = []
        for f in args:
            path = self._expand_path(f)
            entry = self.fs.get_entry(path)
            if entry is None:
                results.append(f"{f}: cannot open (No such file or directory)")
            elif entry.is_dir:
                results.append(f"{f}: directory")
            elif entry.name.endswith(".txt"):
                results.append(f"{f}: ASCII text")
            elif entry.name.endswith(".py"):
                results.append(f"{f}: Python script, ASCII text")
            elif entry.name.endswith(".sh"):
                results.append(f"{f}: Bourne-Again shell script, ASCII text")
            elif entry.name.endswith(".conf"):
                results.append(f"{f}: configuration file, ASCII text")
            elif entry.name.endswith(".log"):
                results.append(f"{f}: log file, ASCII text")
            else:
                results.append(f"{f}: ASCII text")
        return "\n".join(results), 0

    def cmd_stat(self, args):
        if not args:
            return "stat: missing operand", 1
        results = []
        for f in args:
            path = self._expand_path(f)
            entry = self.fs.get_entry(path)
            if entry is None:
                results.append(f"stat: cannot stat '{f}': No such file or directory")
                continue
            ftype = "directory" if entry.is_dir else "regular file"
            results.append(
                f"  File: {entry.name}\n"
                f"  Size: {entry.size}\tBlocks: {(entry.size + 511) // 512}\tIO Block: 4096\t{ftype}\n"
                f"  Access: ({entry.permissions})\tUid: (1000/{self.env.get('USER', 'user')})\tGid: (1000/{self.env.get('USER', 'user')})\n"
                f"  Access: {entry.accessed}\n"
                f"  Modify: {entry.modified}\n"
                f"  Change: {entry.created}"
            )
        return "\n".join(results), 0

    def cmd_readlink(self, args):
        if not args:
            return "readlink: missing operand", 1
        return args[0], 0

    def cmd_basename(self, args):
        if not args:
            return "basename: missing operand", 1
        return args[0].rsplit("/", 1)[-1], 0

    def cmd_dirname(self, args):
        if not args:
            return "dirname: missing operand", 1
        path = args[0].rsplit("/", 1)
        return path[0] if len(path) > 1 else ".", 0

    def cmd_realpath(self, args):
        if not args:
            return "realpath: missing operand", 1
        return self._expand_path(args[0]), 0

    # ====== TEXT PROCESSING COMMANDS ======

    def cmd_echo(self, args):
        no_newline = "-n" in args
        text = " ".join(a for a in args if a != "-n")
        for var, val in self.env.vars.items():
            text = text.replace(f"${var}", val)
            text = text.replace(f"${{{var}}}", val)
        return text, 0 if no_newline else 0

    def cmd_printf(self, args):
        if not args:
            return "printf: missing format string", 1
        fmt = args[0]
        values = args[1:]
        for i, v in enumerate(values):
            fmt = fmt.replace(f"%s", v, 1)
            fmt = fmt.replace(f"%d", v, 1)
        return fmt.replace("\\n", "\n").replace("\\t", "\t"), 0

    def cmd_grep(self, args):
        pattern = None
        file_path = None
        stdin_data = None
        invert = False
        count = False
        ignore_case = False
        i = 0
        while i < len(args):
            a = args[i]
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
            elif a == "-v":
                invert = True
            elif a == "-c":
                count = True
            elif a == "-i":
                ignore_case = True
            elif a.startswith("-"):
                pass
            elif not pattern:
                pattern = a
            elif not file_path:
                file_path = self._expand_path(a)
            i += 1
        if not pattern:
            return "grep: missing pattern", 1
        if stdin_data:
            lines = stdin_data.split("\n")
        elif file_path:
            success, content, error = self.fs.read_file(file_path)
            if not success:
                return error, 1
            lines = content.split("\n")
        else:
            return "grep: missing input", 1
        flags = re.IGNORECASE if ignore_case else 0
        results = [line for line in lines if bool(re.search(pattern, line, flags)) != invert]
        if count:
            return str(len(results)), 0
        return "\n".join(results), 0

    def cmd_egrep(self, args):
        return self.cmd_grep(["-E"] + args)

    def cmd_fgrep(self, args):
        return self.cmd_grep(["-F"] + args)

    def cmd_sed(self, args):
        if not args:
            return "sed: missing expression", 1
        expression = args[0]
        file_path = args[1] if len(args) > 1 else None
        if file_path:
            success, content, error = self.fs.read_file(self._expand_path(file_path))
            if not success:
                return error, 1
        else:
            return "sed: missing input file", 1
        # Simple s/// substitution
        m = re.match(r's/(.*?)/(.*?)/([gi]*)', expression)
        if m:
            pattern, replacement, flags = m.groups()
            count = 0 if 'g' in flags else 1
            ignore = re.IGNORECASE if 'i' in flags else 0
            content = re.sub(pattern, replacement, content, count=count, flags=ignore)
        return content, 0

    def cmd_awk(self, args):
        if not args:
            return "awk: missing expression", 1
        expression = args[0]
        file_path = args[1] if len(args) > 1 else None
        if file_path:
            success, content, error = self.fs.read_file(self._expand_path(file_path))
            if not success:
                return error, 1
        else:
            return "awk: missing input file", 1
        # Simple awk: print fields
        lines = content.strip().split("\n")
        results = []
        m = re.match(r'\{print\s+\$([0-9]+)\}', expression)
        if m:
            field = int(m.group(1))
            for line in lines:
                parts = line.split()
                if field <= len(parts):
                    results.append(parts[field - 1])
        else:
            results = lines
        return "\n".join(results), 0

    def cmd_cut(self, args):
        delimiter = "\t"
        fields = None
        file_path = None
        stdin_data = None
        i = 0
        while i < len(args):
            a = args[i]
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
            elif a == "-d" and i + 1 < len(args):
                delimiter = args[i + 1]
                i += 1
            elif a.startswith("-d="):
                delimiter = a[3:]
            elif a.startswith("-f") or a == "-f" and i + 1 < len(args):
                fields = a[2:] if len(a) > 2 else args[i + 1]
                if not fields.startswith("-f="):
                    i += 1 if a == "-f" else 0
            elif not a.startswith("-"):
                file_path = self._expand_path(a)
            i += 1
        if stdin_data:
            lines = stdin_data.split("\n")
        elif file_path:
            success, content, error = self.fs.read_file(file_path)
            if not success:
                return error, 1
            lines = content.split("\n")
        else:
            return "cut: missing input", 1
        if fields:
            try:
                field_nums = [int(f) for f in fields.split(",")]
                results = []
                for line in lines:
                    parts = line.split(delimiter)
                    selected = [parts[f - 1] for f in field_nums if f <= len(parts)]
                    results.append(delimiter.join(selected))
                return "\n".join(results), 0
            except (ValueError, IndexError):
                return "cut: invalid field specification", 1
        return "\n".join(lines), 0

    def cmd_paste(self, args):
        if len(args) < 2:
            return "paste: missing operand", 1
        files = [self._expand_path(a) for a in args]
        contents = []
        for f in files:
            success, content, _ = self.fs.read_file(f)
            contents.append(content.split("\n") if success else [])
        results = []
        max_lines = max(len(c) for c in contents) if contents else 0
        for i in range(max_lines):
            row = []
            for c in contents:
                row.append(c[i] if i < len(c) else "")
            results.append("\t".join(row))
        return "\n".join(results), 0

    def cmd_tr(self, args):
        if len(args) < 2:
            return "tr: missing operand", 1
        set1, set2 = args[0], args[1]
        stdin_data = None
        for a in args[2:]:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            content = stdin_data
        else:
            return "tr: missing input", 1
        trans = str.maketrans(set1, set2)
        return content.translate(trans), 0

    def cmd_wc(self, args):
        stdin_data = None
        files = []
        show_lines, show_words, show_chars = True, True, True
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
            elif a == "-l":
                show_words = show_chars = False
            elif a == "-w":
                show_lines = show_chars = False
            elif a == "-m" or a == "-c":
                show_lines = show_words = False
            elif not a.startswith("-"):
                files.append(self._expand_path(a))
        if stdin_data:
            content = stdin_data
            filename = ""
        elif files:
            success, content, error = self.fs.read_file(files[0])
            if not success:
                return error, 1
            filename = f" {files[0]}"
        else:
            return "wc: missing input", 1
        lines = content.count("\n")
        words = len(content.split())
        chars = len(content)
        parts = []
        if show_lines:
            parts.append(f"  {lines}")
        if show_words:
            parts.append(f"  {words}")
        if show_chars:
            parts.append(f"  {chars}")
        return "".join(parts) + filename, 0

    def cmd_head(self, args):
        n = 10
        stdin_data = None
        files = []
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                n = int(args[i + 1])
                i += 2
                continue
            if args[i].startswith("-n") and len(args[i]) > 2:
                n = int(args[i][2:])
                i += 1
                continue
            if args[i].startswith("--stdin-data="):
                stdin_data = args[i].split("=", 1)[1]
            else:
                files.append(self._expand_path(args[i]))
            i += 1
        if stdin_data:
            content = stdin_data
        elif files:
            success, content, error = self.fs.read_file(files[0])
            if not success:
                return error, 1
        else:
            return "head: missing input", 1
        return "\n".join(content.split("\n")[:n]), 0

    def cmd_tail(self, args):
        n = 10
        stdin_data = None
        files = []
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                n = int(args[i + 1])
                i += 2
                continue
            if args[i].startswith("--stdin-data="):
                stdin_data = args[i].split("=", 1)[1]
            else:
                files.append(self._expand_path(args[i]))
            i += 1
        if stdin_data:
            content = stdin_data
        elif files:
            success, content, error = self.fs.read_file(files[0])
            if not success:
                return error, 1
        else:
            return "tail: missing input", 1
        return "\n".join(content.split("\n")[-n:]), 0

    def cmd_sort(self, args):
        reverse = "-r" in args
        numeric = "-n" in args
        unique = "-u" in args
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            lines = stdin_data.strip().split("\n")
        else:
            return "", 0
        if numeric:
            try:
                lines.sort(key=lambda x: float(x.split()[0]), reverse=reverse)
            except ValueError:
                lines.sort(reverse=reverse)
        else:
            lines.sort(reverse=reverse)
        if unique:
            seen = []
            for l in lines:
                if l not in seen:
                    seen.append(l)
            lines = seen
        return "\n".join(lines), 0

    def cmd_uniq(self, args):
        stdin_data = None
        count = "-c" in args
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            lines = stdin_data.strip().split("\n")
            seen = []
            counts = []
            for line in lines:
                if line != (seen[-1] if seen else None):
                    seen.append(line)
                    counts.append(1)
                elif seen:
                    counts[-1] += 1
            if count:
                return "\n".join(f"  {c} {l}" for c, l in zip(counts, seen)), 0
            return "\n".join(seen), 0
        return "", 0

    def cmd_diff(self, args):
        if len(args) < 2:
            return "diff: missing operand", 1
        f1, f2 = self._expand_path(args[0]), self._expand_path(args[1])
        s1, c1, _ = self.fs.read_file(f1)
        s2, c2, _ = self.fs.read_file(f2)
        if not s1:
            return f"diff: {args[0]}: No such file", 1
        if not s2:
            return f"diff: {args[1]}: No such file", 1
        lines1, lines2 = c1.split("\n"), c2.split("\n")
        results = []
        max_len = max(len(lines1), len(lines2))
        for i in range(max_len):
            l1 = lines1[i] if i < len(lines1) else ""
            l2 = lines2[i] if i < len(lines2) else ""
            if l1 != l2:
                results.append(f"{i+1}c{i+1}\n< {l1}\n---\n> {l2}")
        return "\n".join(results) if results else "", 0

    def cmd_cmp(self, args):
        if len(args) < 2:
            return "cmp: missing operand", 1
        f1, f2 = self._expand_path(args[0]), self._expand_path(args[1])
        s1, c1, _ = self.fs.read_file(f1)
        s2, c2, _ = self.fs.read_file(f2)
        if c1 == c2:
            return "", 0
        return f"cmp: {args[0]} {args[1]} differ: byte 1, line 1", 1

    def cmd_comm(self, args):
        if len(args) < 2:
            return "comm: missing operand", 1
        f1, f2 = self._expand_path(args[0]), self._expand_path(args[1])
        s1, c1, _ = self.fs.read_file(f1)
        s2, c2, _ = self.fs.read_file(f2)
        set1, set2 = set(c1.split("\n")), set(c2.split("\n"))
        results = []
        for line in sorted(set1 | set2):
            col1 = line if line in set1 and line not in set2 else ""
            col2 = line if line in set2 and line not in set1 else ""
            col3 = line if line in set1 and line in set2 else ""
            results.append(f"\t{col1}\t\t{col2}\t{col3}" if col3 else f"{col1}\t{col2}")
        return "\n".join(results), 0

    def cmd_join(self, args):
        return "join: simulated - output joined lines", 0

    def cmd_split(self, args):
        return "split: simulated - file split into chunks", 0

    def cmd_fold(self, args):
        width = 80
        stdin_data = None
        for a in args:
            if a.startswith("-w"):
                try:
                    width = int(a[2:])
                except ValueError:
                    pass
            elif a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            lines = [stdin_data[i:i+width] for i in range(0, len(stdin_data), width)]
            return "\n".join(lines), 0
        return "", 0

    def cmd_nl(self, args):
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            lines = stdin_data.strip().split("\n")
            return "\n".join(f"  {i+1}\t{l}" for i, l in enumerate(lines)), 0
        return "", 0

    def cmd_tac(self, args):
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            return "\n".join(stdin_data.strip().split("\n")[::-1]), 0
        return "", 0

    def cmd_rev(self, args):
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            return "\n".join(l[::-1] for l in stdin_data.strip().split("\n")), 0
        return "", 0

    def cmd_column(self, args):
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            lines = stdin_data.strip().split("\n")
            max_col = max((len(l.split()) for l in lines), default=0)
            col_widths = [0] * max_col
            rows = [l.split() for l in lines]
            for row in rows:
                for i, val in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(val))
            formatted = []
            for row in rows:
                formatted.append("  ".join(row[i].ljust(col_widths[i]) for i in range(len(row))))
            return "\n".join(formatted), 0
        return "", 0

    def cmd_fmt(self, args):
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            words = stdin_data.split()
            lines, current = [], ""
            for w in words:
                if len(current) + len(w) + 1 > 72:
                    lines.append(current)
                    current = w
                else:
                    current = f"{current} {w}" if current else w
            if current:
                lines.append(current)
            return "\n".join(lines), 0
        return "", 0

    def cmd_expand(self, args):
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            return stdin_data.replace("\t", "    "), 0
        return "", 0

    def cmd_unexpand(self, args):
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            return re.sub(r" {4}", "\t", stdin_data), 0
        return "", 0

    def cmd_tree(self, args):
        path = self.fs.get_cwd()
        if args and not args[0].startswith("-"):
            path = self._expand_path(args[0])
        success, lines, error = self.fs.tree(path)
        if not success:
            return error, 1
        return "\n".join(lines), 0

    def cmd_du(self, args):
        human = "-h" in args
        path = self.fs.get_cwd()
        for a in args:
            if not a.startswith("-"):
                path = self._expand_path(a)
        success, results, error = self.fs.du(path)
        if not success:
            return error, 1
        lines = []
        for p, size in results[:20]:
            if human:
                size_str = self._human_size(size)
            else:
                size_str = str(size)
            lines.append(f"{size_str}\t{p}")
        return "\n".join(lines), 0

    # ====== SYSTEM COMMANDS ======

    def cmd_ps(self, args):
        full = "-f" in args or "--full" in args
        aux = "aux" in args or "-ef" in args
        procs = self.pm.get_all_processes()
        if aux or full:
            lines = ["USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND"]
            lines.append("-" * 100)
            for p in procs:
                mem_pct = (p.memory / self.mm.total_kb) * 100
                lines.append(
                    f"{p.user:<10}{p.pid:<6}{p.cpu_time:>4.1f}{mem_pct:>4.1f}  "
                    f"{p.memory//1024:>6}  {p.memory//1024:>4} ?        "
                    f"{p.state[:4]:<5} {p.start_time if hasattr(p, 'start_time') else '00:00':<6} "
                    f"{p.cpu_time:>4.1f} {p.command}"
                )
        else:
            lines = ["PID    PPID   STAT  COMMAND"]
            lines.append("-" * 50)
            for p in procs:
                lines.append(f"{p.pid:<7}{p.ppid:<7}{p.state[:4]:<6}{p.command}")
        return "\n".join(lines), 0

    def cmd_kill(self, args):
        signal = 9
        pids = []
        for a in args:
            if a.startswith("-"):
                try:
                    signal = int(a.lstrip("-"))
                except ValueError:
                    pass
            else:
                pids.append(a)
        if not pids:
            return "kill: usage: kill [-signal] pid ...", 1
        results = []
        for pid_str in pids:
            try:
                pid = int(pid_str)
            except ValueError:
                results.append(f"kill: invalid pid: {pid_str}")
                continue
            success, error = self.pm.kill_process(pid, signal)
            if success:
                self.mm.free(pid)
            else:
                results.append(error)
        return "\n".join(results) if results else "", 0

    def cmd_killall(self, args):
        if not args:
            return "killall: missing command name", 1
        name = args[0]
        killed = []
        for p in self.pm.get_all_processes():
            if p.name == name or p.command == name:
                success, _ = self.pm.kill_process(p.pid)
                if success:
                    self.mm.free(p.pid)
                    killed.append(str(p.pid))
        if killed:
            return f"Killed process(es): {', '.join(killed)}", 0
        return f"killall: {name}: no process found", 1

    def cmd_pkill(self, args):
        if not args:
            return "pkill: missing pattern", 1
        pattern = args[0]
        killed = []
        for p in self.pm.get_all_processes():
            if pattern in p.name or pattern in p.command:
                success, _ = self.pm.kill_process(p.pid)
                if success:
                    killed.append(str(p.pid))
        if killed:
            return f"Killed process(es): {', '.join(killed)}", 0
        return f"pkill: no process matched '{pattern}'", 1

    def cmd_nice(self, args):
        if not args:
            return "nice: missing command", 1
        return f"nice: executed with default priority 0", 0

    def cmd_renice(self, args):
        if len(args) < 2:
            return "renice: usage: renice <priority> <pid>", 1
        try:
            pid = int(args[-1])
            priority = int(args[0]) if len(args) >= 2 else 0
        except ValueError:
            return "renice: invalid arguments", 1
        proc = self.pm.get_process(pid)
        if proc:
            proc.priority = max(-20, min(19, priority))
            return f"renice: PID {pid} priority set to {proc.priority}", 0
        return f"renice: PID {pid} not found", 1

    def cmd_uname(self, args):
        if "-a" in args or "--all" in args:
            return f"VirtualOS virtual-os 1.0.0 VirtualOS-1.0 x86_64 GNU/Linux", 0
        if "-r" in args:
            return "1.0.0", 0
        if "-n" in args:
            return self.kernel.hostname, 0
        if "-m" in args:
            return "x86_64", 0
        return "VirtualOS", 0

    def cmd_whoami(self, args):
        return self._current_user(), 0

    def cmd_uptime(self, args):
        now = datetime.now().strftime("%H:%M:%S")
        return f" {now} up {self.kernel.get_uptime()},  1 user,  load average: 0.15, 0.10, 0.05", 0

    def cmd_df(self, args):
        human = "-h" in args
        used = self.mm.get_used_memory()
        free = self.mm.get_free_memory()
        total = self.mm.total_kb
        lines = ["Filesystem          1K-blocks      Used Available Use% Mounted on"]
        if human:
            lines.append(f"/dev/virt-disk       {self._human_size(total):>10}  {self._human_size(used):>10}  {self._human_size(free):>10}  {int(used/total*100):>3}% /")
        else:
            lines.append(f"/dev/virt-disk       {total:>10}  {used:>10}  {free:>10}  {int(used/total*100):>3}% /")
        lines.append(f"tmpfs              {total//4:>10}    {total//4:>10}  {total//4:>10}    1% /tmp")
        return "\n".join(lines), 0

    def cmd_free(self, args):
        human = "-h" in args
        usage = self.mm.get_usage()
        if human:
            total = f"{usage['total'] // 1024:>10}"
            used = f"{usage['used'] // 1024:>10}"
            free = f"{usage['free'] // 1024:>10}"
            cached = f"{usage['cached'] // 1024:>10}"
            buffers = f"{usage['buffers'] // 1024:>10}"
        else:
            total = f"{usage['total']:>10}"
            used = f"{usage['used']:>10}"
            free = f"{usage['free']:>10}"
            cached = f"{usage['cached']:>10}"
            buffers = f"{usage['buffers']:>10}"
        lines = ["              total        used        free      cached     buffers"]
        lines.append(f"Mem:    {total}  {used}  {free}  {cached}  {buffers}")
        swap_total = 2048 * 1024
        lines.append(f"Swap:   {swap_total:>10}           0  {swap_total:>10}")
        return "\n".join(lines), 0

    def cmd_top(self, args):
        procs = sorted(self.pm.get_all_processes(), key=lambda p: p.cpu_time, reverse=True)
        usage = self.mm.get_usage()
        lines = [
            f"VirtualOS - {datetime.now().strftime('%H:%M:%S')} up {self.kernel.get_uptime()}",
            f"Tasks: {self.pm.get_process_count()} total, "
            f"{len(self.pm.get_running_processes())} running, "
            f"{sum(1 for p in procs if p.state == 'Ready')} ready, "
            f"{sum(1 for p in procs if p.state == 'Sleeping')} sleeping, "
            f"{sum(1 for p in procs if p.state == 'Stopped')} stopped",
            f"%Cpu(s): 15.0 us,  5.0 sy,  0.0 ni, 80.0 id",
            f"MiB Mem:  {usage['total']//1024:>7.1f} total,  {usage['free']//1024:>7.1f} free,  {usage['used']//1024:>7.1f} used",
            "",
            f"  PID USER      PRI  NI    VIRT    RES    S  %CPU  %MEM   COMMAND",
            "-" * 80,
        ]
        for p in procs[:15]:
            mem_pct = (p.memory / usage['total']) * 100
            cpu = p.cpu_time
            lines.append(
                f"{p.pid:>5} {p.user:<9} {p.priority:>3}  {p.nice:>2}  "
                f"{p.memory//1024:>6}  {p.memory//1024:>6}  "
                f"{p.state[:1]:<2}  {cpu:>5.1f} {mem_pct:>5.1f}   {p.command}"
            )
        return "\n".join(lines), 0

    def cmd_htop(self, args):
        return self.cmd_top(args)

    def cmd_env(self, args):
        return "\n".join(self.env.export_all()), 0

    def cmd_export(self, args):
        if not args:
            return "\n".join(self.env.export_all()), 0
        for arg in args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                self.env.set(key, value)
            else:
                return f"export: invalid: {arg}", 1
        return "", 0

    # ====== NETWORK COMMANDS ======

    def cmd_ping(self, args):
        host = None
        count = 4
        for a in args:
            if a.startswith("-c") and len(a) > 2:
                count = int(a[2:])
            elif not a.startswith("-"):
                host = a
        if not host:
            return "ping: missing host", 1
        results = [f"PING {host} (192.168.1.1) 56(84) bytes of data."]
        for i in range(min(count, 4)):
            t = 0.5 + (i * 0.1)
            results.append(f"64 bytes from {host}: icmp_seq={i+1} ttl=64 time={t:.1f} ms")
        results.append(f"\n--- {host} ping statistics ---")
        results.append(f"{count} packets transmitted, {count} received, 0% packet loss")
        return "\n".join(results), 0

    def cmd_ifconfig(self, args):
        lines = [
            "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500",
            "        inet 192.168.1.100  netmask 255.255.255.0  broadcast 192.168.1.255",
            "        inet6 fe80::1  prefixlen 64  scopeid 0x20<link>",
            "        ether 00:11:22:33:44:55  txqueuelen 1000  (Ethernet)",
            "        RX packets 1234  bytes 123456 (120.5 KiB)",
            "        TX packets 567  bytes 56789 (55.4 KiB)",
            "",
            "lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536",
            "        inet 127.0.0.1  netmask 255.0.0.0",
            "        inet6 ::1  prefixlen 128  scopeid 0x10<loopback>",
            "        loop  txqueuelen 1000  (Local Loopback)",
            "        RX packets 0  bytes 0 (0.0 B)",
            "        TX packets 0  bytes 0 (0.0 B)",
        ]
        return "\n".join(lines), 0

    def cmd_ip(self, args):
        if not args:
            return "ip: usage: ip [addr|route|link|neigh] ...", 1
        subcmd = args[0]
        if subcmd == "addr" or subcmd == "a":
            return self.cmd_ifconfig([])
        elif subcmd == "route" or subcmd == "r":
            return "default via 192.168.1.1 dev eth0\n192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.100", 0
        elif subcmd == "link" or subcmd == "l":
            return "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536\n2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500", 0
        return f"ip: unknown command '{subcmd}'", 1

    def cmd_netstat(self, args):
        lines = [
            "Proto Recv-Q Send-Q Local Address           Foreign Address         State",
            "tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN",
            "tcp        0      0 127.0.0.1:631           0.0.0.0:*               LISTEN",
            "tcp        0      0 192.168.1.100:45678     10.0.0.1:443            ESTABLISHED",
            "udp        0      0 0.0.0.0:68              0.0.0.0:*               ",
        ]
        return "\n".join(lines), 0

    def cmd_ss(self, args):
        return self.cmd_netstat([])

    def cmd_route(self, args):
        lines = [
            "Kernel IP routing table",
            "Destination     Gateway         Genmask         Flags Metric Ref    Use Iface",
            "default         192.168.1.1     0.0.0.0         UG    100    0        0 eth0",
            "192.168.1.0     0.0.0.0         255.255.255.0   U     100    0        0 eth0",
        ]
        return "\n".join(lines), 0

    def cmd_traceroute(self, args):
        if not args:
            return "traceroute: missing host", 1
        host = args[0]
        lines = [f"traceroute to {host} (192.168.1.1), 30 hops max"]
        for i in range(1, 8):
            lines.append(f" {i:>2}  {(0.5 + i * 0.3):.1f} ms  {(0.4 + i * 0.2):.1f} ms  {(0.6 + i * 0.4):.1f} ms")
        return "\n".join(lines), 0

    def cmd_dig(self, args):
        if not args:
            return "dig: missing domain", 1
        domain = args[0]
        return f"""; <<>> DiG 9.16.1 <<>> {domain}
;; ANSWER SECTION:
{domain}.    300    IN    A    192.168.1.1

;; Query time: 12 msec
;; SERVER: 8.8.8.8#53(8.8.8.8)""", 0

    def cmd_nslookup(self, args):
        if not args:
            return "nslookup: missing domain", 1
        return f"Server:\t\t8.8.8.8\nAddress:\t8.8.8.8#53\n\nName:\t{args[0]}\nAddress: 192.168.1.1", 0

    def cmd_host(self, args):
        if not args:
            return "host: missing domain", 1
        return f"{args[0]} has address 192.168.1.1", 0

    def cmd_wget(self, args):
        if not args:
            return "wget: missing URL", 1
        return f"--{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}--  {args[0]}\nResolving... connected.\nHTTP request sent, awaiting response... 200 OK\nLength: 12345 (12K) [text/html]\nSaving to: 'index.html'\n\nindex.html          100%[===================>]  12.06K  --.-KB/s    in 0s\n\nFINISHED -- downloaded 12345 bytes.", 0

    def cmd_curl(self, args):
        if not args:
            return "curl: missing URL", 1
        return f"<!DOCTYPE html><html><body><h1>Response from {args[0]}</h1></body></html>", 0

    def cmd_scp(self, args):
        return "scp: simulated - file transfer complete", 0

    def cmd_rsync(self, args):
        return "rsync: simulated - files synchronized", 0

    def cmd_ssh(self, args):
        if not args:
            return "ssh: usage: ssh [user@]hostname", 1
        return f"ssh: connected to {args[0]} (simulated)", 0

    def cmd_ftp(self, args):
        return "ftp: simulated FTP client (use 'quit' to exit)", 0

    def cmd_telnet(self, args):
        if not args:
            return "telnet: missing host", 1
        return f"telnet: connected to {args[0]} (simulated)", 0

    def cmd_nc(self, args):
        return "nc: netcat - connection opened (simulated)", 0

    def cmd_nmap(self, args):
        if not args:
            return "nmap: missing target", 1
        return f"""Starting Nmap 7.80 ( https://nmap.org )
Nmap scan report for {args[0]} (192.168.1.1)
Host is up (0.0012s latency).
PORT     STATE  SERVICE
22/tcp   open   ssh
80/tcp   open   http
443/tcp  open   https
3306/tcp closed mysql

Nmap done: 1 IP address (1 host up) scanned in 1.23 seconds""", 0

    def cmd_arp(self, args):
        return """Address                  HWtype  HWaddress           Flags Mask            Iface
_gateway                 ether   00:11:22:33:44:55   C                     eth0""", 0

    def cmd_iwconfig(self, args):
        return """wlan0     IEEE 802.11  ESSID:"VirtualOS-WiFi"  Nickname:"<WIFI@REALTEK>"
          Mode:Managed  Frequency:5.18 GHz  Access Point: AA:BB:CC:DD:EE:FF
          Bit Rate=433.3 Mb/s   Tx-Power=20 dBm
          Link Quality=70/70  Signal level=-40 dBm""", 0

    def cmd_ethtool(self, args):
        if not args:
            return "ethtool: missing interface", 1
        return f"""Settings for {args[0]}:
        Supported ports: [ TP ]
        Supported link modes:   100baseT/Half 100baseT/Full 1000baseT/Full
        Speed: 1000Mb/s
        Duplex: Full
        Port: Twisted Pair
        Link detected: yes""", 0

    # ====== I/O COMMANDS ======

    def cmd_io(self, args):
        """Send an I/O request. Usage: io <device_name> <read|write|input|output> [data]"""
        if len(args) < 2:
            return "Usage: io <device_name> <read|write|input|output> [data]", 1
        device_name = args[0]
        request_type = args[1].capitalize()
        data = " ".join(args[2:]) if len(args) > 2 else ""
        valid_types = ["Read", "Write", "Input", "Output"]
        if request_type not in valid_types:
            return f"Invalid I/O type. Valid: {', '.join(valid_types)}", 1
        success, msg = self.dm.send_io_request(device_name, request_type, data)
        return msg, 0 if success else 1

    def cmd_iostat(self, args):
        """Show I/O request status."""
        requests = self.dm.get_io_requests(20)
        if not requests:
            return "No I/O requests in queue.", 0
        lines = [
            f"{'ID':<6} {'Device':<30} {'Type':<10} {'State':<12} {'Time':<10} {'Result'}",
            "-" * 100,
        ]
        for req in requests:
            d = req.to_dict()
            lines.append(
                f"{d['id']:<6} {d['device']:<30} {d['type']:<10} {d['state']:<12} {d['timestamp']:<10} {d['result']}"
            )
        pending = self.dm.get_io_pending_count()
        lines.append("")
        lines.append(f"Pending: {pending}")
        return "\n".join(lines), 0

    # ====== DEVICE INFO COMMANDS ======

    def cmd_lscpu(self, args):
        return """Architecture:          x86_64
CPU(s):                4
Thread(s) per core:    1
Core(s) per socket:    4
Socket(s):             1
Vendor ID:             VirtualOS
CPU family:            6
Model:                 158
Model name:            VirtualOS CPU @ 3.60GHz
Stepping:              10
CPU MHz:               3600.000
BogoMIPS:              7200.00
L1d cache:             32K
L1i cache:             32K
L2 cache:              256K
L3 cache:              8192K""", 0

    def cmd_lsblk(self, args):
        return """NAME   MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
sda      8:0    0   256G  0 disk
├─sda1   8:1    0   512M  0 part /boot
├─sda2   8:2    0     8G  0 part [SWAP]
└─sda3   8:3    0 247.5G  0 part /
sdb      8:16   0   512G  0 disk
└─sdb1   8:17   0   512G  0 part /home""", 0

    def cmd_lspci(self, args):
        devices = self.dm.get_devices_by_category("Display adapters") + \
                  self.dm.get_devices_by_category("Network adapters")
        lines = []
        for d in devices:
            lines.append(f"00:{len(lines):02x}.0 {d.category}: {d.name}")
        if not lines:
            lines = [
                "00:00.0 Host bridge: VirtualOS Host Bridge",
                "00:01.0 VGA compatible controller: Virtual Display Adapter",
                "00:02.0 Ethernet controller: Virtual Ethernet Adapter",
                "00:03.0 Audio device: Virtual Audio Device",
            ]
        return "\n".join(lines), 0

    def cmd_lsusb(self, args):
        return """Bus 001 Device 001: ID 1d6b:0002 VirtualOS USB 2.0
Bus 001 Device 002: ID 0000:0001 Virtual Keyboard
Bus 001 Device 003: ID 0000:0002 Virtual Mouse
Bus 002 Device 001: ID 1d6b:0003 VirtualOS USB 3.0""", 0

    def cmd_lshw(self, args):
        return f"""virtual-os
    description: Virtual Machine
    vendor: VirtualOS
    version: 1.0
    width: 64 bits
    capabilities: smp
  *-core
       description: Motherboard
    *-cpu:0
         description: CPU
         product: VirtualOS CPU
         vendor: VirtualOS
         physical id: 0
         size: 3600MHz
         capacity: 3600MHz
         capabilities: x86_64
    *-memory
         description: System Memory
         size: {self.mm.total_kb // 1024}MiB
    *-disk
         description: ATA Disk
         product: Virtual HDD
         size: 256GiB""", 0

    def cmd_lsmod(self, args):
        return """Module                  Size  Used by
virt_gpu               16384  1
virt_net               20480  0
virt_audio             12288  2
virt_kb                 8192  0
virt_mouse             10240  0""", 0

    def cmd_lsof(self, args):
        return """COMMAND     PID USER   FD   TYPE  SIZE  NODE NAME
init          1 root  cwd    DIR  4096     2 /
init          1 root  txt    REG  8192   128 /sbin/init
system-mon    3 root  cwd    DIR  4096     2 /
bash        101 user  cwd    DIR  4096   512 /home/user/Desktop""", 0

    # ====== USER COMMANDS ======

    def cmd_id(self, args):
        return f"uid=1000({self._current_user()}) gid=1000({self._current_user()}) groups=1000({self._current_user()}),27(sudo)", 0

    def cmd_groups(self, args):
        return f"{self._current_user()} : {self._current_user()} sudo", 0

    def cmd_who(self, args):
        return f"{self._current_user()}  tty0  {datetime.now().strftime('%Y-%m-%d %H:%M')} (:0)", 0

    def cmd_w(self, args):
        return f" {datetime.now().strftime('%H:%M:%S')} up {self.kernel.get_uptime()},  1 user,  load average: 0.15, 0.10, 0.05\nUSER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT\n{self._current_user():<8} tty0     :0               {datetime.now().strftime('%H:%M')}    0.00s  0.15s  0.01s w", 0

    def cmd_hostname(self, args):
        if args:
            self.kernel.hostname = args[0]
            self.env.set("HOSTNAME", args[0])
        return self.kernel.hostname, 0

    def cmd_dnsdomainname(self, args):
        return "localdomain", 0

    def cmd_date(self, args):
        if "%s" in args:
            return str(int(time.time())), 0
        if "-u" in args:
            return datetime.utcnow().strftime("%a %b %d %H:%M:%S UTC %Y"), 0
        return datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y"), 0

    def cmd_cal(self, args):
        now = datetime.now()
        year = now.year
        month = now.month
        if len(args) >= 2:
            month, year = int(args[0]), int(args[1])
        elif len(args) == 1:
            year = int(args[0])
        import calendar
        return calendar.month(year, month), 0

    def cmd_time(self, args):
        if not args:
            return "time: missing command", 1
        start = time.time()
        cmd = args[0]
        cmd_args = args[1:]
        commands = {"ls": self.cmd_ls, "cat": self.cmd_cat, "find": self.cmd_find}
        if cmd in commands:
            output, code = commands[cmd](cmd_args)
        else:
            output, code = f"time: {cmd}: command not found", 127
        elapsed = time.time() - start
        return f"{output}\n\nreal\t0m{elapsed:.3f}s\nuser\t0m{elapsed * 0.8:.3f}s\nsys\t0m{elapsed * 0.2:.3f}s" if output else f"\nreal\t0m{elapsed:.3f}s", code

    def cmd_timeout(self, args):
        if len(args) < 2:
            return "timeout: missing duration or command", 1
        return f"timeout: executed {args[1]} with {args[0]}s limit", 0

    # ====== PROCESS/JOB CONTROL ======

    def cmd_jobs(self, args):
        if not self._jobs:
            return "", 0
        lines = []
        for jid, job in self._jobs.items():
            status = "Running" if job["running"] else "Stopped"
            lines.append(f"[{jid}]  {status}  {job['command']}")
        return "\n".join(lines), 0

    def cmd_bg(self, args):
        return "bg: no stopped jobs", 0

    def cmd_fg(self, args):
        return "fg: no stopped jobs", 0

    def cmd_nohup(self, args):
        if not args:
            return "nohup: missing command", 1
        return f"nohup: running '{args[0]}' in background", 0

    def cmd_xargs(self, args):
        return "xargs: simulated", 0

    def cmd_wait(self, args):
        return "", 0

    # ====== ARCHIVE/COMPRESSION ======

    def cmd_tar(self, args):
        if not args:
            return "tar: missing operand", 1
        action = args[0].lstrip("-")
        files = [a for a in args if not a.startswith("-")]
        if "c" in action:
            return f"tar: archive created: {files[0] if files else 'archive.tar'}", 0
        elif "x" in action:
            return f"tar: extracted: {files[0] if files else 'archive.tar'}", 0
        elif "t" in action:
            return "file1.txt\nfile2.txt\ndir/", 0
        return "tar: unknown action", 1

    def cmd_zip(self, args):
        if len(args) < 2:
            return "zip: missing operand", 1
        return f"zip: adding: {args[1]} (stored 0%)", 0

    def cmd_unzip(self, args):
        if not args:
            return "unzip: missing archive", 1
        return f"unzip: extracting {args[0]}...\n  inflating: file.txt", 0

    def cmd_gzip(self, args):
        if not args:
            return "gzip: missing file", 1
        return f"gzip: {args[0]} compressed", 0

    def cmd_gunzip(self, args):
        if not args:
            return "gunzip: missing file", 1
        return f"gunzip: {args[0]} decompressed", 0

    def cmd_bzip2(self, args):
        if not args:
            return "bzip2: missing file", 1
        return f"bzip2: {args[0]} compressed", 0

    def cmd_bunzip2(self, args):
        if not args:
            return "bunzip2: missing file", 1
        return f"bunzip2: {args[0]} decompressed", 0

    def cmd_xz(self, args):
        if not args:
            return "xz: missing file", 1
        return f"xz: {args[0]} compressed", 0

    def cmd_unxz(self, args):
        if not args:
            return "unxz: missing file", 1
        return f"unxz: {args[0]} decompressed", 0

    def cmd_7z(self, args):
        return "7z: 7-Zip simulated", 0

    # ====== HASH/CRYPTO ======

    def cmd_md5sum(self, args):
        stdin_data = None
        files = []
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
            else:
                files.append(a)
        if stdin_data:
            h = hashlib.md5(stdin_data.encode()).hexdigest()
            return f"{h}  -", 0
        if files:
            results = []
            for f in files:
                success, content, _ = self.fs.read_file(self._expand_path(f))
                if success:
                    h = hashlib.md5(content.encode()).hexdigest()
                    results.append(f"{h}  {f}")
                else:
                    results.append(f"md5sum: {f}: No such file")
            return "\n".join(results), 0
        return "md5sum: missing operand", 1

    def cmd_sha1sum(self, args):
        return self._hash_cmd(args, "sha1")

    def cmd_sha256sum(self, args):
        return self._hash_cmd(args, "sha256")

    def cmd_sha512sum(self, args):
        return self._hash_cmd(args, "sha512")

    def _hash_cmd(self, args, algo):
        stdin_data = None
        files = []
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
            else:
                files.append(a)
        if stdin_data:
            h = getattr(hashlib, algo)(stdin_data.encode()).hexdigest()
            return f"{h}  -", 0
        if files:
            results = []
            for f in files:
                success, content, _ = self.fs.read_file(self._expand_path(f))
                if success:
                    h = getattr(hashlib, algo)(content.encode()).hexdigest()
                    results.append(f"{h}  {f}")
                else:
                    results.append(f"{algo}sum: {f}: No such file")
            return "\n".join(results), 0
        return f"{algo}sum: missing operand", 1

    def cmd_base64(self, args):
        encode = "-d" not in args
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            if encode:
                return base64.b64encode(stdin_data.encode()).decode(), 0
            else:
                return base64.b64decode(stdin_data.encode()).decode(), 0
        return "base64: missing input", 1

    def cmd_gpg(self, args):
        return "gpg: GnuPG simulated", 0

    # ====== PACKAGE MANAGEMENT ======

    def cmd_apt(self, args):
        if not args:
            return "apt: missing command. Usage: apt [update|upgrade|install|remove|search|list|show]", 1
        action = args[0]
        if action == "update":
            return "Hit:1 http://archive.virtualos.org/virtualos stable InRelease\nReading package lists... Done\nBuilding dependency tree... Done\nAll packages are up to date.", 0
        elif action == "upgrade":
            return "Reading package lists... Done\nBuilding dependency tree... Done\nCalculating upgrade... Done\n0 upgraded, 0 newly installed, 0 to remove.", 0
        elif action == "install":
            if len(args) < 2:
                return "apt: missing package name", 1
            return f"Reading package lists... Done\nBuilding dependency tree... Done\nThe following NEW packages will be installed:\n  {args[1]}\n0 upgraded, 1 newly installed, 0 to remove.\nSetting up {args[1]} (1.0.0) ...", 0
        elif action == "remove":
            return f"Removing {' '.join(args[1:])}...", 0
        elif action == "search":
            return f"{' '.join(args[1:])}/stable 1.0.0 amd64\n  VirtualOS package", 0
        elif action == "list":
            return "Listing... Done\nvirtualos-base/stable 1.0.0 amd64 [installed]\nvterm/stable 1.0.0 amd64 [installed]\nvirtualde/stable 1.0.0 amd64 [installed]", 0
        elif action == "show":
            return f"Package: {args[1] if len(args) > 1 else 'unknown'}\nVersion: 1.0.0\nDescription: VirtualOS package", 0
        return f"apt: unknown command '{action}'", 1

    def cmd_apt_get(self, args):
        return self.cmd_apt(args)

    def cmd_dpkg(self, args):
        if not args:
            return "dpkg: missing action", 1
        if args[0] == "-l":
            return "ii  virtualos-base    1.0.0  amd64  VirtualOS base system\nii  vterm             1.0.0  amd64  VirtualOS terminal\nii  virtualde         1.0.0  amd64  Virtual Desktop Environment", 0
        return "dpkg: simulated", 0

    def cmd_yum(self, args):
        return self.cmd_apt(args)

    def cmd_rpm(self, args):
        return "rpm: simulated package manager", 0

    def cmd_pacman(self, args):
        if not args:
            return "pacman: missing command. Usage: pacman -S <pkg> | -R <pkg> | -Q | -Syu", 1
        if "-S" in args[0]:
            pkg = args[1] if len(args) > 1 else "package"
            return f"resolving dependencies...\nlooking for conflicting packages...\n\nPackages (1) {pkg}-1.0.0-1\n\nTotal Installed Size:  1.23 MiB\n\n:: Proceed with installation? [Y/n] y\n:: Processing package changes...\n(1/1) installing {pkg}", 0
        elif "-Q" in args[0]:
            return "virtualos-base 1.0.0-1\nvterm 1.0.0-1\nvirtualde 1.0.0-1", 0
        return "pacman: simulated", 0

    def cmd_pip(self, args):
        return self._pip_cmd(args, "pip")

    def cmd_pip3(self, args):
        return self._pip_cmd(args, "pip3")

    def _pip_cmd(self, args, name):
        if not args:
            return f"{name}: missing command. Usage: {name} install|uninstall|list|search", 1
        if args[0] == "install":
            pkg = " ".join(args[1:]) if len(args) > 1 else "package"
            return f"Collecting {pkg}\n  Downloading {pkg}-1.0.0.tar.gz\nInstalling collected packages: {pkg}\nSuccessfully installed {pkg}-1.0.0", 0
        elif args[0] == "list":
            return "Package           Version\n----------------- -------\npip              23.0.1\nsetuptools       68.0.0\nwheel            0.41.0", 0
        elif args[0] == "search":
            return f"{' '.join(args[1:])}    - Search result", 0
        return f"{name}: unknown command '{args[0]}'", 1

    def cmd_npm(self, args):
        if not args:
            return "npm: missing command. Usage: npm install|run|init|list", 1
        if args[0] == "install":
            return f"added 1 package in 0.5s", 0
        elif args[0] == "list":
            return "virtual-os@1.0.0\n└── (empty)", 0
        return f"npm: simulated - {args[0]}", 0

    def cmd_gem(self, args):
        return "gem: RubyGems simulated", 0

    def cmd_cargo(self, args):
        if not args:
            return "cargo: missing command. Usage: cargo build|run|new|install", 1
        if args[0] == "build":
            return "   Compiling virtual-os v0.1.0\n    Finished dev [unoptimized + debuginfo] target(s) in 2.34s", 0
        elif args[0] == "run":
            return "   Compiling virtual-os v0.1.0\n    Finished dev [unoptimized + debuginfo] target(s) in 1.23s\n     Running `target/debug/virtual-os`\nHello, world!", 0
        return f"cargo: simulated - {args[0]}", 0

    def cmd_snap(self, args):
        return "snap: Snap package manager simulated", 0

    def cmd_flatpak(self, args):
        return "flatpak: Flatpak package manager simulated", 0

    # ====== SYSTEM MANAGEMENT ======

    def cmd_systemctl(self, args):
        if not args:
            return "systemctl: missing command. Usage: systemctl [status|start|stop|restart|enable|disable|list-units] <service>", 1
        action = args[0]
        service = args[1] if len(args) > 1 else ""
        if action == "status":
            return f"● {service}.service - {service} Service\n     Loaded: loaded (/etc/systemd/system/{service}.service; enabled)\n     Active: active (running) since {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n   Main PID: 1234 ({service})\n      Tasks: 5 (limit: 4915)\n     Memory: 12.3M", 0
        elif action in ("start", "stop", "restart", "enable", "disable"):
            return f"{action} {service}.service", 0
        elif action == "list-units":
            return "UNIT                  LOAD   ACTIVE SUB       DESCRIPTION\nsystemd-journald      loaded active running Journal Service\nsystemd-udevd         loaded active running udev Kernel Device Manager\nvirtualos-base       loaded active running VirtualOS Base", 0
        return f"systemctl: unknown command '{action}'", 1

    def cmd_service(self, args):
        if not args:
            return "service: missing service name", 1
        return f"service {args[0]}: {args[1] if len(args) > 1 else 'status'} (simulated)", 0

    def cmd_journalctl(self, args):
        return f"-- Journal begins at {datetime.now().strftime('%Y-%m-%d')} --\n{datetime.now().strftime('%H:%M:%S')} virtual-os systemd[1]: Started VirtualOS.\n{datetime.now().strftime('%H:%M:%S')} virtual-os kernel: VirtualOS 1.0.0 initialized.\n{datetime.now().strftime('%H:%M:%S')} virtual-os systemd[1]: Reached target Multi-User System.", 0

    def cmd_dmesg(self, args):
        err = self._require_root()
        if err:
            return err + "\n[    0.000000] Linux version VirtualOS 1.0.0\n[    0.000000] Command line: root=/dev/sda3\n[    0.012345] Memory: 8192MB available\n[    0.023456] ACPI: RSDP 0000000000000000 000024 (v02 VirtualOS)\n[    0.034567] smpboot: CPU0: VirtualOS CPU @ 3.60GHz\n[    0.045678] smpboot: Total of 4 processors activated\n[    0.123456] EXT4-fs (sda3): mounted filesystem with ordered data mode", 0
        return "[    0.000000] Linux version VirtualOS 1.0.0\n[    0.012345] Memory: 8192MB available\n[    0.023456] CPU: VirtualOS CPU @ 3.60GHz (4 cores)\n[    0.034567] EXT4-fs (sda3): mounted filesystem", 0

    def cmd_modprobe(self, args):
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "modprobe: missing module name", 1
        return f"modprobe: module {args[0]} loaded", 0

    def cmd_insmod(self, args):
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "insmod: missing module file", 1
        return f"insmod: {args[0]} inserted", 0

    def cmd_rmmod(self, args):
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "rmmod: missing module name", 1
        return f"rmmod: module {args[0]} removed", 0

    def cmd_mkfs(self, args):
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "mkfs: missing device", 1
        return f"mkfs: filesystem created on {args[0]}", 0

    def cmd_mount(self, args):
        err = self._require_root()
        if err and args:
            return err, 1
        if not args:
            return "/dev/sda3 on / type ext4 (rw,relatime)\ntmpfs on /tmp type tmpfs (rw,nosuid,nodev)\nproc on /proc type proc (rw,nosuid,nodev,noexec)", 0
        return f"mount: {args[0]} mounted on {args[1] if len(args) > 1 else '/mnt'}", 0

    def cmd_umount(self, args):
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "umount: missing mount point", 1
        return f"umount: {args[0]} unmounted", 0

    def cmd_fdisk(self, args):
        err = self._require_root()
        if err and not args:
            pass
        return """Disk /dev/sda: 256 GiB, 274877906944 bytes, 536870912 sectors
Disk model: Virtual HDD
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes

Device     Boot   Start       End   Sectors   Size Id Type
/dev/sda1  *       2048   1050623   1048576   512M 83 Linux
/dev/sda2       1050624  17827839  16777216     8G 82 Linux swap
/dev/sda3      17827840 536870911 519043072 247.5G 83 Linux""", 0

    def cmd_parted(self, args):
        return "parted: GNU Parted 3.4 (simulated)", 0

    def cmd_fsck(self, args):
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "fsck: missing device", 1
        return f"fsck: {args[0]}: clean, 123456/16384000 files, 12345678/65536000 blocks", 0

    def cmd_reboot(self, args):
        err = self._require_root()
        if err:
            return err, 1
        return "System reboot initiated (simulated).", 0

    def cmd_shutdown(self, args):
        err = self._require_root()
        if err:
            return err, 1
        return "System shutdown initiated (simulated).", 0

    def cmd_poweroff(self, args):
        err = self._require_root()
        if err:
            return err, 1
        return "System poweroff initiated (simulated).", 0

    def cmd_halt(self, args):
        err = self._require_root()
        if err:
            return err, 1
        return "System halt initiated (simulated).", 0

    def cmd_init(self, args):
        err = self._require_root()
        if err:
            return err, 1
        runlevel = args[0] if args else "5"
        return f"init: switching to runlevel {runlevel}", 0

    def cmd_runlevel(self, args):
        return "N 5", 0

    # ====== DISK/MEMORY ======

    def cmd_dd(self, args):
        err = self._require_root()
        if err and (any("of=" in a for a in args)):
            return err, 1
        bs = 512
        count = 1
        for a in args:
            if a.startswith("bs="):
                bs = int(a.split("=")[1])
            elif a.startswith("count="):
                count = int(a.split("=")[1])
        total = bs * count
        return f"{count}+0 records in\n{count}+0 records out\n{total} bytes ({self._human_size(total)}) copied, 0.001s, {self._human_size(total // 1)}/s", 0

    def cmd_sync(self, args):
        return "", 0

    def cmd_swapon(self, args):
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "Filename\t\tType\t\tSize\tUsed\tPriority\n/dev/sda2                               partition\t8388604\t0\t-2", 0
        return f"swapon: {args[0]} enabled", 0

    def cmd_swapoff(self, args):
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "swapoff: missing device", 1
        return f"swapoff: {args[0]} disabled", 0

    def cmd_mkswap(self, args):
        err = self._require_root()
        if err:
            return err, 1
        if not args:
            return "mkswap: missing device", 1
        return f"mkswap: swap space set up on {args[0]}", 0

    def cmd_ionice(self, args):
        return "ionice: I/O priority set", 0

    def cmd_fstrim(self, args):
        err = self._require_root()
        if err:
            return err, 1
        return "fstrim: /: 123.4 MiB trimmed", 0

    def cmd_vmstat(self, args):
        return """procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1  0      0 4096000 262144 524288    0    0    12    34  123  456 15  5 80  0  0""", 0

    def cmd_iostat_cmd(self, args):
        return """Linux VirtualOS 1.0.0 (virtual-os)  2026-01-01  x86_64  (4 CPU)

avg-cpu:  %user   %nice %system %iowait  %steal   %idle
          15.0    0.0     5.0    2.0     0.0    80.0

Device            tps    kB_read/s    kB_wrtn/s    kB_read    kB_wrtn
sda              12.34      1234.56       567.89    1234567     567890
sdb               5.67       456.78       123.45     456789     123456""", 0

    # ====== FIND/SEARCH ======

    def cmd_find(self, args):
        path = self.fs.get_cwd()
        name_filter = None
        type_filter = None
        i = 0
        while i < len(args):
            if not args[i].startswith("-"):
                path = self._expand_path(args[i])
            elif args[i] == "-name" and i + 1 < len(args):
                name_filter = args[i + 1].strip("*")
                i += 1
            elif args[i] == "-type" and i + 1 < len(args):
                type_filter = args[i + 1]
                i += 1
            elif args[i] == "-exec":
                return "find: -exec simulated", 0
            i += 1
        success, results, error = self.fs.find(path, name=name_filter, type_=type_filter)
        if not success:
            return error, 1
        return "\n".join(results), 0

    def cmd_locate(self, args):
        if not args:
            return "locate: missing pattern", 1
        success, all_items, _ = self.fs.find("/", name=args[0].strip("*"))
        if success:
            return "\n".join(all_items[:20]), 0
        return "", 0

    def cmd_updatedb(self, args):
        return "updatedb: database updated", 0

    def cmd_which(self, args):
        if not args:
            return "which: missing command", 1
        # Check if command exists in our command list
        commands = {"ls", "cd", "pwd", "cat", "touch", "mkdir", "rm", "cp", "mv",
                    "echo", "grep", "wc", "head", "tail", "sort", "ps", "kill",
                    "uname", "whoami", "uptime", "df", "free", "env", "export",
                    "ping", "ifconfig", "clear", "help", "history", "date", "cal",
                    "sudo", "su", "find", "tree", "man", "neofetch", "cowsay"}
        results = []
        for cmd in args:
            if cmd in commands or cmd in self._aliases:
                results.append(f"/usr/bin/{cmd}")
            else:
                results.append(f"{cmd} not found")
        return "\n".join(results), 0

    def cmd_whereis(self, args):
        if not args:
            return "whereis: missing command", 1
        return " ".join(f"{cmd}: /usr/bin/{cmd} /usr/share/man/man1/{cmd}.1.gz" for cmd in args), 0

    def cmd_whatis(self, args):
        if not args:
            return "whatis: missing command", 1
        descriptions = {
            "ls": "list directory contents", "cat": "concatenate files", "grep": "print matching lines",
            "ps": "report process status", "kill": "terminate a process", "find": "search for files",
            "man": "format and display manual pages", "chmod": "change file permissions",
        }
        results = []
        for cmd in args:
            desc = descriptions.get(cmd, "no manual entry")
            results.append(f"{cmd} (1) - {desc}")
        return "\n".join(results), 0

    def cmd_type(self, args):
        if not args:
            return "type: missing argument", 1
        results = []
        for cmd in args:
            if cmd in self._aliases:
                results.append(f"{cmd} is aliased to '{self._aliases[cmd]}'")
            else:
                results.append(f"{cmd} is /usr/bin/{cmd}")
        return "\n".join(results), 0

    # ====== TEXT EDITORS ======

    def cmd_nano(self, args):
        if not args:
            return "nano: GNU nano editor (simulated)", 0
        return f"nano: opened '{args[0]}' (simulated editor)", 0

    def cmd_vim(self, args):
        if not args:
            return "VIM - Vi IMproved 9.0 (simulated)\n:type :q to exit", 0
        return f"vim: opened '{args[0]}' (simulated editor)", 0

    def cmd_vi(self, args):
        return self.cmd_vim(args)

    def cmd_emacs(self, args):
        return "GNU Emacs 29.1 (simulated)", 0

    def cmd_ed(self, args):
        return "ed: GNU ed line editor (simulated)", 0

    # ====== TERMINAL ======

    def cmd_clear(self, args):
        return "__CLEAR__", 0

    def cmd_reset(self, args):
        return "__CLEAR__", 0

    def cmd_tput(self, args):
        return "", 0

    def cmd_stty(self, args):
        return "speed 38400 baud; rows 24; columns 80; line = 0;", 0

    def cmd_tty(self, args):
        return "/dev/tty0", 0

    def cmd_script(self, args):
        return "Script started (simulated)", 0

    # ====== SHELL BUILTINS ======

    def cmd_alias(self, args):
        if not args:
            return "\n".join(f"alias {k}='{v}'" for k, v in sorted(self._aliases.items())), 0
        if "=" in args[0]:
            key, value = args[0].split("=", 1)
            self._aliases[key] = value.strip("'\"")
            return "", 0
        return f"alias: {args[0]}: not found", 1

    def cmd_unalias(self, args):
        if not args:
            return "unalias: missing name", 1
        if args[0] in self._aliases:
            del self._aliases[args[0]]
        return "", 0

    def cmd_set(self, args):
        lines = self.env.export_all()
        lines.extend(f"alias {k}='{v}'" for k, v in sorted(self._aliases.items()))
        return "\n".join(lines), 0

    def cmd_unset(self, args):
        if not args:
            return "unset: missing variable", 1
        for var in args:
            self.env.vars.pop(var, None)
        return "", 0

    def cmd_source(self, args):
        if not args:
            return "source: missing file", 1
        success, content, error = self.fs.read_file(self._expand_path(args[0]))
        if success:
            return f"source: executed {args[0]}", 0
        return f"source: {args[0]}: No such file", 1

    def cmd_exit(self, args):
        code = int(args[0]) if args else 0
        return f"exit: logout (simulated, code {code})", code

    def cmd_return(self, args):
        return "", 0

    def cmd_break(self, args):
        return "", 0

    def cmd_continue(self, args):
        return "", 0

    def cmd_eval(self, args):
        if not args:
            return "", 0
        return self.execute(" ".join(args))

    def cmd_exec(self, args):
        if not args:
            return "exec: missing command", 1
        return f"exec: replaced shell with {args[0]}", 0

    def cmd_shift(self, args):
        return "", 0

    def cmd_test(self, args):
        # Simplified test command
        if len(args) >= 3 and args[1] == "=":
            return "", 0 if args[0] == args[2] else 1
        if args and args[0] in ("-z", "-n"):
            s = args[1] if len(args) > 1 else ""
            if args[0] == "-z":
                return "", 0 if not s else 1
            return "", 0 if s else 1
        return "", 0

    def cmd_true(self, args):
        return "", 0

    def cmd_false(self, args):
        return "", 1

    def cmd_seq(self, args):
        start, end, step = 1, 1, 1
        if len(args) == 1:
            end = int(args[0])
        elif len(args) == 2:
            start, end = int(args[0]), int(args[1])
        elif len(args) >= 3:
            start, step, end = int(args[0]), int(args[1]), int(args[2])
        return "\n".join(str(i) for i in range(start, end + 1, step)), 0

    def cmd_yes(self, args):
        text = "y" if not args else " ".join(args)
        return "\n".join([text] * 10), 0

    def cmd_factor(self, args):
        if not args:
            return "factor: missing number", 1
        try:
            n = int(args[0])
        except ValueError:
            return "factor: invalid number", 1
        factors = []
        d = 2
        while n > 1:
            while n % d == 0:
                factors.append(d)
                n //= d
            d += 1
            if d * d > n and n > 1:
                factors.append(n)
                break
        return f"{args[0]}: {' '.join(map(str, factors))}", 0

    def cmd_bc(self, args):
        return "bc: interactive calculator (simulated). Use 'echo 2+2 | bc'", 0

    def cmd_expr(self, args):
        if len(args) < 3:
            return "expr: missing expression", 1
        try:
            a, op, b = int(args[0]), args[1], int(args[2])
            if op == "+":
                return str(a + b), 0
            elif op == "-":
                return str(a - b), 0
            elif op == "*":
                return str(a * b), 0
            elif op == "/":
                return str(a // b if b != 0 else "expr: division by zero"), 0
            elif op == "%":
                return str(a % b), 0
        except (ValueError, ZeroDivisionError):
            return "expr: syntax error", 1
        return "expr: syntax error", 1

    def cmd_let(self, args):
        if not args:
            return "let: missing expression", 1
        try:
            expr = " ".join(args)
            if "=" in expr:
                var, val = expr.split("=", 1)
                self.env.set(var.strip(), str(eval(val.strip())))
                return "", 0
            return str(eval(expr)), 0
        except Exception:
            return "let: syntax error", 1

    def cmd_shuf(self, args):
        import random
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            lines = stdin_data.strip().split("\n")
            random.shuffle(lines)
            return "\n".join(lines), 0
        return "\n".join(str(i) for i in random.sample(range(1, 11), 10)), 0

    def cmd_xkcd(self, args):
        return "xkcd: https://xkcd.com/ - The best webcomic for developers!", 0

    # ====== PERMISSION COMMANDS ======

    def cmd_chmod(self, args):
        if len(args) < 2:
            return "chmod: missing operand", 1
        return "", 0

    def cmd_chown(self, args):
        err = self._require_root()
        if err:
            return err, 1
        if len(args) < 2:
            return "chown: missing operand", 1
        return f"chown: ownership of {args[1]} changed to {args[0]}", 0

    def cmd_chgrp(self, args):
        err = self._require_root()
        if err:
            return err, 1
        if len(args) < 2:
            return "chgrp: missing operand", 1
        return f"chgrp: group of {args[1]} changed to {args[0]}", 0

    def cmd_umask(self, args):
        if not args:
            return "0022", 0
        return "", 0

    # ====== FUN/MISC ======

    def cmd_help(self, args):
        help_text = """VirtualOS Shell - Available Commands (200+ commands):

File Operations:
  ls cd pwd cat touch mkdir rm rmdir cp mv ln rename file stat
  basename dirname realpath readlink

Text Processing:
  echo printf grep egrep fgrep sed awk cut paste tr wc
  head tail sort uniq diff cmp comm join split fold nl tac
  rev column fmt expand unexpand

System Info:
  ps kill killall pkill nice renice uname whoami who w uptime
  df du free top htop vmstat iostat lscpu lsblk lspci lsusb
  lshw lsmod lsof id groups hostname date cal time timeout

User/Privilege:
  sudo su passwd useradd userdel usermod groupadd groupdel
  chmod chown chgrp umask visudo

Process/Job Control:
  jobs bg fg nohup xargs wait

Network:
  ping ifconfig ip netstat ss route traceroute dig nslookup host
  wget curl scp rsync ssh ftp telnet nc nmap arp iwconfig ethtool

I/O:
  io iostat

Archive/Compression:
  tar zip unzip gzip gunzip bzip2 bunzip2 xz unxz 7z

Hash/Crypto:
  md5sum sha1sum sha256sum sha512sum base64 gpg

Package Management:
  apt apt-get dpkg yum rpm pacman pip pip3 npm gem cargo snap flatpak

System Management:
  systemctl service journalctl dmesg modprobe insmod rmmod
  mkfs mount umount fdisk parted fsck reboot shutdown poweroff halt init

Disk/Memory:
  dd sync swapon swapoff mkswap ionice fstrim

Find/Search:
  find locate updatedb which whereis whatis type

Editors:
  nano vim vi emacs ed

Terminal:
  clear reset tput stty tty script

Shell Builtins:
  alias unalias set unset env export source exit return
  break continue eval exec shift test true false
  seq yes factor bc expr let shuf

Fun/Misc:
  help man info apropos history neofetch screenfetch fastfetch
  cowsay cowthink fortune lolcat sl figlet toilet banner units
  look strings xxd hexdump od wall mesg write talk rig xkcd"""
        return help_text, 0

    def cmd_man(self, args):
        if not args:
            return "What manual page do you want?", 1
        cmd = args[0]
        return f"{cmd.upper()}(1)        VirtualOS Manual        {cmd.upper()}(1)\n\nNAME\n    {cmd} - VirtualOS {cmd} command\n\nSYNOPSIS\n    {cmd} [OPTIONS] [ARGUMENTS]\n\nDESCRIPTION\n    This is the VirtualOS simulated manual page for {cmd}.\n    Type 'help' for full command listing.", 0

    def cmd_info(self, args):
        return self.cmd_man(args)

    def cmd_apropos(self, args):
        if not args:
            return "apropos: missing keyword", 1
        return f"{args[0]} (1)  - VirtualOS command related to '{args[0]}'", 0

    def cmd_history(self, args):
        lines = []
        for i, cmd in enumerate(self.history[-50:], 1):
            lines.append(f"  {i:>4}  {cmd}")
        return "\n".join(lines), 0

    def cmd_neofetch(self, args):
        lines = [
            "        ╔══════════════════╗      " + f"\033[32m{self._current_user()}@{self.kernel.hostname}\033[0m",
            "        ║   ╔══════════╗   ║      " + "-" * 30,
            "        ║   ║  ╔══╗    ║   ║      " + f"\033[32mOS:\033[0m VirtualOS 1.0 x86_64",
            "        ║   ║  ╚══╝    ║   ║      " + f"\033[32mHost:\033[0m Virtual Machine",
            "        ║   ╚══════════╝   ║      " + f"\033[32mKernel:\033[0m {self.kernel.kernel_version}",
            "        ╚══════════════════╝      " + f"\033[32mUptime:\033[0m {self.kernel.get_uptime()}",
            "                                  " + f"\033[32mShell:\033[0m /bin/bash",
            f"                                  \033[32mResolution:\033[0m 1920x1080",
            f"                                  \033[32mDE:\033[0m VirtualDE 1.0",
            f"                                  \033[32mTerminal:\033[0m vterm",
            f"                                  \033[32mCPU:\033[0m VirtualOS CPU (4) @ 3.6GHz",
            f"                                  \033[32mMemory:\033[0m {self.mm.get_used_memory()//1024}MiB / {self.mm.total_kb//1024}MiB",
            f"                                  \033[32mUser:\033[0m {self._current_user()}",
        ]
        return "\n".join(lines), 0

    def cmd_screenfetch(self, args):
        return self.cmd_neofetch(args)

    def cmd_fastfetch(self, args):
        return self.cmd_neofetch(args)

    def cmd_cowsay(self, args):
        if not args:
            text = "Moo!"
        else:
            text = " ".join(args)
        border = "-" * (len(text) + 2)
        lines = [
            f" {border}",
            f"< {text} >",
            f" {border}",
            r"        \   ^__^",
            r"         \  (oo)\_______",
            "            (__))\\       )\\//",
            r"                ||----w |",
            r"                ||     ||",
        ]
        return "\n".join(lines), 0

    def cmd_cowthink(self, args):
        if not args:
            text = "Hmm..."
        else:
            text = " ".join(args)
        border = "o" * (len(text) + 2)
        lines = [
            f" {border}",
            f"( {text} )",
            f" {border}",
            r"        \   ^__^",
            r"         \  (oo)\_______",
            "            (__))\\       )\\//",
            r"                ||----w |",
            r"                ||     ||",
        ]
        return "\n".join(lines), 0

    def cmd_fortune(self, args):
        import random
        fortunes = [
            "The best way to predict the future is to invent it. - Alan Kay",
            "Talk is cheap. Show me the code. - Linus Torvalds",
            "Any sufficiently advanced technology is indistinguishable from magic. - Arthur C. Clarke",
            "There are only 10 types of people: those who understand binary and those who don't.",
            "The computer was born to solve problems that did not exist before. - Bill Gates",
            "First, solve the problem. Then, write the code. - John Johnson",
            "Code is like humor. When you have to explain it, it's bad. - Cory House",
            "Simplicity is the soul of efficiency. - Austin Freeman",
        ]
        return random.choice(fortunes), 0

    def cmd_lolcat(self, args):
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            return stdin_data, 0  # Color simulation not possible in Qt
        return "", 0

    def cmd_sl(self, args):
        return r"""      ====        ________                ___________
  _D _|  |_______/        \__I_I_____===__|_________|
   |(_)---  |   H\________/ |   |        =|___ ___|
   /     |  |   H  |  |     |   |         ||_| |_||
  |      |  |   H  |__--------------------| [___] |
  | ________|___H__/__|_____/[][]~\_______|       |
  |/ |   |-----------I_____I [][] []  D   |=======|_
__/ =| o |=-~~\  /~~\  /~~\  /~~\ ____Y___________|__
 |/-=|___|=O=====O=====O=====O   |_____/~\___/
  \_/      \__/  \__/  \__/  \__/      \_/""", 0

    def cmd_figlet(self, args):
        if not args:
            return "figlet: missing text", 1
        text = " ".join(args)
        # Simple ASCII art simulation
        lines = [f"  _{'_' * (len(text)-1)}_ ", f" / {text} \\", f" \ {text} /", f"  ‾{'‾' * (len(text)-1)}‾ "]
        return "\n".join(lines), 0

    def cmd_toilet(self, args):
        return self.cmd_figlet(args)

    def cmd_banner(self, args):
        return self.cmd_figlet(args)

    def cmd_units(self, args):
        if len(args) < 2:
            return "units: usage: units <value> <unit>", 1
        try:
            val = float(args[0])
        except ValueError:
            return "units: invalid number", 1
        unit = args[1].lower()
        conversions = {
            "m": f"{val}m = {val*3.28084:.2f}ft",
            "ft": f"{val}ft = {val*0.3048:.2f}m",
            "km": f"{val}km = {val*0.621371:.2f}mi",
            "mi": f"{val}mi = {val*1.60934:.2f}km",
            "kg": f"{val}kg = {val*2.20462:.2f}lb",
            "lb": f"{val}lb = {val*0.453592:.2f}kg",
            "c": f"{val}°C = {val*9/5+32:.2f}°F",
            "f": f"{val}°F = {(val-32)*5/9:.2f}°C",
        }
        return conversions.get(unit, f"units: unknown unit '{unit}'"), 0

    def cmd_look(self, args):
        if not args:
            return "look: missing string", 1
        return f"look: simulated dictionary lookup for '{args[0]}'", 0

    def cmd_strings(self, args):
        if not args:
            return "strings: missing file", 1
        return "VirtualOS\nHello World\n/bin/bash\n/usr/bin/env", 0

    def cmd_xxd(self, args):
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            lines = []
            for i in range(0, len(stdin_data), 16):
                chunk = stdin_data[i:i+16]
                hex_part = " ".join(f"{ord(c):02x}" for c in chunk)
                lines.append(f"{i:08x}: {hex_part:<48}  {chunk}")
            return "\n".join(lines), 0
        return "xxd: missing input", 0

    def cmd_hexdump(self, args):
        return self.cmd_xxd(args)

    def cmd_od(self, args):
        return self.cmd_xxd(args)

    def cmd_wall(self, args):
        return "wall: broadcast message sent (simulated)", 0

    def cmd_mesg(self, args):
        return "mesg: is y", 0

    def cmd_write(self, args):
        return "write: message sent (simulated)", 0

    def cmd_talk(self, args):
        return "talk: connection established (simulated)", 0

    def cmd_rig(self, args):
        import random
        names = ["John Smith", "Jane Doe", "Bob Johnson", "Alice Williams"]
        cities = ["New York", "London", "Tokyo", "Berlin"]
        return f"Name:    {random.choice(names)}\nAddress: {random.randint(100,999)} Main St\nCity:    {random.choice(cities)}\nPhone:   ({random.randint(100,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}", 0
