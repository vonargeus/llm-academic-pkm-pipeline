# Setup Guide — Gemini API + OpenCode Integration

## Step 1: Get your Gemini API key (free)

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API key"**
4. Copy the key (it looks like `AIzaSy...`)

Gemini 1.5 Flash is **free** with a generous quota (15 requests/min, 1500/day).
That is more than enough for 20–25 papers.

---

## Step 2: Save the key — so you NEVER have to type it again

### Method A: `.env` file (recommended for the Python project)

1. Copy `.env.example` to `.env`:
   ```
   copy .env.example .env
   ```
2. Open `.env` in any text editor and replace the placeholder:
   ```
   GEMINI_API_KEY=AIzaSyYOURACTUALKEYHERE
   ```
3. That's it. Every Python script in this project loads it automatically.
   You never type the key again.

### Method B: Permanent Windows system variable (recommended for OpenCode)

Run this **once** in PowerShell (replace the key):
```powershell
[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "AIzaSyYOURKEY", "User")
[System.Environment]::SetEnvironmentVariable("LLM_PROVIDER", "gemini", "User")
```

After running this, **restart any open terminals**. The key is now permanently
saved in your Windows user profile — you never need to set it again, even
after rebooting.

To verify it worked (in a new terminal):
```powershell
echo $env:GEMINI_API_KEY
```

---

## Step 3: Configure OpenCode to use Gemini

OpenCode reads its LLM configuration from `.opencode/config.json` (or `AGENTS.md`
depending on the platform version). Do the following inside your vault or project folder:

### Option A: Via OpenCode's built-in model selector

Open OpenCode in your project folder and type:
```
/model
```
Then select **Gemini** and choose `gemini-1.5-flash` or `gemini-2.0-flash`.
OpenCode will remember this choice — you don't need to set it again.

### Option B: Via config file

Create or edit `.opencode/config.json` in your project folder:
```json
{
  "model": "gemini-1.5-flash",
  "provider": "google"
}
```

OpenCode will automatically use your `GEMINI_API_KEY` from the Windows environment
variable (set in Step 2).

---

## Step 4: Verify the Python project works

```powershell
cd c:\Users\jubam\Desktop\Bsc_Project

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Test the metadata agent works
python -c "
from src.agents.metadata_agent import call_llm
print(call_llm('Say hello in 5 words.'))
"
```

If this prints a short Gemini response, everything is configured correctly.

---

## Summary: What you need to do ONE TIME only

| Step | Action | Time |
|------|--------|------|
| 1 | Get API key from aistudio.google.com | 2 min |
| 2A | Paste key into `.env` file | 30 sec |
| 2B | Run `SetEnvironmentVariable` in PowerShell | 30 sec |
| 3 | Set Gemini model in OpenCode with `/model` | 1 min |

After that: just open OpenCode in your project folder — it reads the key automatically.
No typing API keys. No setup commands. Just work.

---

## Cost estimate

For a 25-paper corpus:
- Metadata extraction: 25 × ~3000 input tokens + ~500 output = ~87K tokens total
- Note generation: 25 × ~12000 input + ~2000 output = ~350K tokens total
- Link generation: 25 × ~5000 input + ~500 output = ~137K tokens total
- **Total: ~574K tokens**

Gemini 1.5 Flash free tier: **1,500,000 tokens/day free**
→ Your entire thesis corpus fits in the free tier with room to spare.
