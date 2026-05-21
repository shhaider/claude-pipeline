# Concurrent Work Addendum

This addendum applies when a gate run executes alongside an autonomous agent or other concurrent work on the same repo or shared resources.

Checks required by this addendum:
- concurrent agents/processes must be identified by PID and command at task start;
- no `kill`, `pkill`, `killall`, `systemctl stop`, or other process-disrupting command may be issued without explicit user go-ahead;
- worktree files modified or untracked by the concurrent agent must be classified and left alone unless the brief explicitly authorizes touching them;
- any commit on a branch the concurrent agent is using must be surgical (verified via git show --stat HEAD); commit must touch only the file(s) the brief authorizes;
- post-task verification must confirm the concurrent agent's processes are still running and that the agent's branch HEAD has continued to evolve naturally.
