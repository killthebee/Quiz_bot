import sys
import io
import re
import os
import glob


sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')
#Если не форсить, то у меня начинаются проблемы с кирилицей


def fetch_question_answer_pairs(path):
    with open(os.path.join(path), 'r', encoding='KOI8-R') as f:
        texts = f.read()

    splited_texts = texts.split('\n\n')

    q_and_a_pairs = {}
    for index_of_answer, may_be_question in enumerate(splited_texts, 1):
        if may_be_question.startswith('Вопрос'):
            first_index_of_question = re.search('\d[:]\n', may_be_question).end()
            question = may_be_question[first_index_of_question:]
            first_index_of_answer = re.search('[:]\n', splited_texts[index_of_answer]).end()
            try:
                z = splited_texts[index_of_answer].index('.')
                answer = splited_texts[index_of_answer][first_index_of_answer:z]
            except ValueError:
                answer = splited_texts[index_of_answer][first_index_of_answer:]
            addon = {question: answer}
            q_and_a_pairs.update(addon)
    return q_and_a_pairs


def fetch_paths():

    paths = []
    for filename in glob.glob('CONTENT/*.txt'):
        paths.append(filename)
    return paths

def main():

    paths = fetch_paths()
    questions_and_asnwers= {}
    for path in paths:
        q_and_a_from_1_file = fetch_question_answer_pairs(path)
        questions_and_asnwers.update(q_and_a_from_1_file)
    return questions_and_asnwers
