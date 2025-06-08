# Put your voice conversation data somewhere (so you can look at it (and listen to it)).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Project plan

[ ] simple voice bot
[ ] add langfuse tracing
[ ] add sqlite storage for each turn
  [ ] turn text
  [ ] turn audio
  [ ] turn timing data
[ ] simple evals
  [ ] P50 and P95 voice-to-voice
  [ ] manually inject a flaw and use Gemini Pro to find it
[ ] utility to play a turn

