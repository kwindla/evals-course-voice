# Put your voice conversation data somewhere (so you can look at it (and listen to it)).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## To run the bots locally

```bash
python 001-bot-simple.py
```

## Simple bot file (reference - no data storage)

```bash
python 001-bot-simple.py
```

## Bot with open telemetry tracing (Langfuse)

To add open telemetry tracing, add these lines to the bot and set three environment variables.

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

Set these environment variables:

```bash
ENABLE_TRACING=true
OTEL_EXPORTER_OTLP_ENDPOINT="https://us.cloud.langfuse.com/api/public/otel"
OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic%20<base64 encoded public-key:secret-key>"
```

And run the bot with the otel tracing code..

```bash
python 002-bot-langfuse.py
```

Instructions for setting up Pipecat + Langfuse are here:

  https://github.com/pipecat-ai/pipecat/blob/main/examples/open-telemetry/langfuse/README.md#setup-instructions

## Bot that saves turn data to sqlite

For each conversation turn, we'll save information about what the user and bot said, plus some timing data, in a sqlite database.

Here's how we create the database file.

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

We'll also save the full audio of each conversation.







## Project plan

[x] simple voice bot
[x] add langfuse tracing
[ ] add sqlite storage for each turn
  [ ] turn text
  [ ] turn audio
  [ ] turn timing data
[ ] simple evals
  [ ] P50 and P95 voice-to-voice
  [ ] manually inject a flaw and use Gemini Pro to find it
[ ] utility to play a turn

