# Put your voice conversation data somewhere (so you can look at it (and listen to it)).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## To run the bots locally

The first time you run the bot, it will take a few seconds to cache the Silero VAD model. Subsequent runs will start quickly.

```bash
python 001-bot-simple.py
```

## Simple bot file (reference - no data storage)

```bash
python 001-bot-simple.py
```

## Bot with open telemetry tracing (Langfuse)

We can add open telemetry tracing with just a few lines of code. `002-bot-otel.py` demonstrates this.

```bash
$ diff 001-bot-simple.py 002-bot-otel.py
45a46,48
> from pipecat.utils.tracing.setup import setup_tracing
> from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
> 
47a51
> 
52a57,66
> IS_TRACING_ENABLED = bool(os.getenv("ENABLE_TRACING"))
> if IS_TRACING_ENABLED:
>     otlp_exporter = OTLPSpanExporter()
>     setup_tracing(
>         service_name="evals-course-voice",
>         exporter=otlp_exporter,
>     )
>     logger.info("OpenTelemetry tracing initialized")
> 
> 
142a157
>         enable_tracing=IS_TRACING_ENABLED,
```

I set these environment variables to send the otel traces to Langfuse. 

```bash
ENABLE_TRACING=true
OTEL_EXPORTER_OTLP_ENDPOINT="https://us.cloud.langfuse.com/api/public/otel"
OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic%20<base64 encoded public-key:secret-key>"
```

Run the bot and the look at the traces using your otel tooling of choice.

```bash
python 002-bot-langfuse.py
```

Instructions for setting up Pipecat + Langfuse are here:

  https://github.com/pipecat-ai/pipecat/blob/main/examples/open-telemetry/langfuse/README.md#setup-instructions

## Bot that saves turn data to sqlite

`003-bot-sqlite.py` shows how you might write code that saves conversation turn text and metrics using sqlite, and also saves the full conversation audio.

Here's how we create the sqlite db file.

```bash
sqlite3 db-and-recordings/conversation_turns.db "
CREATE TABLE IF NOT EXISTS conversation_turn (
  session_id TEXT NOT NULL,
  turn_number INTEGER NOT NULL,
  turn_start_time REAL NOT NULL,  -- seconds since Unix epoch, as returned by time.time()
  turn_end_time REAL NOT NULL,    -- seconds since Unix epoch, as returned by time.time()
  user_speech_text TEXT,
  llm_response_text TEXT,
  voice_to_voice_response_time REAL,
  interrupted BOOLEAN NOT NULL
);"
```

We've also vibe-coded three example "look at the data" scripts.

### analyze-conversations.py

Prints out some basic stats about the conversations saved in the db file.

```bash
(venv) khkramer@toque evals-course-voice % python analyze_conversations.py list-sessions --show-percentiles
Session ID                First Turn Start          Num Turns  P50 V2V (s)  P95 V2V (s)
-----------------------------------------------------------------------------------------------
1749447300-448            2025-06-08 22:35:00       2          0.710        0.744
1749447318-995            2025-06-08 22:35:18       3          0.731        1.339
1749447338-12             2025-06-08 22:35:38       1          0.679        0.679
1749447349-494            2025-06-08 22:35:49       4          0.762        0.906
1749447402-850            2025-06-08 22:36:44       1          0.672        0.672
1749447408-394            2025-06-08 22:36:48       2          0.821        0.941
1749447421-9              2025-06-08 22:37:01       5          0.725        1.160
1749447559-573            2025-06-08 22:39:20       2          0.577        0.610
1749447577-500            2025-06-08 22:39:39       1          0.677        0.677
1749447583-771            2025-06-08 22:39:46       1          0.840        0.840
1749447590-918            2025-06-08 22:39:50       3          0.801        0.811
1749447618-597            2025-06-08 22:40:21       1          0.657        0.657
1749447625-979            2025-06-08 22:40:25       2          0.832        0.926
1749447640-426            2025-06-08 22:40:42       1          0.801        0.801
1749447646-958            2025-06-08 22:40:49       1          0.988        0.988
```

### play_turn_audio.py

Plays a single turn of audio from a session. We add some buffer time on the start and end to make it easier to hear the full turn context.

```bash
python play_turn_audio.py 1749447421-9 4
Playing session 1749447421-9 turn 4 (20.94s - 31.92s)
Playing db-and-recordings/conversation-1749447421-9.wav from 20.94s to 31.92s
```

### check_first_turn_greeting.py

An example of the kind of quick evals you might hack together to test specific issues you find as you look at bot conversation data. In this case, we're checking to see if the bot always greets the user with the phrase that it is supposed to say. This is a real-world example. GPT-4o will sometimes explicitly refuse to say exact phrases or freelance a little bit by saying a phrase plus a bit more than it was asked to say.

This script uses an LLM to check the assistant side of the first turn of every conversation in the sqlite db file.

```bash
python check_first_turn_greeting.py
# ...
Session: 1749450406-713
First turn (LLM): I'm here and ready to help! What can I do for you today?
Result: NOT EXACT
----------------------------------------
100%|███████████████████████████████████████████████████| 21/21 [00:10<00:00,  2.06it/s]

Summary:
Total tested: 21
Correct (EXACT): 20
Incorrect (NOT EXACT): 1
Percentage correct: 95.2%
```



