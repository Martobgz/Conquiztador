from django.test import TestCase

from questions.models import AnswerOption, Category, ChoiceQuestion, NumericQuestion


class QuestionBankFixtureTests(TestCase):
    fixtures = ["questions/question_bank.json"]

    def test_fixture_loads_expected_counts(self):
        self.assertEqual(Category.objects.count(), 6)
        self.assertEqual(ChoiceQuestion.objects.count(), 12)
        self.assertEqual(AnswerOption.objects.count(), 48)
        self.assertEqual(NumericQuestion.objects.count(), 12)

    def test_every_choice_question_has_four_options(self):
        for question in ChoiceQuestion.objects.all():
            with self.subTest(question=question.pk):
                self.assertEqual(question.answer_options.count(), 4)

    def test_every_choice_question_has_exactly_one_correct_option(self):
        for question in ChoiceQuestion.objects.all():
            with self.subTest(question=question.pk):
                self.assertEqual(
                    question.answer_options.filter(is_correct=True).count(), 1
                )

    def test_every_numeric_question_has_an_integer_answer(self):
        for question in NumericQuestion.objects.all():
            with self.subTest(question=question.pk):
                self.assertIsInstance(question.correct_answer, int)

    def test_every_record_passes_model_validation(self):
        for model in (Category, ChoiceQuestion, NumericQuestion, AnswerOption):
            for obj in model.objects.all():
                with self.subTest(model=model.__name__, pk=obj.pk):
                    obj.full_clean()

    def test_every_category_has_both_kinds_of_questions(self):
        for category in Category.objects.all():
            with self.subTest(category=category.name):
                self.assertTrue(category.choicequestions.exists())
                self.assertTrue(category.numericquestions.exists())
