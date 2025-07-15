# Git Lab Assignment: Kestrel-1 Rover, Share the Code

**Course:** 26RA2308 Git for Software Development and Collaboration
**Builds on:** Experiments 1 to 8. **Based on:** Experiment 9 (Push and Pull Operations with GitHub)
**Time allowed:** 1 hour. **Marks:** 100

---

## The story

It is Monday 09:00 at the Kestrel-1 rover lab. Until now the rover code lived only on the lab laptop. **Asha** and
**Chitra** work from home and fix small things straight on the GitHub website, so the team needs one shared copy on
GitHub, and you are the one who sets it up and keeps it in sync. The lab has one rule:

> **Never overwrite what is on GitHub.** If GitHub has work you do not have, you bring it down first.

In the next hour you connect the project to your own GitHub repository (`git remote`, `git push -u`), see the
difference between looking at GitHub's changes and taking them (`git fetch`, `git pull`), run into a rejected push and
solve it the right way (`git pull --rebase`), publish a feature branch, and check that everything is in sync. Along the
way you reuse `git config` and aliases (Experiment 3), `git commit` (Experiments 4 and 5), `git log`, `git status` and
`git diff` (Experiment 6), branches (Experiment 7), the `A..B` ranges of Experiment 8 and the terminal skills from
Experiments 1 and 2.

## What you need

`git`, `python3` and a free **GitHub account**. Your SSH key from Experiment 3 must be added to that account: check
with `ssh -T git@github.com` (it says `Hi <your-username>! You've successfully authenticated`). If your terminal does not
print English messages, run `export LC_ALL=C` first, because the grader reads what Git prints. If a long output opens in
a pager (a screen with `:` or `(END)` at the bottom), press `q` to leave it.

## How to change a file on github.com

Two steps of this lab ask you to change a file in the browser, as Asha and Chitra do.

1. Open your repository on github.com and click the file named in the step (for example `README.md`).
2. Click the **pencil** icon (Edit this file).
3. Press `Ctrl+End` to jump to the end of the file. If the cursor is at the end of a line of text, press `Enter` once.
   Type the line shown in the step.
4. Click **Commit changes...**. Replace the message in the box with the message shown in the step, keep
   **Commit directly to the main branch**, and click **Commit changes**.

A message typed wrongly on github.com cannot be changed afterwards. Carry on: you lose only the checks that read it.

## Rules

1. Work **only inside your own clone**. You stay on `main`, except in Task 4, which makes a branch and ends back on `main`.
2. Push **only to `origin`**, your own GitHub repository. Never use `--force` (or `-f`) and never use `git reset`.
3. Type the commands yourself. The grader checks that your pasted output matches what is really in your repository
   (your commit numbers, and the commits GitHub made for you), so output copied from a classmate is detected.
4. Keep the commit messages and the lines you type on github.com exactly as written.

## How you hand in your work

1. In Task 1 you copy `submission/outputs.template.txt` to `submission/outputs.txt`.
2. After **each step** (numbered **1.1**, **1.2**, ...), paste what the terminal printed under the matching
   `--- N.M` line of `submission/outputs.txt`, replacing `(paste output here)`. Do not edit or delete the
   `=== TASK` and `--- N.M` lines. Type your answers after the colon of the `ANSWER-n :` lines (the line just
   below each `# Qn` question). Any editor is fine for `submission/outputs.txt`.
3. Fill in your name and registration number at the top of the file.
4. Run the automatic grader whenever you want to see where you stand:

   ```bash
   python3 tests/grade.py
   ```

   It prints **PASS** or **FAIL** for every task, tells you exactly which check failed, and shows your score out
   of 100. You can fix a mistake and run it again as often as you like. The grader never uses the internet: it reads
   your clone.
5. When you are done, show the final grader output to your instructor (it is also saved in
   `submission/results.txt`), and submit `submission/outputs.txt` as instructed. The file is not pushed to GitHub on
   purpose: `.gitignore` keeps it local.

