"""Shell Commands - Linux command implementations for the virtual OS."""
import os
import re
import time
from datetime import datetime


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
        }

    def get(self, key, default=""):
        return self.vars.get(key, default)

    def set(self, key, value):
        self.vars[key] = value

    def export_all(self):
        return [f"{k}={v}" for k, v in sorted(self.vars.items())]


class ShellCommands:
    """Implements all Linux-like shell commands."""

    def __init__(self, kernel):
        self.kernel = kernel
        self.fs = kernel.filesystem
        self.pm = kernel.process_manager
        self.mm = kernel.memory_manager
        self.dm = kernel.device_manager
        self.env = ShellEnvironment()
        self.history = []
        self._aliases = {
            "ll": "ls -l",
            "la": "ls -a",
            "cls": "clear",
            "dir": "ls",
        }

    def execute(self, command_line):
        """Execute a command line string. Returns (output, exit_code)."""
        command_line = command_line.strip()
        if not command_line:
            return "", 0

        # Handle aliases
        first_word = command_line.split()[0]
        if first_word in self._aliases:
            command_line = command_line.replace(first_word, self._aliases[first_word], 1)

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

        # Command dispatch
        commands = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "pwd": self.cmd_pwd,
            "cat": self.cmd_cat,
            "touch": self.cmd_touch,
            "mkdir": self.cmd_mkdir,
            "rm": self.cmd_rm,
            "cp": self.cmd_cp,
            "mv": self.cmd_mv,
            "echo": self.cmd_echo,
            "find": self.cmd_find,
            "tree": self.cmd_tree,
            "ps": self.cmd_ps,
            "kill": self.cmd_kill,
            "uname": self.cmd_uname,
            "whoami": self.cmd_whoami,
            "uptime": self.cmd_uptime,
            "df": self.cmd_df,
            "free": self.cmd_free,
            "env": self.cmd_env,
            "export": self.cmd_export,
            "grep": self.cmd_grep,
            "wc": self.cmd_wc,
            "head": self.cmd_head,
            "tail": self.cmd_tail,
            "sort": self.cmd_sort,
            "uniq": self.cmd_uniq,
            "ping": self.cmd_ping,
            "ifconfig": self.cmd_ifconfig,
            "clear": self.cmd_clear,
            "help": self.cmd_help,
            "history": self.cmd_history,
            "date": self.cmd_date,
            "cal": self.cmd_cal,
            "chmod": self.cmd_chmod,
            "hostname": self.cmd_hostname,
            "id": self.cmd_id,
            "who": self.cmd_who,
            "top": self.cmd_top,
            "du": self.cmd_du,
            "man": self.cmd_man,
            "neofetch": self.cmd_neofetch,
            "cowsay": self.cmd_cowsay,
            "io": self.cmd_io,
            "iostat": self.cmd_iostat,
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
        # Pass output to second command as stdin (simplified)
        second_parts = self._parse_args(parts[1].strip())
        cmd = second_parts[0]
        args = second_parts[1:] + ["--stdin-data=" + output]
        commands = {
            "grep": self.cmd_grep,
            "wc": self.cmd_wc,
            "head": self.cmd_head,
            "tail": self.cmd_tail,
            "sort": self.cmd_sort,
            "uniq": self.cmd_uniq,
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
        # Execute command
        output, code = self.execute(cmd_part)
        if code != 0 and cmd_part.strip():
            return output, code
        # Write output to file
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
        # POSIX normalization (forward slashes only)
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
        results = []
        for arg in args:
            if arg.startswith("-n"):
                continue
            path = self._expand_path(arg)
            success, content, error = self.fs.read_file(path)
            if not success:
                results.append(error)
                continue
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

    def cmd_rm(self, args):
        recursive = "-r" in args or "-R" in args or "--recursive" in args
        force = "-f" in args or "--force" in args
        files = [a for a in args if not a.startswith("-")]
        if not files:
            return "rm: missing operand", 1
        for f in files:
            path = self._expand_path(f)
            success, error = self.fs.rm(path, recursive=recursive)
            if not success and not force:
                return error, 1
        return "", 0

    def cmd_cp(self, args):
        recursive = "-r" in args or "-R" in args
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
        src_args = [a for a in args if not a.startswith("-")]
        if len(src_args) < 2:
            return "mv: missing operand", 1
        src = self._expand_path(src_args[0])
        dest = self._expand_path(src_args[1])
        success, error = self.fs.mv(src, dest)
        if not success:
            return error, 1
        return "", 0

    def cmd_echo(self, args):
        text = " ".join(args)
        # Expand variables
        for var, val in self.env.vars.items():
            text = text.replace(f"${var}", val)
            text = text.replace(f"${{{var}}}", val)
        return text, 0

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
            i += 1
        success, results, error = self.fs.find(path, name=name_filter, type_=type_filter)
        if not success:
            return error, 1
        return "\n".join(results), 0

    def cmd_tree(self, args):
        path = self.fs.get_cwd()
        if args and not args[0].startswith("-"):
            path = self._expand_path(args[0])
        success, lines, error = self.fs.tree(path)
        if not success:
            return error, 1
        return "\n".join(lines), 0

    # ====== SYSTEM COMMANDS ======

    def cmd_ps(self, args):
        full = "-f" in args or "--full" in args
        procs = self.pm.get_all_processes()
        if not full:
            lines = ["PID    PPID   STAT  COMMAND"]
            lines.append("-" * 50)
            for p in procs:
                lines.append(f"{p.pid:<7}{p.ppid:<7}{p.state[:4]:<6}{p.command}")
        else:
            lines = ["UID      PID    PPID   STAT  COMMAND"]
            lines.append("-" * 60)
            for p in procs:
                lines.append(f"{p.user:<9}{p.pid:<7}{p.ppid:<7}{p.state[:4]:<6}{p.command}")
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
        return self.env.get("USER", "user"), 0

    def cmd_uptime(self, args):
        now = datetime.now().strftime("%H:%M:%S")
        return f" {now} up {self.kernel.get_uptime()},  1 user,  load average: 0.15, 0.10, 0.05", 0

    def cmd_df(self, args):
        human = "-h" in args
        used = self.mm.get_used_memory()
        free = self.mm.get_free_memory()
        total = self.mm.total_kb
        lines = ["Filesystem          1K-blocks      Used Available Use% Mounted on"]
        lines.append(f"/dev/virt-disk       {total:>10}  {used:>10}  {free:>10}  {int(used/total*100):>3}% /")
        lines.append(f"tmpfs              {total//4:>10}    {(total//4-used//10):>10}  {total//4:>10}    1% /tmp")
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

    # ====== TEXT COMMANDS ======

    def cmd_grep(self, args):
        pattern = None
        file_path = None
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
            elif not pattern:
                pattern = a
            elif not file_path:
                file_path = self._expand_path(a)
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
        results = [line for line in lines if re.search(pattern, line)]
        return "\n".join(results), 0

    def cmd_wc(self, args):
        stdin_data = None
        files = []
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
            else:
                files.append(self._expand_path(a))
        if stdin_data:
            content = stdin_data
        elif files:
            success, content, error = self.fs.read_file(files[0])
            if not success:
                return error, 1
        else:
            return "wc: missing input", 1
        lines = content.count("\n")
        words = len(content.split())
        chars = len(content)
        return f"  {lines}  {words} {chars}", 0

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
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            lines = sorted(stdin_data.strip().split("\n"))
            return "\n".join(lines), 0
        return "", 0

    def cmd_uniq(self, args):
        stdin_data = None
        for a in args:
            if a.startswith("--stdin-data="):
                stdin_data = a.split("=", 1)[1]
        if stdin_data:
            lines = stdin_data.strip().split("\n")
            seen = []
            for line in lines:
                if line not in seen:
                    seen.append(line)
            return "\n".join(seen), 0
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

    # ====== MISC COMMANDS ======

    def cmd_clear(self, args):
        return "__CLEAR__", 0

    def cmd_help(self, args):
        help_text = """VirtualOS Shell - Available Commands:

File Operations:
  ls [-l] [-a] [-h] [path]    List directory contents
  cd [path]                   Change directory
  pwd                         Print working directory
  cat <file>                  Display file contents
  touch <file>                Create empty file
  mkdir [-p] <dir>            Create directory
  rm [-r] [-f] <file>         Remove file/directory
  cp [-r] <src> <dest>        Copy file/directory
  mv <src> <dest>             Move/rename file
  find [path] [-name] [-type]  Search for files
  tree [path]                 Display directory tree
  du [path]                   Disk usage

System:
  ps [-f]                     List processes
  kill [-signal] <pid>        Terminate process
  top                         Interactive process viewer
  uname [-a]                  System information
  whoami                      Current user
  uptime                      System uptime
  df [-h]                     Disk space
  free [-h]                   Memory usage
  hostname                    Show/set hostname

Text Processing:
  echo <text>                 Print text
  grep <pattern> [file]       Search text
  wc                          Word/line/char count
  head [-n]                   First N lines
  tail [-n]                   Last N lines
  sort                        Sort lines
  uniq                        Remove duplicates

Network:
  ping [-c count] <host>      Ping host
  ifconfig                    Network interfaces

Other:
  env                         Environment variables
  export KEY=value            Set environment variable
  date                        Current date/time
  cal                         Calendar
  history                     Command history
  clear                       Clear screen
  help                        Show this help
  neofetch                    System info display
  man <cmd>                   Manual page

I/O:
  io <device> <type> [data]   Send I/O request
  iostat                      I/O request status"""
        return help_text, 0

    def cmd_history(self, args):
        lines = []
        for i, cmd in enumerate(self.history[-20:], 1):
            lines.append(f"  {i:>4}  {cmd}")
        return "\n".join(lines), 0

    def cmd_date(self, args):
        if "%s" in args:
            return str(int(time.time())), 0
        return datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y"), 0

    def cmd_cal(self, args):
        now = datetime.now()
        year = now.year
        month = now.month
        if len(args) >= 2:
            month, year = int(args[0]), int(args[1])
        elif len(args) == 1:
            year = int(args[0])
        cal_lines = []
        cal_lines.append(f"    {now.strftime('%B')} {year}")
        cal_lines.append("Su Mo Tu We Th Fr Sa")
        first_day = datetime(year, month, 1).weekday()
        days_in_month = (datetime(year, month + 1, 1) - datetime(year, month, 1)).days if month < 12 else 31
        line = "   " * (first_day + 1) if first_day < 6 else ""
        for day in range(1, days_in_month + 1):
            pos = (first_day + day) % 7
            if pos == 0 and day > 1:
                cal_lines.append(line.rstrip())
                line = ""
            line += f"{day:>3}"
            if day == now.day and month == now.month:
                line = line[:-3] + f"{day:>3}"
        if line:
            cal_lines.append(line.rstrip())
        return "\n".join(cal_lines), 0

    def cmd_chmod(self, args):
        if len(args) < 2:
            return "chmod: missing operand", 1
        return "", 0

    def cmd_hostname(self, args):
        if args:
            self.kernel.hostname = args[0]
            self.env.set("HOSTNAME", args[0])
        return self.kernel.hostname, 0

    def cmd_id(self, args):
        return "uid=1000(user) gid=1000(user) groups=1000(user),27(sudo)", 0

    def cmd_who(self, args):
        return "user     tty0         2026-01-01 00:00 (:0)", 0

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

    def cmd_man(self, args):
        if not args:
            return "What manual page do you want?", 1
        cmd = args[0]
        help_text = self.cmd_help([])[0]
        if cmd in help_text:
            return f"{cmd}(1) - VirtualOS Manual\n\nSee 'help' for {cmd} usage", 0
        return f"No manual entry for {cmd}", 1

    def cmd_neofetch(self, args):
        lines = [
            "        ╔══════════════════╗      " + f"\033[32m{self.env.get('USER', 'user')}@{self.kernel.hostname}\033[0m",
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
        ]
        return "\n".join(lines), 0

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

    @staticmethod
    def _human_size(size):
        for unit in ['B', 'K', 'M', 'G']:
            if size < 1024:
                return f"{size}{unit}"
            size /= 1024
        return f"{size:.1f}T"
