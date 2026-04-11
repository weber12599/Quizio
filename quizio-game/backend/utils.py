import os

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


def compute_stats(q_type: str, answers_dict: dict) -> tuple:
    """Compute answer statistics for the bar charts."""
    stats = {}
    total = len(answers_dict)

    for sid, ans in answers_dict.items():
        if q_type == 'multiple' and isinstance(ans, list):
            for a in ans:
                stats[str(a)] = stats.get(str(a), 0) + 1
        elif q_type == 'boolean':
            ans_idx = '0' if ans else '1'
            stats[ans_idx] = stats.get(ans_idx, 0) + 1
        elif q_type == 'single':
            stats[str(ans)] = stats.get(str(ans), 0) + 1

    return stats, total


def generate_leaderboard(room: dict) -> list:
    """Helper function to calculate scores and generate leaderboard."""
    scores = {}
    names = {}

    for p_sid, p in room['players'].items():
        if p['role'] == 'client':
            st_id = p['student_id']
            scores[st_id] = 0
            names[st_id] = p['name']

    gradings = room.get('gradings', {})
    for q_id, q_gradings in gradings.items():
        for st_id, result in q_gradings.items():
            if result.get('is_correct'):
                scores[st_id] = scores.get(st_id, 0) + 100

    leaderboard = [
        {'name': names.get(st_id, 'Unknown'), 'score': score}
        for st_id, score in scores.items()
    ]
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    return leaderboard
