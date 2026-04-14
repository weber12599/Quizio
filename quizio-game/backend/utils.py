import os
from collections import Counter
from typing import Any, Dict, Tuple

import httpx
import nh3

DATA_SERVICE_BASE_URL = os.getenv('DATA_SERVICE_BASE_URL')
DATA_SERVICE_STUDENT_AUTH_URL = f'{DATA_SERVICE_BASE_URL}/api/auth/student'
DATA_SERVICE_GUEST_AUTH_URL = f'{DATA_SERVICE_BASE_URL}/api/auth/guest'


def sanitize_rich_text(html_content: str) -> str:
    if not html_content:
        return html_content

    allowed_tags = {
        'p',
        'b',
        'i',
        'u',
        'strong',
        'em',
        'br',
        'ul',
        'ol',
        'li',
        'img',
        'h1',
        'h2',
        'h3',
        'blockquote',
        'code',
        'pre',
        's',
    }
    allowed_attributes = {
        'img': {'src', 'alt', 'title', 'width', 'height'},
        'code': {'class'},
    }
    return nh3.clean(html_content, tags=allowed_tags, attributes=allowed_attributes)


async def check_student_credentials(student_id: str, password: str, token: str):
    if not token:
        print('Error: No valid host token provided for this room.')
        return None

    auth_header = f'Bearer {token}'

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                DATA_SERVICE_STUDENT_AUTH_URL,
                json={'student_id': student_id, 'password': password},
                headers={'Authorization': auth_header},
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(
                    f'Student verification failed: {response.status_code} - {response.text}'
                )
                return None
        except Exception as e:
            print(f'Network error (cannot connect to quizio-data): {e}')
            return None


async def check_guest_credentials(guest_name: str, token: str):
    if not token:
        print('Error: No valid host token provided for this room.')
        return None

    auth_header = f'Bearer {token}'

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                DATA_SERVICE_GUEST_AUTH_URL,
                json={'guest_name': guest_name},
                headers={'Authorization': auth_header},
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(
                    f'Guest verification failed: {response.status_code} - {response.text}'
                )
                return None
        except Exception as e:
            print(f'Network error (cannot connect to quizio-data): {e}')
            return None


async def submit_student_submission(token: str, payload: dict):
    """
    Send a single student's submission (answers + gradings) to the Data Backend.
    """
    url = f'{DATA_SERVICE_BASE_URL}/api/submissions/'
    headers = {'Authorization': f'Bearer {token}'}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url, json=payload, headers=headers, timeout=10.0
            )
            if response.status_code not in (200, 201):
                print(f'Error submitting data to data-backend: {response.text}')
        except Exception as e:
            print(f'Network error while submitting data: {e}')


async def submit_batch_submissions(token: str, payload: list):
    """
    Send all student submissions as a single batch to the Data Backend.
    """
    url = f'{DATA_SERVICE_BASE_URL}/api/submissions/batch'
    headers = {'Authorization': f'Bearer {token}'}

    async with httpx.AsyncClient() as client:
        try:
            # Increased timeout slightly for batch processing
            response = await client.post(
                url, json=payload, headers=headers, timeout=15.0
            )
            if response.status_code not in (200, 201):
                print(f'Error submitting batch data to data-backend: {response.text}')
        except Exception as e:
            print(f'Network error while submitting batch data: {e}')


def grade_answer(q_type: str, student_answer: any, correct_answer: any) -> bool:
    """Evaluate student's answer based on the question type."""
    if correct_answer is None or correct_answer == '':
        return False

    if q_type == 'essay':
        return False

    if q_type == 'multiple':
        if not isinstance(student_answer, list) or not isinstance(correct_answer, list):
            return False

        stu_set = set(str(x).strip() for x in student_answer)
        ref_set = set(str(x).strip() for x in correct_answer)
        return stu_set == ref_set

    if q_type == 'boolean':
        if str(student_answer).strip() == '0':
            stu_bool = True
        elif str(student_answer).strip() == '1':
            stu_bool = False
        else:
            stu_bool = str(student_answer).strip().lower() in ['true', '1', 'yes']

        ref_bool = str(correct_answer).strip().lower() in ['true', '1', 'yes']
        return stu_bool == ref_bool

    if q_type == 'single':
        return str(student_answer).strip() == str(correct_answer).strip()

    if q_type == 'short':
        return (
            str(student_answer).strip().lower() == str(correct_answer).strip().lower()
        )

    return False


def compute_stats(q_type: str, answers_dict: dict) -> Tuple[Dict[str, int], int]:
    """
    Computes statistics based on the question type.
    Always returns a tuple of (frequency_dict, total_answers).
    """
    total = len(answers_dict) if answers_dict else 0
    if total == 0:
        return {}, 0

    if q_type in ['single', 'boolean']:
        stats = {}
        for ans in answers_dict.values():
            if ans is not None:
                ans_str = str(ans)
                stats[ans_str] = stats.get(ans_str, 0) + 1
        return stats, total

    elif q_type == 'multiple':
        stats = {}
        for ans_list in answers_dict.values():
            if isinstance(ans_list, list):
                for ans in ans_list:
                    if ans is not None:
                        ans_str = str(ans)
                        stats[ans_str] = stats.get(ans_str, 0) + 1
        return stats, total

    elif q_type == 'short':
        stats = calculate_exact_frequency(answers_dict)
        return stats, total

    return {}, total


def generate_leaderboard(room: dict) -> list:
    """Helper function to calculate scores and generate leaderboard."""
    scores = {}
    names = {}

    for player_id, p in room['clients'].items():
        scores[player_id] = 0
        names[player_id] = p['name']

    gradings = room.get('gradings', {})
    for q_id, q_gradings in gradings.items():
        for player_id, result in q_gradings.items():
            if result.get('is_correct'):
                scores[player_id] = scores.get(player_id, 0) + 100

    leaderboard = [
        {'name': names.get(st_id, 'Unknown'), 'score': score}
        for st_id, score in scores.items()
    ]
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    return leaderboard


def calculate_exact_frequency(answers_dict: Dict[str, Any]) -> Dict[str, int]:
    """
    Calculates the exact word frequency for short answer questions (Strategy A).
    Converts all valid string answers to lowercase and strips whitespaces.

    Returns:
        A dictionary mapping the cleaned answer to its frequency count.
        Example: {"apple": 3, "banana": 1}
    """
    if not answers_dict:
        return {}

    processed_answers = []

    for player_id, answer in answers_dict.items():
        if isinstance(answer, str) and answer.strip():
            cleaned_ans = answer.strip().lower()
            processed_answers.append(cleaned_ans)

    # Counter returns a dictionary-like object, we convert it to a standard dict
    return dict(Counter(processed_answers))
