"""Build the demo-shop fixture used in the README and in evals/.

    python examples/make_demo_shop.py <target-dir>

Creates a tiny, deliberately sloppy Python webshop as a fresh git repo with
three commits (including a reverted "fix") and a committed fake .env. The
author, dates and line endings are fixed, so every run produces the same
commit hashes on every OS.

Requires git >= 2.28 and Python 3.8+. pytest is optional: if installed, the
script runs the fixture's single test as a self-check.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ORDERS_V1 = '''DB = {}

def create_order(user, items):
    total = 0
    for i in items:
        total += i["price"] * i["qty"]
    if total > 100:
        total = total * 0.9
    DB[len(DB)+1] = {"user": user, "items": items, "total": total, "status": "new"}
    return len(DB)

def refund(order_id):
    o = DB[order_id]
    o["status"] = "reversed"
    return o

def invoice_total(items):
    t = 0
    for i in items:
        t += i["price"] * i["qty"]
    if t > 100:
        t = t * 0.9
    return t
'''

API = '''from shop.orders import create_order, refund
def handle(req):
    if req["path"] == "/order":
        return {"id": create_order(req["user"], req["items"])}
    if req["path"] == "/chargeback":
        return refund(int(req["id"]))
    if req["path"] == "/debug":
        from shop.orders import DB
        return DB
'''

TEST = '''from shop.orders import create_order, DB
def test_create():
    oid = create_order("a", [{"price": 10, "qty": 2}])
    assert DB[oid]["total"] == 20
'''

FILES = {
    "shop/__init__.py": "",
    "shop/orders.py": ORDERS_V1,
    "shop/api.py": API,
    "tests/test_orders.py": TEST,
    # Deliberately committed. The value is fake and matches no real key format.
    ".env": "PAYMENT_KEY=demo-not-a-real-key\n",
    ".gitignore": "__pycache__/\n.pytest_cache/\n",
    "README.md": "# Demo shop\nTiny webshop. Run tests: python -m pytest\n",
}

# (message, ISO date, discount factor written to orders.py before committing)
COMMITS = [
    ("initial shop", "2026-01-05T09:00:00+00:00", None),
    ("fix discount", "2026-01-05T10:00:00+00:00", "0.85"),
    ('Revert "fix discount"', "2026-01-05T11:00:00+00:00", "0.9"),
]


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def write(target, rel, text):
    path = target / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def git(target, *args, env=None):
    subprocess.run(["git", *args], cwd=target, check=True, env=env,
                   stdout=subprocess.DEVNULL)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target", help="empty or non-existent directory")
    target = Path(parser.parse_args().target).resolve()

    if target == REPO_ROOT or REPO_ROOT in target.parents:
        fail(f"target is inside the unvibe repo ({REPO_ROOT}); pick a folder outside it")
    if target.exists() and any(target.iterdir()):
        fail(f"target is not empty: {target}")
    if shutil.which("git") is None:
        fail("git not found on PATH")

    target.mkdir(parents=True, exist_ok=True)
    for rel, text in FILES.items():
        write(target, rel, text)

    git(target, "init", "-q", "-b", "main")
    # Repo-local settings so global config can't change the hashes.
    for key, value in [("user.name", "demo"), ("user.email", "demo@example.com"),
                       ("core.autocrlf", "false"), ("commit.gpgsign", "false")]:
        git(target, "config", key, value)

    for message, date, factor in COMMITS:
        if factor is not None:
            write(target, "shop/orders.py", ORDERS_V1.replace("* 0.9", f"* {factor}"))
        env = {**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
        git(target, "add", "-A")
        git(target, "commit", "-q", "-m", message, env=env)

    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=target,
                          check=True, capture_output=True, text=True).stdout.strip()

    test = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                          cwd=target, capture_output=True, text=True)
    if test.returncode == 0:
        result = test.stdout.strip().splitlines()[-1]
    elif "No module named pytest" in test.stderr:
        result = "skipped (pytest not installed)"
    else:
        print(test.stdout + test.stderr, file=sys.stderr)
        fail("fixture self-test failed")

    print(f"demo-shop ready: {target}")
    print(f"HEAD: {head} | self-test: {result}")
    print("Next: open that folder in a new agent session and follow evals/README.md")


if __name__ == "__main__":
    main()
