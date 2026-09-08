# Git and GitHub

Two small experiments, run in a scratch repository, with the real output pasted in.

## Experiment 1 - `git commit -m` versus `git commit -a -m`

The difference is entirely about the staging area (index).

- `git commit -m "msg"` records whatever is in the index. If you edited a file but never ran
  `git add`, the edit is not part of the commit.
- `git commit -a -m "msg"` first stages every *tracked* file that has been modified or deleted,
  then commits. It saves the separate `git add` step for files git already knows about.
- Neither form touches *untracked* files. A brand-new file always needs an explicit `git add`.

### Session

```text
$ git init -q -b main .
$ echo "todo: learn git" > todo.txt
$ git add todo.txt
$ git commit -q -m "first version of todo" && git log --oneline
b21df8a first version of todo

$ echo "todo: practice -a flag" >> todo.txt
$ git status -s
 M todo.txt

$ git commit -m "commit without -a"
On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   todo.txt

no changes added to commit (use "git add" and/or "git commit -a")

$ git commit -a -m "commit with -a picks up the tracked change"
[main c4a5678] commit with -a picks up the tracked change
 1 file changed, 1 insertion(+)

$ echo "new file" > untracked.txt
$ git status -s
?? untracked.txt

$ git commit -a -m "does -a include untracked?"
On branch main
Untracked files:
  (use "git add <file>..." to include in what will be committed)
	untracked.txt

nothing added to commit but untracked files present (use "git add" to track)

$ git log --oneline
c4a5678 commit with -a picks up the tracked change
b21df8a first version of todo
```

### Takeaways

1. The first `git commit -m` did nothing because the modification was only in the working tree.
2. `-a` staged and committed the same modification in one step.
3. `-a` refused to pick up `untracked.txt`. Git tells you so in the message.

## Experiment 2 - `git cherry-pick`

Cherry-pick replays one commit from anywhere in the repository on top of the current branch.
It creates a *new* commit with the same diff and message; the original stays where it was.
Useful when a branch has one change you want now and several you do not.

### Setup: a `hotfix` branch with three commits

```text
$ echo "config v1" > config.txt && git add config.txt && git commit -q -m "Add config"
$ git switch -c hotfix
Switched to a new branch 'hotfix'

$ echo "logging on" > logging.txt && git add logging.txt && git commit -q -m "hotfix: enable logging"
$ echo "config v1 + port fix" > config.txt && git commit -q -a -m "hotfix: correct the port in config"
$ echo "temp debug" > debug.txt && git add debug.txt && git commit -q -m "hotfix: temporary debug file"

$ git log --oneline
739b55e hotfix: temporary debug file
ee4e5bf hotfix: correct the port in config
4a15a5f hotfix: enable logging
01e35a0 Add config
c4a5678 commit with -a picks up the tracked change
b21df8a first version of todo
```

Only the middle commit (`ee4e5bf`, the port fix) is wanted on `main`. The logging change and
the debug file should stay on the branch.

### Pick just that commit

```text
$ git switch main
Switched to branch 'main'

$ git cherry-pick ee4e5bf
[main 2e12fe7] hotfix: correct the port in config
 Date: Thu Sep 3 00:19:23 2026 +0530
 1 file changed, 1 insertion(+), 1 deletion(-)

$ git log --oneline
2e12fe7 hotfix: correct the port in config
01e35a0 Add config
c4a5678 commit with -a picks up the tracked change
b21df8a first version of todo

$ ls
config.txt
todo.txt
untracked.txt

$ cat config.txt
config v1 + port fix
```

### Takeaways

- `main` now has the port fix, but neither `logging.txt` nor `debug.txt` exists there.
- The picked commit got a new hash (`2e12fe7` vs `ee4e5bf`) because it has a different parent,
  even though the message and diff are identical. Git kept the original author date.
- If the pick conflicts, git stops and you resolve the files, then `git cherry-pick --continue`
  (or `--abort` to back out).
- Handy variants: `git cherry-pick A..B` for a range, `-n` to apply without committing,
  `-x` to append "(cherry picked from commit ...)" to the message for traceability.
