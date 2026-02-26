from django import forms


class HadithSearchForm(forms.Form):
    q = forms.CharField(required=False)
