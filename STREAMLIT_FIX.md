# Fix for Streamlit Cloud Error: AI/requirements.txt

## The Problem

Streamlit Cloud is trying to parse `AI/requirements.txt` as a package, which causes:
```
error: Failed to parse: `AI/requirements.txt`
ERROR: Invalid requirement: 'AI/requirements.txt'
```

## The Solution

The `requirements.txt` file is now correctly located at `HospitalFlow AI/requirements.txt` (same folder as `app.py`).

### Steps to Fix:

1. **Go to Streamlit Cloud Dashboard**: https://share.streamlit.io/

2. **Find your app** and click on it

3. **Click "⋮" (three dots) menu** → **"Reboot app"** or **"Restart"**

   This will clear any cached references to the old `AI/requirements.txt` location.

4. **Wait for redeployment** (1-2 minutes)

5. **Check the logs** - you should now see plotly being installed successfully

## Why This Happened

There was a previous commit that moved `requirements.txt` to `AI/requirements.txt`. Even though we've fixed it, Streamlit Cloud might have cached the old reference.

## Current Structure (Correct)

```
hospitalflow/
└── HospitalFlow AI/
    ├── app.py
    ├── requirements.txt  ✅ (correct location)
    ├── db.py
    ├── simulation.py
    └── utils.py
```

## If Still Not Working

1. **Delete the deployment** on Streamlit Cloud
2. **Create a new deployment** with:
   - Repository: `a-fazi/hospitalflow`
   - Branch: `main`
   - Main file path: `HospitalFlow AI/app.py`
   - App URL: `hospitalflow`

This will start fresh without any cached references.

