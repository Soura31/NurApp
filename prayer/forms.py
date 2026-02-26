from django import forms


class PrayerCityForm(forms.Form):
    city = forms.CharField(max_length=120)
    country = forms.CharField(max_length=2, initial="SN")
