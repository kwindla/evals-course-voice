import argparse
import sqlite3
import wave
import pyaudio
import os

DB_PATH = os.path.join("db-and-recordings", "conversation_turns.db")
AUDIO_DIR = "db-and-recordings"

# Amount of padding to add to the start and end of the turn when playing it back. We're
# not aiming for perfect turn alignment here. We just want to be able to hear the turn
# start and end.
PLAY_PADDING = 1.0


def get_turn_times(session_id, turn_number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Get the first turn's start time for this session
    c.execute(
        """SELECT turn_start_time FROM conversation_turn WHERE session_id=? ORDER BY turn_number ASC LIMIT 1""",
        (session_id,),
    )
    row = c.fetchone()
    if not row:
        raise ValueError(f"No turns found for session_id {session_id}")
    session_start = row[0]
    # Get the requested turn's start and end time
    c.execute(
        """SELECT turn_start_time, turn_end_time FROM conversation_turn WHERE session_id=? AND turn_number=?""",
        (session_id, turn_number),
    )
    row = c.fetchone()
    if not row:
        raise ValueError(f"Turn {turn_number} not found for session_id {session_id}")
    turn_start, turn_end = row
    conn.close()
    # Offset relative to session start
    return (
        max(0, turn_start - session_start - PLAY_PADDING),
        turn_end - session_start + PLAY_PADDING,
    )


def play_wav_segment(wav_path, start_sec, end_sec, chunk_ms=100):
    print(f"Playing {wav_path} from {start_sec:.2f}s to {end_sec:.2f}s")
    with wave.open(wav_path, "rb") as wf:
        framerate = wf.getframerate()
        sampwidth = wf.getsampwidth()
        nchannels = wf.getnchannels()
        start_frame = int(start_sec * framerate)
        end_frame = int(end_sec * framerate)
        nframes = end_frame - start_frame
        wf.setpos(start_frame)

        chunk_frames = int((chunk_ms / 1000.0) * framerate)

        p = pyaudio.PyAudio()
        stream = p.open(
            format=p.get_format_from_width(sampwidth),
            channels=nchannels,
            rate=framerate,
            output=True,
        )
        frames_left = nframes
        try:
            while frames_left > 0:
                frames_to_read = min(chunk_frames, frames_left)
                data = wf.readframes(frames_to_read)
                if not data:
                    break
                stream.write(data)
                frames_left -= frames_to_read
        except KeyboardInterrupt:
            print("\nPlayback interrupted by user.")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()


def main():
    parser = argparse.ArgumentParser(
        description="Play audio for a turn in a conversation."
    )
    parser.add_argument("session_id", type=str, help="Session ID")
    parser.add_argument("turn_number", type=int, help="Turn number (integer)")
    args = parser.parse_args()

    wav_path = os.path.join(AUDIO_DIR, f"conversation-{args.session_id}.wav")
    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"Audio file not found: {wav_path}")

    start_sec, end_sec = get_turn_times(args.session_id, args.turn_number)
    print(
        f"Playing session {args.session_id} turn {args.turn_number} ({start_sec:.2f}s - {end_sec:.2f}s)"
    )
    try:
        play_wav_segment(wav_path, start_sec, end_sec)
    except KeyboardInterrupt:
        print("\nPlayback interrupted by user.")
        return


if __name__ == "__main__":
    main()
