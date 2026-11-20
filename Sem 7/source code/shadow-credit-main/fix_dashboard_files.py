import os
import shutil

# Define moves
moves = [
    (r"d:\Fintech project\shadow-credit\frontend\app\dashboard\CaseQueue.tsx", r"d:\Fintech project\shadow-credit\frontend\app\dashboard\page.tsx"),
    (r"d:\Fintech project\shadow-credit\frontend\app\dashboard\SessionPage.tsx", r"d:\Fintech project\shadow-credit\frontend\app\dashboard\[sessionId]\page.tsx")
]

for src, dst in moves:
    try:
        if os.path.exists(src):
            # Ensure dir exists
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            # Copy content
            shutil.copy2(src, dst)
            print(f"Copied {src} to {dst}")
            # Remove source
            os.remove(src)
            print(f"Removed {src}")
        else:
            print(f"Source not found: {src}")
    except Exception as e:
        print(f"Error moving {src} to {dst}: {e}")
