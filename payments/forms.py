from django import forms


class PaymentFilterForm(forms.Form):
    status = forms.ChoiceField(required=False, choices=[("", "Tous"), ("succeeded", "Reussi"), ("failed", "Echoue")])
