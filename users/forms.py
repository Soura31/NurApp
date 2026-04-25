from django import forms

from .models import UserGoal, UserProfile


class ProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "w-full rounded-2xl bg-[#0f1419] border border-[#c9a84c]/35 px-4 py-3 text-white")

    class Meta:
        model = UserProfile
        fields = ["avatar", "city", "country", "preferred_language", "preferred_reciter", "bio", "is_private"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }


class UserGoalForm(forms.ModelForm):
    class Meta:
        model = UserGoal
        fields = ["goal_type", "title", "target_value", "target_months", "reminder_enabled"]
