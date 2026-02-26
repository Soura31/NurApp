from django import forms


class CheckoutForm(forms.Form):
    billing_cycle = forms.ChoiceField(choices=[("monthly", "Mensuel"), ("yearly", "Annuel")])
