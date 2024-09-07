import streamlit as st
import json
import re
import random

# Define the QuestionBank class
class QuestionBank:
    def __init__(self, questions):
        self.questions = questions
        self.all_tags = self.extract_tags()

    def extract_tags(self):
        # Extract unique tags from the questions and sort them alphabetically
        tags = set()
        for question in self.questions:
            tags.add(question.get('tag', ''))
        return sorted(list(tags))

    def get_questions_by_tags(self, tags):
        # Return questions that match any of the given tags
        return [q for q in self.questions if q.get('tag', '') in tags]

# Load questions from the JSON file
def load_questions_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Extract relevant fields from the JSON structure
    questions = [
        {
            'id': item['id'],
            'question': item['question'],
            'answer': item['answer'],
            'tag': item['tag']
        }
        for item in data['data']
    ]
    return questions

# Initialize the question bank with data from the JSON file
questions_data = load_questions_from_json(r'MedQA_BERT_tagged.json')
question_bank = QuestionBank(questions_data)

# Initialize session state
if 'user_authenticated' not in st.session_state:
    st.session_state.user_authenticated = False
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'question_index' not in st.session_state:
    st.session_state.question_index = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'selected_questions' not in st.session_state:
    st.session_state.selected_questions = []

def main():
    st.title("Quiz Application")

    if not st.session_state.user_authenticated:
        login_view()
    elif not st.session_state.selected_questions:
        tag_list()
    elif st.session_state.question_index < len(st.session_state.selected_questions):
        question_detail()
    else:
        quiz_summary()

def login_view():
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login", key="login_button"):
        if username == "admin" and password == "password":
            st.session_state.user_authenticated = True
            st.success("Logged in successfully!")
        else:
            st.error("Invalid credentials")

def tag_list():
    st.header("Select Tags")

    # Create two columns: one for the dropdown and one for the question count
    col1, col2 = st.columns([3, 1])

    with col1:
        selected_tags = st.multiselect("Choose tags", options=question_bank.all_tags)

    with col2:
        if selected_tags:
            # Calculate the total number of questions for the selected tags
            total_questions = len(question_bank.get_questions_by_tags(selected_tags))
            st.write(f"Total questions: {total_questions}")
        else:
            st.write("No tags selected")

    if st.button("Start Quiz", key="start_quiz_button"):
        questions = question_bank.get_questions_by_tags(selected_tags)
        if questions:
            random.shuffle(questions)  # Randomize the order of questions
            st.session_state.selected_questions = questions
            st.session_state.question_index = 0
            st.session_state.user_answers = {}
            st.rerun()
        else:
            st.error("No questions available for the selected tags.")

def question_detail():
    question = st.session_state.selected_questions[st.session_state.question_index]
    match = re.match(r'(.*?)\s*([A-E]:\s*.*(?:\s*[A-E]:\s*.*)*)$', question['question'], re.DOTALL)
    if match:
        question_text = match.group(1).strip()
        choices_text = match.group(2)
    else:
        question_text = question['question']
        choices_text = ""

    answers = re.findall(r'([A-E]):\s*(.*?)(?=\s*[A-E]:|$)', choices_text, re.DOTALL)
    answers = [{'letter': letter.strip(), 'text': text.strip().rstrip(',').strip()} for letter, text in answers]

    st.subheader(f"Question {st.session_state.question_index + 1} of {len(st.session_state.selected_questions)}")
    st.write(question_text)

    user_answer = st.radio("Select your answer:", options=[f"{a['letter']}: {a['text']}" for a in answers], key=f"radio_{st.session_state.question_index}")

    progress = (st.session_state.question_index + 1) / len(st.session_state.selected_questions)
    st.progress(progress)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Previous", key="prev_button") and st.session_state.question_index > 0:
            st.session_state.question_index -= 1
            #st.rerun()
    with col2:
        if st.button("Submit", key="submit_button"):
            correct_answer = question['answer']
            is_correct = user_answer.split(':')[0].strip() == correct_answer
            st.session_state.user_answers[st.session_state.question_index] = user_answer.split(':')[0].strip()
            if is_correct:
                st.success("Correct!")
            else:
                st.error(f"Incorrect. The correct answer is {correct_answer}.")
    with col3:
        if st.button("Next", key="next_button"):
            if st.session_state.question_index < len(st.session_state.selected_questions) - 1:
                st.session_state.question_index += 1
            else:
                st.session_state.question_index = len(st.session_state.selected_questions)
            st.rerun()

def quiz_summary():
    st.header("Quiz Summary")
    total_questions = len(st.session_state.selected_questions)
    answered_questions = len(st.session_state.user_answers)
    correct_answers = sum(1 for i, q in enumerate(st.session_state.selected_questions) if st.session_state.user_answers.get(i) == q['answer'])
    incorrect_answers = answered_questions - correct_answers
    percent_correct = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    st.write(f"Total Questions: {total_questions}")
    st.write(f"Answered Questions: {answered_questions}")
    st.write(f"Correct Answers: {correct_answers}")
    st.write(f"Incorrect Answers: {incorrect_answers}")
    st.write(f"Percentage Correct: {percent_correct:.2f}%")

    if st.button("Start New Quiz", key="new_quiz_button"):
        st.session_state.questions = []
        st.session_state.question_index = 0
        st.session_state.user_answers = {}
        st.session_state.selected_questions = []
        st.rerun()

if __name__ == "__main__":
    main()
