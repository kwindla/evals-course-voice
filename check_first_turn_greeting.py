import os
import sqlite3
import openai
import argparse
from tqdm import tqdm
from dotenv import load_dotenv

DB_PATH = os.path.join(
    os.path.dirname(__file__), "db-and-recordings/conversation_turns.db"
)

PROMPT_TEMPLATE = """You are checking LLM output for a voice conversation. The following is the transcript of the first turn of a conversation. If the text is 'I am here and ready to help', respond ONLY with 'EXACT'. You can ignore punctuation and spacing differences. But there should be no other text before or after the phrase, and the phrase should be very close to 'I am here and ready to help'. If it is anything else, respond ONLY with 'NOT EXACT'.
    
    TEXT: 
    
    {text}"""


def get_first_turns(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT session_id, llm_response_text
        FROM conversation_turn
        WHERE turn_number = 1
        ORDER BY session_id ASC
        """
    )
    return cursor.fetchall()


def check_with_gpt4o(text, openai_api_key):
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a strict text checker."},
            {"role": "user", "content": PROMPT_TEMPLATE.format(text=text)},
        ],
        max_tokens=3,
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Check if first turn is exact greeting."
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Don't call OpenAI API, just print first turns.",
    )
    args = parser.parse_args()

    load_dotenv(override=True)
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not args.no_api and not openai_api_key:
        print("Please set the OPENAI_API_KEY environment variable in your .env file.")
        return

    conn = sqlite3.connect(DB_PATH)
    first_turns = get_first_turns(conn)
    conn.close()

    total = 0
    correct = 0
    incorrect = 0
    for session_id, llm_text in tqdm(first_turns):
        if args.no_api:
            print(f"Session: {session_id}\nFirst turn (LLM): {llm_text}\n{'-' * 40}")
        else:
            result = check_with_gpt4o(llm_text or "", openai_api_key)
            print(
                f"Session: {session_id}\nFirst turn (LLM): {llm_text}\nResult: {result}\n{'-' * 40}"
            )
            total += 1
            if result.upper() == "EXACT":
                correct += 1
            else:
                incorrect += 1
    if not args.no_api:
        percent = (correct / total * 100) if total > 0 else 0.0
        print(f"\nSummary:")
        print(f"Total tested: {total}")
        print(f"Correct (EXACT): {correct}")
        print(f"Incorrect (NOT EXACT): {incorrect}")
        print(f"Percentage correct: {percent:.1f}%")


if __name__ == "__main__":
    main()
