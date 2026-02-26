from django import forms


class DashboardFilterForm(forms.Form):
    period = forms.ChoiceField(required=False, choices=[("7", "7 jours"), ("30", "30 jours")])
