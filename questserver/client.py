from collections import namedtuple
from json import load, dump
from questioncataloguing import Catalogue, _Question, Section
from subprocess import run
from sqlite3 import connect, Connection
from os import path, makedirs
from json import loads, dumps
from time import time
from random import shuffle
from typing import List


DECAY_FACTOR = 0.8
DECAY_TIME = 7   # days

def evaluate_answer_score(score_history, use_decay=True):
    '''
    Evaluate how good the client can answer
    a question. Uses decay over time.
    score_history =[(score, time), ...]
    newest first
    '''
    if not score_history:
        return 0
    
    def decay_factor(timestamp):
        if not use_decay:
            return 1
        age_days = (time() - timestamp) / (24 * 3600)
        return DECAY_FACTOR ** (age_days // DECAY_TIME)

    WEIGHTS = [35, 30, 25, 20, 15, 10]
    weights = [w / sum(WEIGHTS) for w in WEIGHTS]
    score = 0
    for i in range(len(weights)):
        if len(score_history) == 0:
            return score
        score_once, timestamp = score_history[0]
        score += score_once * weights[i] * decay_factor(timestamp)
        del score_history[0]
    return score

AnswerStat = namedtuple('AnswerStat', ['section_id', 'question_id', 'score'])

ScoreDiffHistory = namedtuple(
    'ScoreDiffHistroy',
    ['timestamp', 'duration', 'mode', 'scorediff', 'section', 'section_scorediff']
)

class Client:
    def __init__(self, user_id, catalogue: Catalogue):
        self.user_id = user_id
        self.base_dir = 'userdata/{user_id}'.format(user_id=user_id)
        makedirs(self.base_dir, exist_ok=True)
        self.userdata_json = '{base}/user.json'.format(base=self.base_dir)

        self.catalogue = catalogue
        self.con = self.build_stats_for_catalogue(catalogue)
        self.cur = self.con.cursor()


    def set_userdata(self, user):
        with open(self.userdata_json, 'w') as f:
            d = {
                'user_id': self.user_id,
                'username': user.username,
                'fname': user.first_name,
                'lname': user.last_name,
            }
            dump(d, f)

    def build_stats_for_catalogue(self, c: Catalogue) -> Connection:
        catalogue_db = '{base}/catalogue_{catalogue_id}.sqlite3'.format(
            base=self.base_dir, catalogue_id=c.id)
        
        con = connect(catalogue_db)
        cur = con.cursor()

        cur.execute(
            'CREATE TABLE IF NOT EXISTS statistics '
            '(section_id TEXT, question_id, score FLOAT, time INT)'
        )
        cur.execute(
            'CREATE TABLE IF NOT EXISTS runs '
            '(section_id TEXT, gamemode TEXT, start INT, duration FLOAT)'
        )
        con.commit()

        cur.close()
        return con

    def get_question_score(self, q: _Question, at_timestamp=None):
        if at_timestamp is None:
            at_timestamp = int(time())
        self.cur.execute(
            'SELECT score, time FROM statistics '
            'WHERE section_id = ? AND question_id = ? '
            'AND time <= ? '
            'ORDER BY TIME DESC LIMIT 15',
            (q.section_id, q.id, at_timestamp))
        res = self.cur.fetchall()
        score = evaluate_answer_score(res)
        return score

    def get_section_score(self, s: Section, at_timestamp=None):
        max_points = 0
        scored = 0
        for q in s.get_all_questions():
            max_points += q.points
            scored += self.get_question_score(q, at_timestamp)
    
        return scored / max_points

    def get_catalogue_score(self, at_timestamp=None):
        max_points = 0
        scored = 0
        for s in self.catalogue.get_all_sections():
            for q in s.get_all_questions():
                max_points += q.points
                scored = self.get_question_score(q, at_timestamp)
        return scored / max_points

    def get_hardest(self, sections: List[Section], limit=100):
        questions = []
        for sec in sections:
            questions += sec.get_all_questions()
        shuffle(questions)

        sorted_questions = sorted(
            questions,
            key=lambda q: self.get_question_score(q)
        )
        return list(sorted_questions[:limit])

    def enter_score(self, q: _Question, score: float):
        self.cur.execute(
            'INSERT INTO statistics (section_id, question_id, score, time) '
            'VALUES (?, ?, ?, ?)',
            (q.section_id, q.id, score, int(time()))
        )
        self.con.commit()

    def enter_run(self, section_id, gamemode, start, duration):
        self.cur.execute(
            'INSERT INTO runs (section_id, gamemode, start, duration) VALUES '
            '(?, ?, ?, ?)',
            (section_id, gamemode, int(start + 0.5), duration)
        )
        self.con.commit()

    def get_run_scorediffs(self, max=10) -> List[ScoreDiffHistory]:
        self.cur.execute(
            'SELECT section_id, gamemode, start, duration FROM runs '
            'ORDER BY start DESC'
        )
        results = []
        res = self.cur.fetchall()
        for section_id, gamemode, start, duration in res:
            prev_score = self.get_catalogue_score(start - 1)
            post_score = self.get_catalogue_score(start + duration)

            section_scorediff = None
            if not section_id is None:
                s = self.catalogue.get_section(section_id=section_id)
                prev_score_section = self.get_section_score(s, at_timestamp=start)
                post_score_section = self.get_section_score(s, at_timestamp=start + duration)
                section_scorediff = post_score_section - prev_score_section

            results.append(ScoreDiffHistory(
                timestamp=int(start + duration),
                duration=duration,
                mode=gamemode,
                scorediff=post_score - prev_score,
                section=self.catalogue.get_section(section_id=section_id),
                section_scorediff=section_scorediff
            ))
        return results
