import re
import os
import glob


def fetch_question_answer_pairs(path):
    
    with open(os.path.join(path), 'r', encoding='KOI8-R') as f:
        text = f.read()

    splited_text = text.split('\n\n')
    q_and_a_pairs = {}
    for index_of_answer, may_be_question in enumerate(splited_text, 1):
        if may_be_question.startswith('Вопрос'):

            first_index_of_question = re.search('\d[:]\n', may_be_question).end()
            question = may_be_question[first_index_of_question:]

            full_answer = splited_text[index_of_answer]
            first_index_of_clean_answer = re.search('[:]\n', full_answer).end()
            clean_answer = full_answer[first_index_of_clean_answer:]

            q_and_a_pairs[question] = clean_answer

    return q_and_a_pairs


def main():

    paths = [path for path in glob.glob('QUIZ_CONTENT/*.txt')]
    questions_and_asnwers= {}
    for path in paths:
        q_and_a_from_1_file = fetch_question_answer_pairs(path)
        questions_and_asnwers.update(q_and_a_from_1_file)

    return questions_and_asnwers


if __name__ == "__main__":
  main()
