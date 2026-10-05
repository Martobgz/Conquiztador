from django.contrib import admin
from django.forms.models import BaseInlineFormSet

from .models import AnswerOption, Category, ChoiceQuestion, NumericQuestion


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class AnswerOptionFormSet(BaseInlineFormSet):
    """Applies the four-options, one-correct rule to the submitted options."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        correct_flags = [
            form.cleaned_data.get("is_correct", False)
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        ChoiceQuestion.validate_options(correct_flags)


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    formset = AnswerOptionFormSet
    extra = ChoiceQuestion.REQUIRED_OPTIONS
    max_num = ChoiceQuestion.REQUIRED_OPTIONS


@admin.register(ChoiceQuestion)
class ChoiceQuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "category")
    list_filter = ("category",)
    search_fields = ("text",)
    inlines = (AnswerOptionInline,)


@admin.register(NumericQuestion)
class NumericQuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "category", "correct_answer")
    list_filter = ("category",)
    search_fields = ("text",)
