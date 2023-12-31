import os


def get_questions_answers(filepath):
    files = os.listdir(filepath)
    questions = []
    answers = []
    for file in files:
        with open(os.path.join(filepath, file), 'r', encoding="KOI8-R") as file:
            file_content = file.read()
        blocks = file_content.split('\n\n')
        for block in blocks:
            if block.startswith('Вопрос'):
                question_lines = block.split('\n')[1:]
                questions.append(''.join(question_lines))
            elif block.startswith('Ответ'):
                answer_lines = block.split('\n')[1:]
                answers.append(''.join(answer_lines))

    questions_answers = dict(zip(questions, answers))
    return questions_answers
