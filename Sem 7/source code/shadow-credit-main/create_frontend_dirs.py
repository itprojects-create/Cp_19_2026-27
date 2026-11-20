import os

dirs = [
    r"d:\Fintech project\shadow-credit\frontend\store",
    r"d:\Fintech project\shadow-credit\frontend\app\dashboard\[sessionId]"
]

for d in dirs:
    try:
        os.makedirs(d, exist_ok=True)
        print(f"Created: {d}")
    except Exception as e:
        print(f"Error creating {d}: {e}")
