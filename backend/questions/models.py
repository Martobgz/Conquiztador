from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    """A topic that questions belong to, e.g. History or Geography."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class BaseQuestion(models.Model):
    """Fields shared by every kind of question. Has no table of its own."""

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="%(class)ss",
    )
    text = models.TextField()

    class Meta:
        abstract = True

    def __str__(self):
        return self.text


class ChoiceQuestion(BaseQuestion):
    """A question with four answer options, exactly one of them correct."""

    REQUIRED_OPTIONS = 4

    @classmethod
    def validate_options(cls, correct_flags):
        """Check a list of is_correct values against the four-options rule."""
        errors = []
        if len(correct_flags) != cls.REQUIRED_OPTIONS:
            errors.append(
                f"A choice question needs exactly {cls.REQUIRED_OPTIONS} "
                f"answer options, not {len(correct_flags)}."
            )
        correct_count = sum(1 for flag in correct_flags if flag)
        if correct_count != 1:
            errors.append(
                "A choice question needs exactly one correct answer option, "
                f"not {correct_count}."
            )
        if errors:
            raise ValidationError(errors)

    def clean(self):
        super().clean()
        # Options point at the question, so an unsaved question has none yet.
        # The admin checks the submitted options through the inline formset.
        if self.pk is None:
            return
        self.validate_options(
            list(self.answer_options.values_list("is_correct", flat=True))
        )


class NumericQuestion(BaseQuestion):
    """A question answered with a whole number."""

    correct_answer = models.IntegerField()


class AnswerOption(models.Model):
    """One of the four possible answers to a choice question."""

    question = models.ForeignKey(
        ChoiceQuestion,
        on_delete=models.CASCADE,
        related_name="answer_options",
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text
