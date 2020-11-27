import os, asyncio
import pytest
from pytest_mock import mocker
from configparser import ConfigParser

from songguess.sg import SongGuess

@pytest.fixture
def bot_mock(mocker):
    stub = mocker.stub("bot_mock")
    return stub

@pytest.fixture
def queue_mock(mocker, question_mock):
    def prepare_mock(amount, is_anime_dup=False):
        return amount
    
    qm = mocker.patch("songguess.sg.QuestionQueue")
    qm.prepare.side_effect = prepare_mock
    qm.get_question.return_value = question_mock
    return qm

@pytest.fixture
def question_mock(mocker):
    q = mocker.MagicMock()
    q.info = {
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
    }
    return q

@pytest.fixture
def config():
    config = ConfigParser()
    if not config.read(os.path.join(os.path.dirname(__file__), "../config.ini")):
        raise Exception()
    return config

@pytest.fixture
def sg(bot_mock, config, queue_mock):
    sg = SongGuess(bot_mock, config, queue_mock)
    return sg

@pytest.mark.asyncio
async def test_play(mocker, sg):
    mocker.patch("songguess.sg.commands.command")
    ctx = mocker.AsyncMock()
    await sg.play(sg, ctx)
    assert ctx.send.assert_any_await("Game loading...")
    assert ctx.send.assert_any_await("New round start!")