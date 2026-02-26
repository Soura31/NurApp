from django import forms


class ZikrCounterForm(forms.Form):
    increment = forms.IntegerField(min_value=1, initial=1)
