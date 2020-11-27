import asyncio
import pytest
from pytest_mock import mocker

from songguess.queue import QuestionQueue, Question

class MockQuestion:
        def __init__(self, info, loop, thread_pool):
            self.info = info
            self.task = None

        def set_download_task(self):
            if self.task == None:
                self.task = asyncio.Future()
                self.task.set_result(True)

@pytest.fixture
def qdb_mock(mocker):
    qdb = mocker.patch("songguess.queue.QuestionDB")
    qdb.get_questions.return_value = [
        {
            "name": "song1",
            "singer": "singer1",
            "url": "http://url1",
            "year": 2000,
            "intro": 0,
            "verse": 10,
            "chorus": 20,
            "anime": "anime1",
            "season": "",
            "type": "op",
            "tags": []
        },
        {
            "name": "song2",
            "singer": "singer2",
            "url": "http://url2",
            "year": 2005,
            "intro": 0,
            "verse": 10,
            "chorus": 20,
            "anime": "anime2",
            "season": "",
            "type": "op",
            "tags": []
        },
        {
            "name": "song3",
            "singer": "singer3",
            "url": "http://url3",
            "year": 2010,
            "intro": 0,
            "verse": 10,
            "chorus": 20,
            "anime": "anime3",
            "season": "",
            "type": "movie",
            "tags": []
        },
        {
            "name": "song1",
            "singer": "singer1",
            "url": "http://url4",
            "year": 2015,
            "intro": 0,
            "verse": 10,
            "chorus": 20,
            "anime": "anime1",
            "season": "",
            "type": "ed",
            "tags": []
        },
        {
            "name": "song2",
            "singer": "singer2",
            "url": "http://url5",
            "year": 2020,
            "intro": 0,
            "verse": 10,
            "chorus": 20,
            "anime": "anime2",
            "season": "",
            "type": "ed",
            "tags": []
        }
    ]
    return qdb

@pytest.fixture
def question_queue(qdb_mock):
    qq = QuestionQueue(qdb_mock, None, 5, 4)
    return qq

@pytest.fixture
def question_mock(mocker):
    qClass = mocker.patch("songguess.queue.Question", new=MockQuestion)
    return qClass

@pytest.mark.parametrize(
    "amount, is_anime_dup, expect",
    [
        (5, False, 3),
        (5, True, 5),
        (3, False, 3),
        (3, True, 3),
    ],
)
def test_prepare(question_queue, question_mock, amount, is_anime_dup, expect):
    num = question_queue.prepare(amount, is_anime_dup)
    assert num == expect

@pytest.mark.asyncio
async def test_get_question(question_queue, question_mock):
    for _ in range(10):
        q = question_mock(None, None, None)
        question_queue.qlist.append(q)
    await question_queue.get_question()

    assert len(question_queue.qlist) == 9