## Time plan

| Task | Time on the clock | Topic | Suggested time | Marks |
|---|---|---|---|---|
| 1 | 09:00 | Connect to GitHub | 12 min | 20 |
| 2 | 09:12 | Fetch, then pull | 10 min | 25 |
| 3 | 09:22 | A rejected push | 14 min | 30 |
| 4 | 09:36 | Publish a feature branch | 8 min | 15 |
| 5 | 09:44 | Wrap up | 4 min | 10 |
| | | Buffer for running the grader and fixing mistakes | 12 min | |

**Skipped a task, or running behind?** You do not lose the rest of the lab. A **catch-up box** at the start of the next
task brings your clone to the state you need, in one to six lines. If you skipped several tasks, run their boxes in
order. You lose only the marks of the task you skipped.

---

## Task 1: Connect to GitHub (20 marks)

Get the project, tell Git who you are, and move the project to your own GitHub repository.

```bash
git clone https://github.com/qbit-glitch/26RA2308-gitlab-9-rover-push-pull-lab.git \
    rover-push-pull-lab
cd rover-push-pull-lab
cp submission/outputs.template.txt submission/outputs.txt
git config user.name "Your Full Name"
git config user.email "your.email@example.com"
git config alias.tree "log --oneline --graph --decorate --all"
git config pull.rebase false
git remote rename origin upstream
```

