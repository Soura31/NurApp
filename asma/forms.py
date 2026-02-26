from django import forms


class AsmaQuizForm(forms.Form):
    answer = forms.CharField(max_length=120)
