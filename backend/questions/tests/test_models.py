from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from questions.models import AnswerOption, Category, ChoiceQuestion, NumericQuestion


def add_options(question, correct_flags):
    for index, is_correct in enumerate(correct_flags, start=1):
        AnswerOption.objects.create(
            question=question, text=f"Отговор {index}", is_correct=is_correct
        )


class CategoryModelTests(TestCase):
    def test_create_category_with_valid_name(self):
        category = Category.objects.create(name="История")

        category.full_clean()
        self.assertEqual(str(category), "История")

    def test_name_is_required(self):
        with self.assertRaises(ValidationError):
            Category(name="").full_clean()

    def test_name_must_be_unique(self):
        Category.objects.create(name="История")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Category.objects.create(name="История")

    def test_duplicate_name_fails_validation(self):
        Category.objects.create(name="История")

        with self.assertRaises(ValidationError):
            Category(name="История").full_clean()

    def test_category_with_choice_questions_cannot_be_deleted(self):
        category = Category.objects.create(name="История")
        ChoiceQuestion.objects.create(category=category, text="Въпрос?")

        with self.assertRaises(ProtectedError):
            category.delete()
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())

    def test_category_with_numeric_questions_cannot_be_deleted(self):
        category = Category.objects.create(name="История")
        NumericQuestion.objects.create(
            category=category, text="Въпрос?", correct_answer=1878
        )

        with self.assertRaises(ProtectedError):
            category.delete()
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())

    def test_category_without_questions_can_be_deleted(self):
        category = Category.objects.create(name="История")

        category.delete()

        self.assertEqual(Category.objects.count(), 0)


class ChoiceQuestionModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="География")

    def make_question(self):
        return ChoiceQuestion.objects.create(
            category=self.category, text="Коя е столицата на Австралия?"
        )

    def test_create_valid_choice_question(self):
        question = self.make_question()
        add_options(question, [False, False, False, True])

        question.full_clean()
        self.assertEqual(question.category, self.category)
        self.assertEqual(question.text, "Коя е столицата на Австралия?")
        self.assertEqual(question.answer_options.count(), 4)
        self.assertEqual(question.answer_options.filter(is_correct=True).count(), 1)
        self.assertIn(question, self.category.choicequestions.all())

    def test_text_is_required(self):
        with self.assertRaises(ValidationError):
            ChoiceQuestion(category=self.category, text="").full_clean()

    def test_category_is_required(self):
        with self.assertRaises(ValidationError):
            ChoiceQuestion(text="Въпрос?").full_clean()

    def test_fewer_than_four_options_is_invalid(self):
        question = self.make_question()
        add_options(question, [True, False, False])

        with self.assertRaises(ValidationError):
            question.full_clean()

    def test_more_than_four_options_is_invalid(self):
        question = self.make_question()
        add_options(question, [True, False, False, False, False])

        with self.assertRaises(ValidationError):
            question.full_clean()

    def test_no_correct_option_is_invalid(self):
        question = self.make_question()
        add_options(question, [False, False, False, False])

        with self.assertRaises(ValidationError):
            question.full_clean()

    def test_more_than_one_correct_option_is_invalid(self):
        question = self.make_question()
        add_options(question, [True, True, False, False])

        with self.assertRaises(ValidationError):
            question.full_clean()

    def test_deleting_question_deletes_its_options(self):
        question = self.make_question()
        add_options(question, [True, False, False, False])

        question.delete()

        self.assertEqual(AnswerOption.objects.count(), 0)

    def test_choice_question_has_no_correct_answer_field(self):
        field_names = {field.name for field in ChoiceQuestion._meta.get_fields()}

        self.assertNotIn("correct_answer", field_names)


class NumericQuestionModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="История")

    def test_create_valid_numeric_question(self):
        question = NumericQuestion.objects.create(
            category=self.category,
            text="През коя година е Освобождението на България?",
            correct_answer=1878,
        )

        question.full_clean()
        self.assertEqual(question.category, self.category)
        self.assertEqual(question.correct_answer, 1878)
        self.assertIn(question, self.category.numericquestions.all())

    def test_correct_answer_is_required(self):
        with self.assertRaises(ValidationError):
            NumericQuestion(category=self.category, text="Въпрос?").full_clean()

    def test_correct_answer_must_be_an_integer(self):
        with self.assertRaises(ValidationError):
            NumericQuestion(
                category=self.category, text="Въпрос?", correct_answer="много"
            ).full_clean()

    def test_text_is_required(self):
        with self.assertRaises(ValidationError):
            NumericQuestion(
                category=self.category, text="", correct_answer=1
            ).full_clean()


class AnswerOptionModelTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Наука")
        self.question = ChoiceQuestion.objects.create(
            category=category, text="Кой е химичният символ на златото?"
        )

    def test_is_correct_defaults_to_false(self):
        option = AnswerOption.objects.create(question=self.question, text="Ag")

        self.assertFalse(option.is_correct)
        self.assertEqual(str(option), "Ag")

    def test_text_is_required(self):
        with self.assertRaises(ValidationError):
            AnswerOption(question=self.question, text="").full_clean()

    def test_option_belongs_to_a_choice_question(self):
        field = AnswerOption._meta.get_field("question")

        self.assertIs(field.related_model, ChoiceQuestion)