Use your own real name and e-mail (not the placeholders above, and not one of the teammates'). Do **not** use
`--global` here. `pull.rebase false` pins the one setting that changes what `git pull` does. The clone's `origin`
points at the **course** repository; renaming it to `upstream` frees the name `origin` for **your own** repository.
Your instructor may give you a different clone URL.

Now, in the browser: sign in to github.com, click **New repository**, call it `rover-push-pull-lab`, leave everything
else empty (**no** README, **no** .gitignore, **no** license) and click **Create repository**. Copy its SSH address.
Then, back in the terminal (replace `YOUR-USERNAME` with your GitHub user name):

```bash
git remote add origin git@github.com:YOUR-USERNAME/rover-push-pull-lab.git
git remote -v
```

* **1.1** Paste the output of `git remote -v`. Each remote is listed twice (fetch and push): `upstream` is the course
  repository, `origin` is yours.

```bash
git push -u origin main
```

* **1.2** Paste the output. `* [new branch]` means GitHub did not have `main` yet. The option `-u` makes your local
  `main` remember that it goes with `origin/main`.

```bash
git branch -vv
```

* **1.3** Paste the output. The word in square brackets is the branch that `main` is tracking.
* Then type your answer to `ANSWER-1` in the file (there is no pasted output for it): which remote name now points to
  the course repository?

## Task 2: Fetch, then pull (25 marks)

Asha fixes the README from her phone. In the browser, change `README.md` of **your** repository as described in the
box "How to change a file on github.com": add the line below at the end and commit it with the message below.

```text
Contact the team: rover-team@example.com
```

```text
docs: add team contact line
```

*Needs:* the push of Task 1.

> **Catch-up box: only if you skipped Task 1.** Run this one line, once. It does what step 1.2 does. If you did
> Task 1, do **not** run it. There is nothing to paste for it, and you lose only the marks of Task 1.
>
> ```bash
> git push -u origin main
> ```

First only **look**: `git fetch` downloads what GitHub has and updates `origin/main`, but it does not touch your
files or your `main`.

```bash
git fetch origin
```

* **2.1** Paste the output. The line `<old>..<new>  main -> origin/main` is the new commit arriving.

```bash
git status
```

* **2.2** Paste the output. Find `behind 'origin/main' by 1 commit`.

```bash
git diff main origin/main
```

* **2.3** Paste the output. It shows exactly what the commit made on GitHub changes in `README.md`.

Now **take** it: `git pull` is a fetch followed by a merge. Your `main` has nothing GitHub lacks, so the merge only
moves `main` forward.

```bash
git pull origin main
```

* **2.4** Paste the output. Read the word `Fast-forward`.

## Task 3: A rejected push (30 marks)

Now Chitra adds a note, again on the website. In the browser, change `NOTES.txt` of **your** repository: add the line
below at the end and commit it with the message below.

```text
- Field team: log every test run in CHANGELOG.md.
```

```text
docs: add field team note
```

**Do not** run `git fetch` or `git pull` yet: your laptop has no idea that GitHub moved. Meanwhile you make your own
commit on the laptop (a different file, so nothing can clash). `-a` stages every change to a tracked file and `-m`
gives the message.

*Needs:* the pull of Task 2.

> **Catch-up box: only if you skipped Task 2.** In the browser, make the `README.md` change of Task 2 (the line and
> the message shown there), **before** the change above. Then run this one line, once. If you did Task 2, do **not**
> run it. There is nothing to paste for it, and you lose only the marks of Task 2.
>
> ```bash
> git pull origin main
> ```

```bash
echo "- 0.3: calibrate the left turn" >> CHANGELOG.md
git commit -am "docs: log left turn calibration"
```

* **3.1** Paste the output of the `git commit` command.

```bash
git push origin main
```

* **3.2** Paste the output. It is **supposed to be rejected**: `! [rejected]` and `(fetch first)`. GitHub has a commit
  that you do not have, and Git will not let you overwrite it. Never "fix" this with `--force`.

The right answer: bring GitHub's commit down, and put your commit **on top of it**. `--rebase` replays your commit after
the commit from GitHub, so history stays one straight line.

```bash
git pull --rebase origin main
```

* **3.3** Paste the output. It ends with `Successfully rebased and updated refs/heads/main.`

```bash
git tree
```

* **3.4** Paste the output (your alias). Your commit is on top, with `origin/main` (the commit from GitHub) just under it.
  Your commit has a **new number** now: a rebase makes a new commit.

```bash
git push origin main
```

* **3.5** Paste the output. This time it works: `<old>..<new>  main -> main`.
* Then type your answer to `ANSWER-2` in the file: the commit number (at least 7 characters) printed next to
  `origin/main` in 3.4, the commit that GitHub made, `docs: add field team note`.

## Task 4: Publish a feature branch (15 marks)

Make a branch for the turn calibration, commit on it, and publish it.

*Needs:* the push of Task 3.

> **Catch-up box: only if you skipped Task 3.** In the browser, make the `NOTES.txt` change of Task 3 (the line and
> the message shown there). Then run these four lines, once, on `main`. They do what Task 3 does. If you did Task 3,
> do **not** run them. There is nothing to paste for them, and you lose only the marks of Task 3. (If you skipped
> Task 2 as well, run its box first.)
>
> ```bash
> echo "- 0.3: calibrate the left turn" >> CHANGELOG.md
> git commit -am "docs: log left turn calibration"
> git pull --rebase origin main
> git push origin main
> ```

```bash
git switch -c feature/turn-calibration
echo "def calibrate_turn(): pass" > calibrate_turn.py
git add calibrate_turn.py
git commit -m "feat(control): add turn calibration stub"
git push -u origin feature/turn-calibration
```

* **4.1** Paste the output of the `git push` command. `-u` again links the local branch to its GitHub twin.

```bash
git branch -vv
```

* **4.2** Paste the output. Both branches show the remote branch they track.

```bash
git remote show origin
```

* **4.3** Paste the output. This one asks GitHub itself: which branches it has, and what `git pull` and `git push`
  would do for each of yours.

## Task 5: Wrap up (10 marks)

Go back to `main` and check that your laptop and GitHub agree.

*Needs:* the branch of Task 4.

> **Catch-up box: only if you skipped Task 4.** Run these six lines, once. They do what Task 4 does and put you back
> on `main`. If you did Task 4, do **not** run them. There is nothing to paste for them, and you lose only the marks of
> Task 4.
>
> ```bash
> git switch -c feature/turn-calibration
> echo "def calibrate_turn(): pass" > calibrate_turn.py
> git add calibrate_turn.py
> git commit -m "feat(control): add turn calibration stub"
> git push -u origin feature/turn-calibration
> git switch main
> ```

```bash
git switch main
git status
```

* **5.1** Paste the output of `git status`. `main` is up to date with `origin/main`.

```bash
git branch -r
```

* **5.2** Paste the output. These are your remote-tracking branches: Git's last known copy of each branch on each remote.
  You cannot commit on them; only a fetch, pull or push moves them.

```bash
git log --oneline upstream/main..main
```

* **5.3** Paste the output (the `A..B` range from Experiment 8): the commits that `main` has and the course repository
  does not.
* Then type your answer to `ANSWER-3` in the file: how many commits is that?

## Finish

```bash
python3 tests/grade.py
```

You want to see `PASS` for all five tasks and `TOTAL: 100/100`. Anything marked `FAIL` is listed with the reason; fix
it and run the grader again.

## Marks

| Task | Marks | How it is checked |
|---|---|---|
| 1 | 20 | the two remotes, the push with `-u` and the tracking branch are pasted; your identity, your own GitHub address and the tracking are real in your clone |
| 2 | 25 | fetch, status, diff and the fast-forward pull are pasted; the commit GitHub made is really on `main`, and the reflogs show a fetch and a pull |
| 3 | 30 | the commit, the rejected push, the rebase, the straight graph and the accepted push are pasted; your commit really sits on top of GitHub's commit with a new number, with no merge commit; one answer |
| 4 | 15 | the push, `branch -vv` and `remote show` are pasted; the branch really tracks its GitHub twin and holds the commit |
| 5 | 10 | the status, the remote-tracking branches and the range are pasted; `main` equals `origin/main` and is exactly 3 commits above the course; one answer |

A task shows **PASS** only when every check in it passes, and you earn marks for each check that passes even if the
task as a whole fails.

## If something goes wrong

* **You skipped a task and a later one fails.** Run the catch-up box at the start of the task after the one you
  skipped (in order, if you skipped several), then carry on.
* **`Permission denied (publickey)`.** GitHub does not know your SSH key. Redo the key step of Experiment 3 (add the
  `.pub` file under GitHub, Settings, SSH keys), check with `ssh -T git@github.com`, then push again. Without a key you can
  use the HTTPS address of your repository instead (`https://github.com/YOUR-USERNAME/rover-push-pull-lab.git`, with a
  personal access token as the password): `git remote set-url origin <address>`.
* **`error: remote origin already exists`.** The clone's `origin` is still the course repository. Run
  `git remote rename origin upstream`, then `git remote add origin ...` again.
* **Step 1.2 is rejected, or says `remote contains work`.** You created the GitHub repository with a README or a
  licence, so it is not empty. Delete it (Settings, at the bottom), create it again empty, and push again.
* **Step 3.2 was not rejected.** You ran `git fetch` or `git pull` after the change on github.com, or the change on the
  website was not committed. Make sure the `NOTES.txt` commit is on github.com, and that your laptop has not seen it
  (a fetch would show it). If your laptop already knows it, `git pull --rebase origin main` first, then do 3.1 to 3.5
  with a new commit message line in `CHANGELOG.md`; you lose only the check that reads the rejection.
* **`git pull --rebase` stops and says `CONFLICT`.** You edited a file that GitHub also changed (`README.md` or
  `NOTES.txt`). Run `git rebase --abort`, then `git status` and ask your instructor.
* **An editor opened and asked for a commit message.** You left out `-m "..."`. Save and exit (nano: `Ctrl+O`,
  `Enter`, `Ctrl+X`; vim: `Esc`, then `:wq` and `Enter`). Then fix the message with
  `git commit --amend -m "<the message from the step>"` (before you push).
* **`tests/grade.py` says it cannot find the starting commit.** You are not inside your clone: `cd rover-push-pull-lab`.
