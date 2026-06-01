import pygit2
from pathlib import Path
import json
from blake3 import blake3

# Hashes the committed git blob bytes (what GitHub raw serves), NOT the
# working-tree files — avoids CRLF mismatches on Windows (autocrlf=true).

def walk_tree(repo, tree, parent=Path("")):
    for e in tree:
        path = parent / e.name
        obj = repo[e.id]
        if isinstance(obj, pygit2.Tree):
            yield from walk_tree(repo, obj, path)
        else:
            yield path, obj  # blob

def main():
    with open("index_base.json", encoding="utf-8") as f:
        index = json.load(f)
    index["files"] = []

    repo = pygit2.Repository('.')
    tree = repo.revparse_single('HEAD').tree
    ld_tree = None
    for e in tree:
        if e.name == "localized_data" and isinstance(repo[e.id], pygit2.Tree):
            ld_tree = repo[e.id]
            break
    if not ld_tree:
        print("[Error] localized_data tree not found")
        return

    for path, blob in walk_tree(repo, ld_tree):
        if path.name == ".gitignore":
            continue
        data = blob.data
        index["files"].append({
            'path': path.as_posix(),
            'hash': blake3(data).hexdigest(),
            'size': len(data),
        })

    with open("index.json", "w", encoding="utf-8", newline='\n') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print("files indexed:", len(index["files"]))

main()
