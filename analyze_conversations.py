import argparse
import sqlite3
import datetime
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "db-and-recordings/conversation_turns.db")


def percentile(data, percent):
    """
    Return the percentile of the data (percent in [0, 1]).
    Uses numpy if available, otherwise falls back to manual calculation.
    """
    if not data:
        return None
    try:
        import numpy as np
        import inspect
        np_percentile = np.percentile
        # Check if 'method' is in the signature (NumPy >= 1.22)
        if 'method' in inspect.signature(np_percentile).parameters:
            return float(np_percentile(data, percent * 100, method="linear"))
        else:
            return float(np_percentile(data, percent * 100, interpolation="linear"))
    except ImportError:
        # Manual calculation (nearest-rank method for small N)
        data_sorted = sorted(data)
        idx = percent * (len(data_sorted) - 1)
        lower = int(idx)
        upper = min(lower + 1, len(data_sorted) - 1)
        weight = idx - lower
        return data_sorted[lower] * (1 - weight) + data_sorted[upper] * weight


def list_sessions(show_percentiles=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT session_id, MIN(turn_start_time), COUNT(*)
        FROM conversation_turn
        GROUP BY session_id
        ORDER BY MIN(turn_start_time) ASC
        """
    )
    sessions = cursor.fetchall()
    if not sessions:
        print("No sessions found.")
        return
    if show_percentiles:
        print(f"{'Session ID':<25} {'First Turn Start':<25} {'Num Turns':<10} {'P50 V2V (s)':<12} {'P95 V2V (s)':<12}")
        print("-" * 95)
    else:
        print(f"{'Session ID':<25} {'First Turn Start':<25} {'Num Turns':<10}")
        print("-" * 65)
    for session_id, first_turn_start, num_turns in sessions:
        # Format the timestamp to local time, human readable
        dt = datetime.datetime.fromtimestamp(first_turn_start)
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        if show_percentiles:
            # Get all voice_to_voice_response_time values for this session
            cursor.execute(
                "SELECT voice_to_voice_response_time FROM conversation_turn WHERE session_id = ? AND voice_to_voice_response_time IS NOT NULL ORDER BY turn_number ASC",
                (session_id,)
            )
            v2v_times = [row[0] for row in cursor.fetchall() if row[0] is not None]
            v2v_times_sorted = sorted(v2v_times)
            p50 = percentile(v2v_times_sorted, 0.5)
            p95 = percentile(v2v_times_sorted, 0.95)
            p50_str = f"{p50:.3f}" if p50 is not None else "-"
            p95_str = f"{p95:.3f}" if p95 is not None else "-"
            print(f"{session_id:<25} {formatted_time:<25} {num_turns:<10} {p50_str:<12} {p95_str:<12}")
        else:
            print(f"{session_id:<25} {formatted_time:<25} {num_turns:<10}")
    conn.close()


def show_session(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT turn_number, turn_start_time, turn_end_time, user_speech_text, llm_response_text, voice_to_voice_response_time, interrupted
        FROM conversation_turn
        WHERE session_id = ?
        ORDER BY turn_number ASC
        """,
        (session_id,)
    )
    turns = cursor.fetchall()
    if not turns:
        print(f"No turns found for session_id: {session_id}")
        return
    print(f"Session: {session_id}")
    print("-" * 80)
    for t in turns:
        (turn_number, start, end, user_text, llm_text, v2v_time, interrupted) = t
        start_fmt = datetime.datetime.fromtimestamp(start).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        end_fmt = datetime.datetime.fromtimestamp(end).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"Turn {turn_number}")
        print(f"  Start: {start_fmt}")
        print(f"  End:   {end_fmt}")
        print(f"  Interrupted: {bool(interrupted)}")
        print(f"  Voice-to-voice response time: {v2v_time:.3f} s")
        print(f"  User said: {user_text}")
        print(f"  LLM said:  {llm_text}")
        print("-" * 80)
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Analyze conversation turns in the SQLite DB.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_list = subparsers.add_parser("list-sessions", help="List all session IDs with first turn time and number of turns.")
    parser_list.add_argument("--show-percentiles", action="store_true", help="Show P50 and P95 voice-to-voice response time for each session.")
    parser_show = subparsers.add_parser("show-session", help="Show all turns for a session.")
    parser_show.add_argument("session_id", help="Session ID to display.")

    args = parser.parse_args()

    if args.command == "list-sessions":
        list_sessions(show_percentiles=args.show_percentiles)
    elif args.command == "show-session":
        show_session(args.session_id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
