from django import forms

from .models import ForumPost, ForumReply


class ForumPostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ["category", "title", "content"]


class ForumReplyForm(forms.ModelForm):
    class Meta:
        model = ForumReply
        fields = ["content"]
