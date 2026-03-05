from datetime import date, timedelta

from django.contrib import messages
from django.db.models import Q
from django.views.generic import ListView, TemplateView

from .models import Hadith

DEFAULT_HADITHS = [
    {
        "text_arabic": "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ",
        "text_french": "Les actions ne valent que par leurs intentions.",
        "narrator": "Umar ibn Al-Khattab",
        "source": "Sahih al-Bukhari",
        "reference": "1",
    },
    {
        "text_arabic": "الدِّينُ النَّصِيحَةُ",
        "text_french": "La religion, c'est le conseil sincere.",
        "narrator": "Tamim Ad-Dari",
        "source": "Sahih Muslim",
        "reference": "55",
    },
    {
        "text_arabic": "خَيْرُكُمْ مَنْ تَعَلَّمَ الْقُرْآنَ وَعَلَّمَهُ",
        "text_french": "Le meilleur d'entre vous est celui qui apprend le Coran et l'enseigne.",
        "narrator": "Uthman ibn Affan",
        "source": "Sahih al-Bukhari",
        "reference": "5027",
    },
    {
        "text_arabic": "لَا تَغْضَبْ",
        "text_french": "Ne te mets pas en colere.",
        "narrator": "Abu Hurayra",
        "source": "Sahih al-Bukhari",
        "reference": "6116",
    },
    {
        "text_arabic": "مَنْ لَا يَرْحَمْ لَا يُرْحَمْ",
        "text_french": "Celui qui ne fait pas misericorde ne recevra pas de misericorde.",
        "narrator": "Jarir ibn Abdullah",
        "source": "Sahih Muslim",
        "reference": "2319",
    },
    {
        "text_arabic": "الْكَلِمَةُ الطَّيِّبَةُ صَدَقَةٌ",
        "text_french": "Une bonne parole est une aumone.",
        "narrator": "Abu Hurayra",
        "source": "Sahih al-Bukhari",
        "reference": "2989",
    },
    {
        "text_arabic": "الطُّهُورُ شَطْرُ الإِيمَانِ",
        "text_french": "La purification est la moitie de la foi.",
        "narrator": "Abu Malik Al-Ashari",
        "source": "Sahih Muslim",
        "reference": "223",
    },
    {
        "text_arabic": "يَسِّرُوا وَلَا تُعَسِّرُوا",
        "text_french": "Facilitez et ne rendez pas les choses difficiles.",
        "narrator": "Anas ibn Malik",
        "source": "Sahih al-Bukhari",
        "reference": "69",
    },
    {
        "text_arabic": "تَبَسُّمُكَ فِي وَجْهِ أَخِيكَ لَكَ صَدَقَةٌ",
        "text_french": "Ton sourire envers ton frere est une aumone.",
        "narrator": "Abu Dharr",
        "source": "Jami at-Tirmidhi",
        "reference": "1956",
    },
    {
        "text_arabic": "الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ",
        "text_french": "Le musulman est celui dont les autres musulmans sont a l'abri de sa langue et de sa main.",
        "narrator": "Abdullah ibn Amr",
        "source": "Sahih al-Bukhari",
        "reference": "10",
    },
    {
        "text_arabic": "مَنْ صَمَتَ نَجَا",
        "text_french": "Celui qui se tait est sauve.",
        "narrator": "Abu Hurayra",
        "source": "Jami at-Tirmidhi",
        "reference": "2501",
    },
    {
        "text_arabic": "مَنْ سَلَكَ طَرِيقًا يَلْتَمِسُ فِيهِ عِلْمًا سَهَّلَ اللَّهُ لَهُ بِهِ طَرِيقًا إِلَى الْجَنَّةِ",
        "text_french": "Celui qui suit un chemin pour y rechercher la science, Allah lui facilite un chemin vers le Paradis.",
        "narrator": "Abu Hurayra",
        "source": "Sahih Muslim",
        "reference": "2699",
    },
]


def ensure_default_hadiths():
    if Hadith.objects.exists():
        return
    start_date = date(2026, 1, 1)
    for index, item in enumerate(DEFAULT_HADITHS):
        Hadith.objects.create(
            text_arabic=item["text_arabic"],
            text_french=item["text_french"],
            narrator=item["narrator"],
            source=item["source"],
            reference=item["reference"],
            display_date=start_date + timedelta(days=index),
        )


class HadithOfDayView(TemplateView):
    template_name = "hadith/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ensure_default_hadiths()
        today = date.today()
        hadith = Hadith.objects.filter(display_date=today).first()
        if not hadith:
            all_hadith = list(Hadith.objects.all())
            if all_hadith:
                hadith = all_hadith[today.toordinal() % len(all_hadith)]
            else:
                messages.warning(self.request, "Aucun hadith configure actuellement.")
        context["hadith"] = hadith
        return context


class HadithArchiveView(ListView):
    model = Hadith
    template_name = "hadith/archive.html"
    context_object_name = "hadiths"
    paginate_by = 24

    def get_queryset(self):
        ensure_default_hadiths()
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(text_french__icontains=q)
                | Q(text_arabic__icontains=q)
                | Q(source__icontains=q)
                | Q(reference__icontains=q)
                | Q(narrator__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["total_hadiths"] = Hadith.objects.count()
        return context
