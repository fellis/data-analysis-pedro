import json

NEW_ZIP_CELL = r'''import zipfile
import shutil
import tempfile

# Input: zip file name (in ROOT_DATA or cwd), or Colab upload, or env PROVIDER_ZIP
INPUT_ZIP = "Archive.zip"

# Folders to keep when cleaning (do not delete)
KEEP_DIRS = {"provider_structures", "provider_mappings", "output"}

def clean_workspace(root: Path) -> None:
    """Remove provider data dirs and files under root; keep KEEP_DIRS."""
    for item in root.iterdir():
        if item.name.startswith("."):
            continue
        if item.is_dir():
            if item.name in KEEP_DIRS:
                continue
            shutil.rmtree(item)
            print("Removed dir:", item.name)
        else:
            item.unlink()
            print("Removed file:", item.name)

def remove_junk_files(root: Path) -> None:
    """Remove __MACOSX and all ._* files/dirs (macOS metadata) under root."""
    macosx = root / "__MACOSX"
    if macosx.exists():
        shutil.rmtree(macosx)
        print("Removed __MACOSX")
    removed = 0
    for path in sorted(root.rglob(".*"), key=lambda p: -len(p.parts)):
        if path.name.startswith("._"):
            if path.is_file():
                path.unlink()
                removed += 1
            elif path.is_dir() and not any(path.iterdir()):
                path.rmdir()
                removed += 1
    if removed:
        print("Removed", removed, "junk files (._*)")

def get_zip_path() -> str:
    """Return path to the zip: Colab upload, or INPUT_ZIP / PROVIDER_ZIP in ROOT_DATA or cwd."""
    if IN_COLAB:
        from google.colab import files
        uploaded = files.upload()
        if not uploaded:
            raise RuntimeError("No file uploaded. Run the cell and choose a zip (e.g. Archive.zip).")
        name = list(uploaded.keys())[0]
        if not name.lower().endswith(".zip"):
            raise RuntimeError("Upload a .zip file.")
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        tmp.write(uploaded[name])
        tmp.close()
        return tmp.name
    zip_name = os.environ.get("PROVIDER_ZIP", INPUT_ZIP)
    path = Path(zip_name)
    if not path.is_absolute():
        for base in (ROOT_DATA, Path.cwd()):
            candidate = base / zip_name
            if candidate.exists():
                return str(candidate)
        raise FileNotFoundError(f"ZIP not found: {zip_name}. Place {INPUT_ZIP} in project dir or set PROVIDER_ZIP.")
    if not path.exists():
        raise FileNotFoundError(f"ZIP not found: {path}")
    return str(path)

def unzip_and_flatten(zip_path: str, root: Path) -> None:
    """Extract zip to root. If single top-level dir (not in KEEP_DIRS), move its contents up."""
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(root)
    subdirs = [d for d in root.iterdir() if d.is_dir() and d.name not in KEEP_DIRS and not d.name.startswith(".")]
    if len(subdirs) == 1:
        single = subdirs[0]
        for child in single.iterdir():
            dest = root / child.name
            if dest.exists():
                shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
            shutil.move(str(child), str(root))
        single.rmdir()
        print("Flattened single root folder:", single.name)

# 1) Clean workspace (keep provider_structures, provider_mappings, output)
print("Cleaning workspace...")
clean_workspace(ROOT_DATA)
# 2) Resolve and unzip input (Archive.zip or upload)
zip_path = get_zip_path()
print("Extracting:", zip_path)
unzip_and_flatten(zip_path, ROOT_DATA)
# 3) Remove junk: __MACOSX and ._* files
remove_junk_files(ROOT_DATA)
print("Done. Provider folders:", [p.name for p in ROOT_DATA.iterdir() if p.is_dir() and not p.name.startswith(".")])
'''

def main():
    with open("provider_evaluation.ipynb") as f:
        nb = json.load(f)
    # Cell at index 3 is the zip cell
    lines = NEW_ZIP_CELL.strip().split("\n")
    source = [line + "\n" for line in lines[:-1]]
    if lines:
        source.append(lines[-1])
    nb["cells"][3]["source"] = source
    with open("provider_evaluation.ipynb", "w") as f:
        json.dump(nb, f, indent=1)
    print("Patched cell 3 (zip cell).")

if __name__ == "__main__":
    main()
