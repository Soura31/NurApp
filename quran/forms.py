from django import forms


class QuranFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Recherche")
    revelation_place = forms.ChoiceField(
        required=False,
        choices=[("", "Tous"), ("makkah", "Mecque"), ("madinah", "Medine")],
    )


class VerseActionForm(forms.Form):
    surah_number = forms.IntegerField(min_value=1, max_value=114)
    ayah_number = forms.IntegerField(min_value=1)
    note = forms.CharField(required=False, widget=forms.Textarea)
