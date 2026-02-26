from django.views.generic import TemplateView

from subscriptions.models import Plan


class LandingPageView(TemplateView):
    template_name = "landing/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plans"] = Plan.objects.all()
        context["features"] = [
            "Coran avec traductions multiplies",
            "Horaires de priere geolocalises",
            "Audio recitateurs premium",
            "Azkar avec compteur intelligent",
            "Forum communaute modere",
            "Dashboard spirituel personnel",
        ]
        context["testimonials"] = [
            {"name": "Amina B.", "text": "NurCoran m'aide a rester reguliere dans mes rappels."},
            {"name": "Moussa D.", "text": "Le suivi des prieres est clair et motive toute la famille."},
            {"name": "Fatou K.", "text": "Les recitations audio ont transforme mon apprentissage."},
        ]
        context["faqs"] = [
            ("Puis-je commencer gratuitement ?", "Oui, le plan Free est disponible sans carte bancaire."),
            ("La devise est-elle en FCFA ?", "Oui, tous les montants sont affiches en FCFA."),
            ("Comment annuler un abonnement ?", "Via le portail client Stripe accessible dans le dashboard."),
            ("Les contenus premium sont-ils immediats ?", "Oui, activation automatique apres paiement valide."),
            ("Puis-je utiliser NurCoran sur mobile ?", "Oui, toute l'interface est responsive mobile-first."),
        ]
        return context

