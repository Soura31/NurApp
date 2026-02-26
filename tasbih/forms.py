from django import forms


class TasbihSessionForm(forms.Form):
    dhikr_text = forms.CharField(max_length=150)
    target = forms.IntegerField(min_value=1, initial=33)
    count = forms.IntegerField(min_value=0, initial=0)
