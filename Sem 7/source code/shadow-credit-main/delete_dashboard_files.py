import os

files = [
    r"d:\Fintech project\shadow-credit\frontend\app\dashboard\layout.tsx",
    r"d:\Fintech project\shadow-credit\frontend\app\dashboard\page.tsx"
]

for f in files:
    try:
        if os.path.exists(f):
            os.remove(f)
            print(f"Deleted: {f}")
        else:
            print(f"Not found: {f}")
    except Exception as e:
        print(f"Error deleting {f}: {e}")
