from apps.questionbank.models.question_models import (
    QuestionAttemptResponse,
    QuestionChoice,
    QuestionMedia,
    QuestionRetryHint,
    QuestionSubject,
    QuestionTag,
)
from apps.user.utils.utils import get_current_user_organization
from middlewares.current_user_middleware import get_current_user
from utils.rna_utils import debug_print


class QuestionClone:
    def init(self):
        pass

    def clone_question(self, original_question):
        cloned_question = self._clone_question_instance(original_question)
        self._clone_related_entities(original_question, cloned_question)
        return cloned_question

    def _clone_question_instance(self, instance):
        instance.pk = None
        organization_id = None
        if not get_current_user().is_superuser:  # type: ignore
            organization_id = get_current_user_organization()
        instance.organization_id = organization_id
        instance.save()
        return instance

    def _clone_related_entities(self, original_question, cloned_question):
        self._clone_medias(original_question, cloned_question)
        self._clone_subjects(original_question, cloned_question)
        self._clone_choices(original_question, cloned_question)
        self._clone_retry_hints(original_question, cloned_question)
        self._clone_attempt_responses(original_question, cloned_question)
        self._clone_tags(original_question, cloned_question)

    def _clone_subjects(self, original_question, cloned_question):
        subjects = original_question.subjects.all()
        cloned_subjects = [
            QuestionSubject(
                question=cloned_question,
                subject_education_level=subject.subject_education_level,
                difficulty_level=subject.difficulty_level,
                measuring_unit=subject.measuring_unit,
                time_limit=subject.time_limit,
                total_marks=subject.total_marks,
                is_optional=subject.is_optional,
                is_global=subject.is_global,
            )
            for subject in subjects
        ]
        QuestionSubject.objects.bulk_create(cloned_subjects)
        newly_cloned_subjects = QuestionSubject.objects.filter(question=cloned_question)
        self._clone_subject_countries(subjects, newly_cloned_subjects)

    def _clone_subject_countries(self, original_subjects, cloned_subjects):
        for original_subject, cloned_subject in zip(original_subjects, cloned_subjects):
            cloned_subject.countries.set(original_subject.countries.all())

    def _clone_attempt_responses(self, original_question, cloned_question):
        attempt_responses = original_question.attempt_responses.all()
        cloned_attempt_responses = [
            QuestionAttemptResponse(
                question=cloned_question,
                text=attempt_response.text,
                type=attempt_response.type,
            )
            for attempt_response in attempt_responses
        ]
        QuestionAttemptResponse.objects.bulk_create(cloned_attempt_responses)

    def _clone_choices(self, original_question, cloned_question):
        choices = original_question.choices.all()
        cloned_choices = [
            QuestionChoice(
                question=cloned_question,
                title=choice.title,
                text=choice.text,
                weight=choice.weight,
                is_negative_weight=choice.is_negative_weight,
                is_correct=choice.is_correct,
                has_media=choice.has_media,
            )
            for choice in choices
        ]
        QuestionChoice.objects.bulk_create(cloned_choices)
        newly_cloned_choices = QuestionChoice.objects.filter(question=cloned_question)
        self._clone_choice_media(choices, newly_cloned_choices)

    def _clone_choice_media(self, original_choices, cloned_choices):
        for original_choice, cloned_choice in zip(original_choices, cloned_choices):
            cloned_choice.medias.set(original_choice.medias.all())

    def _clone_retry_hints(self, original_question, cloned_question):
        retry_hints = original_question.retry_hints.all()
        cloned_retry_hints = [
            QuestionRetryHint(
                question=cloned_question,
                text=retry_hint.text,
                sequence=retry_hint.sequence,
                has_media=retry_hint.has_media,
            )
            for retry_hint in retry_hints
        ]
        QuestionRetryHint.objects.bulk_create(cloned_retry_hints)
        newly_cloned_retry_hints = QuestionRetryHint.objects.filter(question=cloned_question)
        self._clone_retry_hint_media(retry_hints, newly_cloned_retry_hints)

    def _clone_retry_hint_media(self, original_retry_hints, cloned_retry_hints):
        for original_retry_hint, cloned_retry_hint in zip(original_retry_hints, cloned_retry_hints):
            cloned_retry_hint.medias.set(original_retry_hint.medias.all())

    def _clone_tags(self, original_question, cloned_question):
        tags = original_question.tags.all()
        cloned_tags = [
            QuestionTag(
                question=cloned_question,
                tag=tag,
            )
            for tag in tags
        ]
        QuestionTag.objects.bulk_create(cloned_tags)

    def _clone_medias(self, original_question, cloned_question):
        medias = original_question.medias.all()
        cloned_medias = [
            QuestionMedia(
                question=cloned_question,
                media=media,
            )
            for media in medias
        ]
        QuestionMedia.objects.bulk_create(cloned_medias)
