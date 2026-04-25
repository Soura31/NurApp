from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, time, timedelta
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from django.utils.text import slugify

from asma.models import AsmaName
from quran.models import HifzAssignment

from .hijri import get_today_hijri
from .models import (
    AppNotification,
    BadgeDefinition,
    ChallengeParticipant,
    CollectiveChallenge,
    DailyReadingLog,
    Dua,
    DuaCategory,
    FavoriteDua,
    NotificationPreference,
    RamadanDayLog,
    ReadingGroup,
    ReadingGroupMembership,
    UserBadge,
    UserFollow,
    UserGoal,
)

User = get_user_model()

BADGE_SEED = [
    ("premier-pas", "Premier pas", "Premiere lecture enregistree sur NurCoran.", "fa-solid fa-shoe-prints", "lecture"),
    ("bismillah", "Bismillah", "Debut de parcours spirituel lance avec regularite.", "fa-solid fa-star-and-crescent", "lecture"),
    ("al-fatiha", "Al-Fatiha", "La sourate Al-Fatiha a ete marquee comme lue.", "fa-solid fa-book-open-reader", "lecture"),
    ("juz-amma", "Juz Amma", "Le Juz Amma est complete.", "fa-solid fa-book-quran", "lecture"),
    ("streak-7", "Streak 7 jours", "Sept jours consecutifs de lecture.", "fa-solid fa-fire", "streak"),
    ("streak-30", "Streak 30 jours", "Trente jours consecutifs de lecture.", "fa-solid fa-fire-flame-curved", "streak"),
    ("streak-100", "Streak 100 jours", "Cent jours consecutifs de lecture.", "fa-solid fa-trophy", "streak"),
    ("streak-365", "Streak 365 jours", "Une annee de regularite dans la lecture.", "fa-solid fa-crown", "streak"),
    ("hafiz-debutant", "Hafiz debutant", "Une premiere portion de hifz a ete memorisee.", "fa-solid fa-brain", "hifz"),
    ("khatam", "Khatam", "Le Coran entier a ete complete.", "fa-solid fa-medal", "lecture"),
    ("ramadan", "Ramadan", "Lecture ou suivi actif pendant Ramadan.", "fa-solid fa-moon", "saison"),
    ("partageur", "Partageur", "Une publication a ete partagee dans la communaute.", "fa-solid fa-share-nodes", "social"),
]

DUA_CATEGORY_SEED = [
    ("Matin", "matin"),
    ("Soir", "soir"),
    ("Repas", "repas"),
    ("Voyage", "voyage"),
    ("Famille", "famille"),
    ("Protection", "protection"),
    ("Pardon", "pardon"),
    ("Prophetes", "prophetes"),
    ("Patience", "patience"),
    ("Subsistance", "subsistance"),
]

DUA_PHRASES = {
    "matin": ("اللهم اجعل صباحي نورا وبركة", "Allahumma ij'al sabahi nuran wa barakah", "O Allah, fais de ce matin une lumiere et une benediction."),
    "soir": ("اللهم اجعل مسائي سكينة وامانا", "Allahumma ij'al masa'i sakiinatan wa amanan", "O Allah, fais de cette soiree une source de paix et de securite."),
    "repas": ("اللهم بارك لنا فيما رزقتنا", "Allahumma barik lana fima razaqtana", "O Allah, mets Ta benediction dans ce que Tu nous as accorde."),
    "voyage": ("اللهم هون علينا سفرنا هذا", "Allahumma hawwin alayna safarana hadha", "O Allah, facilite pour nous ce voyage."),
    "famille": ("اللهم اصلح لي اهلي وذريتي", "Allahumma aslih li ahli wa dhurriyati", "O Allah, reforme ma famille et ma descendance."),
    "protection": ("اللهم احفظني من كل سوء", "Allahumma ihfazni min kulli suu", "O Allah, protege-moi de tout mal."),
    "pardon": ("اللهم اغفر لي وارحمني", "Allahumma ighfir li warhamni", "O Allah, pardonne-moi et fais-moi misericorde."),
    "prophetes": ("ربنا اتنا من لدنك رحمة", "Rabbana atina min ladunka rahmah", "Notre Seigneur, accorde-nous une misericorde venant de Toi."),
    "patience": ("اللهم ارزقني الصبر والثبات", "Allahumma urzuqni as-sabra wa ath-thabat", "O Allah, accorde-moi patience et fermete."),
    "subsistance": ("اللهم ارزقني رزقا طيبا واسعا", "Allahumma urzuqni rizqan tayyiban wasi'an", "O Allah, accorde-moi une subsistance pure et abondante."),
}

DUA_VARIATIONS = [
    "pour commencer la journee dans le dhikr",
    "pour garder le coeur serein",
    "pour renforcer la confiance en Allah",
    "pour demander une issue benefique",
    "pour rechercher une protection constante",
    "pour trouver la gratitude",
    "pour rester patient face aux epreuves",
    "pour adoucir la maison et les liens",
    "pour garder la constance dans l'adoration",
    "pour finir la journee avec paix",
]

ASMA_SEED = [
    (1, "ٱلرَّحْمَٰنُ", "Ar-Rahman", "Le Tout Misericordieux"),
    (2, "ٱلرَّحِيمُ", "Ar-Rahim", "Le Tres Misericordieux"),
    (3, "ٱلْمَلِكُ", "Al-Malik", "Le Roi, Le Souverain"),
    (4, "ٱلْقُدُّوسُ", "Al-Quddus", "Le Tres Pur"),
    (5, "ٱلسَّلَامُ", "As-Salam", "La Source de la Paix"),
    (6, "ٱلْمُؤْمِنُ", "Al-Mu'min", "Le Garant de la securite"),
    (7, "ٱلْمُهَيْمِنُ", "Al-Muhaymin", "Le Protecteur, Le Temoignant"),
    (8, "ٱلْعَزِيزُ", "Al-'Aziz", "Le Tout-Puissant"),
    (9, "ٱلْجَبَّارُ", "Al-Jabbar", "Le Contraignant, Le Restaurateur"),
    (10, "ٱلْمُتَكَبِّرُ", "Al-Mutakabbir", "Le Majestueux"),
    (11, "ٱلْخَٰلِقُ", "Al-Khaliq", "Le Createur"),
    (12, "ٱلْبَارِئُ", "Al-Bari", "Le Producteur, L'Initiateur"),
    (13, "ٱلْمُصَوِّرُ", "Al-Musawwir", "Le Formateur"),
    (14, "ٱلْغَفَّارُ", "Al-Ghaffar", "Le Grand Pardonneur"),
    (15, "ٱلْقَهَّارُ", "Al-Qahhar", "Le Dominateur Supreme"),
    (16, "ٱلْوَهَّابُ", "Al-Wahhab", "Le Donateur"),
    (17, "ٱلرَّزَّاقُ", "Ar-Razzaq", "Le Pourvoyeur"),
    (18, "ٱلْفَتَّاحُ", "Al-Fattah", "L'Ouvreur, Le Juge"),
    (19, "ٱلْعَلِيمُ", "Al-'Alim", "L'Omniscient"),
    (20, "ٱلْقَابِضُ", "Al-Qabid", "Celui Qui retient"),
    (21, "ٱلْبَاسِطُ", "Al-Basit", "Celui Qui etend"),
    (22, "ٱلْخَافِضُ", "Al-Khafid", "Celui Qui abaisse"),
    (23, "ٱلرَّافِعُ", "Ar-Rafi'", "Celui Qui eleve"),
    (24, "ٱلْمُعِزُّ", "Al-Mu'izz", "Celui Qui honore"),
    (25, "ٱلْمُذِلُّ", "Al-Mudhill", "Celui Qui humilie"),
    (26, "ٱلسَّمِيعُ", "As-Sami'", "L'Audient"),
    (27, "ٱلْبَصِيرُ", "Al-Basir", "Le Clairvoyant"),
    (28, "ٱلْحَكَمُ", "Al-Hakam", "Le Juge"),
    (29, "ٱلْعَدْلُ", "Al-'Adl", "Le Juste"),
    (30, "ٱللَّطِيفُ", "Al-Latif", "Le Subtil, Le Doux"),
    (31, "ٱلْخَبِيرُ", "Al-Khabir", "Le Bien-Informe"),
    (32, "ٱلْحَلِيمُ", "Al-Halim", "Le Tres Clement"),
    (33, "ٱلْعَظِيمُ", "Al-'Azim", "L'Immense"),
    (34, "ٱلْغَفُورُ", "Al-Ghafur", "Le Pardonneur"),
    (35, "ٱلشَّكُورُ", "Ash-Shakur", "Le Tres Reconnaissant"),
    (36, "ٱلْعَلِيُّ", "Al-'Ali", "Le Tres Haut"),
    (37, "ٱلْكَبِيرُ", "Al-Kabir", "Le Tres Grand"),
    (38, "ٱلْحَفِيظُ", "Al-Hafiz", "Le Protecteur"),
    (39, "ٱلْمُقِيتُ", "Al-Muqit", "Le Nourricier"),
    (40, "ٱلْحَسِيبُ", "Al-Hasib", "Celui Qui tient compte"),
    (41, "ٱلْجَلِيلُ", "Al-Jalil", "Le Majestueux"),
    (42, "ٱلْكَرِيمُ", "Al-Karim", "Le Noble, Le Genereux"),
    (43, "ٱلرَّقِيبُ", "Ar-Raqib", "L'Observateur"),
    (44, "ٱلْمُجِيبُ", "Al-Mujib", "Celui Qui repond"),
    (45, "ٱلْوَاسِعُ", "Al-Wasi'", "L'Immense, L'Infini"),
    (46, "ٱلْحَكِيمُ", "Al-Hakim", "Le Sage"),
    (47, "ٱلْوَدُودُ", "Al-Wadud", "Le Tout-Aimant"),
    (48, "ٱلْمَجِيدُ", "Al-Majid", "Le Glorieux"),
    (49, "ٱلْبَاعِثُ", "Al-Ba'ith", "Le Ressusciteur"),
    (50, "ٱلشَّهِيدُ", "Ash-Shahid", "Le Temoignage Absolu"),
    (51, "ٱلْحَقُّ", "Al-Haqq", "La Verite"),
    (52, "ٱلْوَكِيلُ", "Al-Wakil", "Le Garant"),
    (53, "ٱلْقَوِيُّ", "Al-Qawiyy", "Le Fort"),
    (54, "ٱلْمَتِينُ", "Al-Matin", "L'Inebranlable"),
    (55, "ٱلْوَلِيُّ", "Al-Waliyy", "Le Protecteur Proche"),
    (56, "ٱلْحَمِيدُ", "Al-Hamid", "Le Digne de louange"),
    (57, "ٱلْمُحْصِي", "Al-Muhsi", "Celui Qui denombre tout"),
    (58, "ٱلْمُبْدِئُ", "Al-Mubdi", "L'Initiateur"),
    (59, "ٱلْمُعِيدُ", "Al-Mu'id", "Le Restaurateur"),
    (60, "ٱلْمُحْيِي", "Al-Muhyi", "Le Donneur de vie"),
    (61, "ٱلْمُمِيتُ", "Al-Mumit", "Le Donneur de mort"),
    (62, "ٱلْحَيُّ", "Al-Hayy", "Le Vivant"),
    (63, "ٱلْقَيُّومُ", "Al-Qayyum", "Le Subsistant par Lui-meme"),
    (64, "ٱلْوَاجِدُ", "Al-Wajid", "Celui Qui trouve"),
    (65, "ٱلْمَاجِدُ", "Al-Majid", "Le Noble, Le Glorieux"),
    (66, "ٱلْوَاحِدُ", "Al-Wahid", "L'Unique"),
    (67, "ٱلْأَحَدُ", "Al-Ahad", "L'Un"),
    (68, "ٱلصَّمَدُ", "As-Samad", "L'Absolu"),
    (69, "ٱلْقَادِرُ", "Al-Qadir", "Le Tout-Capable"),
    (70, "ٱلْمُقْتَدِرُ", "Al-Muqtadir", "Le Determinant tout"),
    (71, "ٱلْمُقَدِّمُ", "Al-Muqaddim", "Celui Qui avance"),
    (72, "ٱلْمُؤَخِّرُ", "Al-Mu'akhkhir", "Celui Qui retarde"),
    (73, "ٱلْأَوَّلُ", "Al-Awwal", "Le Premier"),
    (74, "ٱلْآخِرُ", "Al-Akhir", "Le Dernier"),
    (75, "ٱلظَّاهِرُ", "Az-Zahir", "L'Apparent"),
    (76, "ٱلْبَاطِنُ", "Al-Batin", "Le Cache"),
    (77, "ٱلْوَالِي", "Al-Wali", "Le Gouverneur"),
    (78, "ٱلْمُتَعَالِي", "Al-Muta'ali", "Le Tres Eleve"),
    (79, "ٱلْبَرُّ", "Al-Barr", "La Source de tout bien"),
    (80, "ٱلتَّوَابُ", "At-Tawwab", "Celui Qui accueille le repentir"),
    (81, "ٱلْمُنْتَقِمُ", "Al-Muntaqim", "Le Justicier"),
    (82, "ٱلْعَفُوُّ", "Al-'Afuww", "L'Absoluteur"),
    (83, "ٱلرَّءُوفُ", "Ar-Ra'uf", "Le Tres Bienveillant"),
    (84, "مَالِكُ ٱلْمُلْكِ", "Malik al-Mulk", "Le Maitre de la royaute"),
    (85, "ذُو ٱلْجَلَالِ وَٱلْإِكْرَامِ", "Dhul-Jalali wal-Ikram", "Le Detenteur de majeste et de generosite"),
    (86, "ٱلْمُقْسِطُ", "Al-Muqsit", "Le Tres Equitable"),
    (87, "ٱلْجَامِعُ", "Al-Jami'", "Le Rassembleur"),
    (88, "ٱلْغَنِيُّ", "Al-Ghaniyy", "Le Riche, L'Autosuffisant"),
    (89, "ٱلْمُغْنِيُ", "Al-Mughni", "Celui Qui enrichit"),
    (90, "ٱلْمَانِعُ", "Al-Mani'", "Celui Qui empeche"),
    (91, "ٱلضَّارُّ", "Ad-Darr", "Celui Qui eprouve"),
    (92, "ٱلنَّافِعُ", "An-Nafi'", "Celui Qui apporte le bien"),
    (93, "ٱلنُّورُ", "An-Nur", "La Lumiere"),
    (94, "ٱلْهَادِي", "Al-Hadi", "Le Guide"),
    (95, "ٱلْبَدِيعُ", "Al-Badi'", "L'Incomparable Initiateur"),
    (96, "ٱلْبَاقِي", "Al-Baqi", "L'Imperissable"),
    (97, "ٱلْوَارِثُ", "Al-Warith", "L'Heritier"),
    (98, "ٱلرَّشِيدُ", "Ar-Rashid", "Le Guide vers la droiture"),
    (99, "ٱلصَّبُورُ", "As-Sabur", "Le Patient"),
]

HISTORY_TIMELINE = [
    ("Prophetes", "Adam", "Debut de l'humanite et premier prophete."),
    ("Prophetes", "Idris", "Modele d'elevation par le savoir et la droiture."),
    ("Prophetes", "Nuh", "Patience et perseverance dans l'appel."),
    ("Prophetes", "Hud", "Rappel a la justice et a l'humilite."),
    ("Prophetes", "Salih", "Lecon sur les signes et la responsabilite."),
    ("Prophetes", "Ibrahim", "Modele du tawhid et du sacrifice."),
    ("Prophetes", "Lut", "Protection de la morale et de la dignite."),
    ("Prophetes", "Ismail", "Soumission et confiance en Allah."),
    ("Prophetes", "Ishaq", "Transmission de la benediction prophetique."),
    ("Prophetes", "Yaqub", "Patience lumineuse et esperance."),
    ("Prophetes", "Yusuf", "Purete, dignite et pardon."),
    ("Prophetes", "Shuayb", "Justice economique et droiture."),
    ("Prophetes", "Ayyub", "Endurance dans l'epreuve."),
    ("Prophetes", "Dhul-Kifl", "Fidelite dans l'engagement."),
    ("Prophetes", "Musa", "Liberation et loi revelee."),
    ("Prophetes", "Harun", "Soutien fraternel dans la mission."),
    ("Prophetes", "Dawud", "Royaute, justice et louange."),
    ("Prophetes", "Sulayman", "Sagesse et gratitude dans l'autorite."),
    ("Prophetes", "Ilyas", "Rappel contre l'idolatrie."),
    ("Prophetes", "Al-Yasa", "Continuite de l'appel."),
    ("Prophetes", "Yunus", "Retour a Allah et repentance."),
    ("Prophetes", "Zakariya", "Invocation sincere et confiance."),
    ("Prophetes", "Yahya", "Purete et verite."),
    ("Prophetes", "Isa", "Misericorde, miracles et appel."),
    ("Prophetes", "Muhammad ﷺ", "Sceau de la prophetie et misericorde pour les mondes."),
    ("Sira", "Premiere revelation", "Iqra ouvre la mission prophetique."),
    ("Sira", "Hijra", "Migration vers Madinah et naissance de la communaute."),
    ("Sira", "Fath Makkah", "Conquete de Makkah avec pardon et humilite."),
    ("Califes", "Abu Bakr", "Stabilite, verite et unite."),
    ("Califes", "Umar", "Justice et expansion."),
    ("Califes", "Uthman", "Compilation du Mushaf et generosite."),
    ("Califes", "Ali", "Science, courage et sagesse."),
    ("Batailles", "Badr", "Confiance en Allah malgre la faiblesse numerique."),
    ("Batailles", "Uhud", "Lecon d'obeissance et de resilience."),
    ("Batailles", "Khandaq", "Strategie, patience et cohesion."),
]


def ensure_badge_definitions():
    for slug, name, description, icon, category in BADGE_SEED:
        BadgeDefinition.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "description": description, "icon": icon, "category": category},
        )


def ensure_dua_catalog():
    if Dua.objects.exists():
        return

    for order, (name, slug) in enumerate(DUA_CATEGORY_SEED, start=1):
        category, _ = DuaCategory.objects.get_or_create(name=name, slug=slug, defaults={"order": order})
        arabic_text, transliteration, translation = DUA_PHRASES[slug]
        for index, variant in enumerate(DUA_VARIATIONS, start=1):
            title = f"{name} {index}"
            Dua.objects.create(
                category=category,
                title=title,
                arabic_text=arabic_text,
                transliteration=transliteration,
                translation=f"{translation} Cette invocation est proposee {variant}.",
                source="Collection NurCoran",
                share_text=f"{title} - {translation}",
                is_featured=index == 1,
            )


def ensure_asma_catalog():
    if AsmaName.objects.count() >= 99:
        return

    for number, arabic_name, transliteration, meaning in ASMA_SEED:
        AsmaName.objects.update_or_create(
            number=number,
            defaults={
                "name_arabic": arabic_name,
                "transliteration": transliteration,
                "meaning": meaning,
                "explanation": f"Reflechissez au Nom {transliteration} et invoquez Allah par ce sens: {meaning}.",
            },
        )


def ensure_challenge_catalog():
    today = timezone.localdate()
    first_day = today.replace(day=1)
    last_day = today.replace(day=monthrange(today.year, today.month)[1])
    season_titles = [
        ("khatam-collectif-mensuel", "Khatam collectif mensuel", "Objectif commun pour lire ensemble un Khatam complet.", "Mensuel"),
        ("ramadan-solidaire", "Defi Ramadan", "Lire davantage pendant Ramadan et soutenir la constance.", "Ramadan"),
        ("dhul-hijja-lumiere", "Defi Dhul Hijja", "Multiplier les lectures durant les dix jours benis.", "Dhul Hijja"),
        ("muharram-renouveau", "Defi Muharram", "Commencer l'annee hijri avec un elan de lecture.", "Muharram"),
    ]
    for slug, title, description, season in season_titles:
        CollectiveChallenge.objects.get_or_create(
            slug=slug,
            defaults={
                "title": title,
                "description": description,
                "target_value": 6236 if "khatam" in slug else 30000,
                "start_date": first_day,
                "end_date": last_day,
                "season": season,
                "badge_slug": "partageur" if "khatam" in slug else "ramadan",
            },
        )


def ensure_sample_groups():
    leader = User.objects.order_by("id").first()
    if not leader or ReadingGroup.objects.exists():
        return

    seeds = [
        ("Khatam 30 jours", 30, "Terminer le Coran en un mois avec repartition des juz."),
        ("Hifz Juz Amma", 21, "Memorisation collective des petites sourates."),
        ("Lecture Famille", 45, "Progression douce avec suivi commun."),
    ]
    for name, target_days, description in seeds:
        group = ReadingGroup.objects.create(
            name=name,
            slug=slugify(name),
            target_days=target_days,
            description=description,
            creator=leader,
        )
        ReadingGroupMembership.objects.create(group=group, user=leader, role="leader", assigned_juz=1, progress_percent=18)


def ensure_initial_content():
    ensure_badge_definitions()
    ensure_dua_catalog()
    ensure_asma_catalog()
    ensure_challenge_catalog()
    ensure_sample_groups()


def get_or_create_notification_preferences(user):
    return NotificationPreference.objects.get_or_create(user=user)[0]


def create_notification(user, notification_type: str, title: str, body: str, url: str = ""):
    return AppNotification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        body=body,
        url=url,
    )


def build_month_streak_calendar(user, reference_date: date | None = None):
    if not user.is_authenticated:
        return []
    current = reference_date or timezone.localdate()
    total_days = monthrange(current.year, current.month)[1]
    logged_days = set(
        DailyReadingLog.objects.filter(user=user, log_date__year=current.year, log_date__month=current.month).values_list(
            "log_date", flat=True
        )
    )
    calendar = []
    for day in range(1, total_days + 1):
        current_day = current.replace(day=day)
        calendar.append(
            {
                "date": current_day,
                "day": day,
                "is_today": current_day == timezone.localdate(),
                "has_read": current_day in logged_days,
            }
        )
    return calendar


def refresh_streak(user):
    if not user.is_authenticated:
        return 0
    days = list(DailyReadingLog.objects.filter(user=user).order_by("-log_date").values_list("log_date", flat=True))
    if not days:
        if hasattr(user, "userprofile"):
            user.userprofile.streak_days = 0
            user.userprofile.save(update_fields=["streak_days"])
        return 0

    streak = 0
    expected = timezone.localdate()
    if days[0] < expected:
        expected = days[0]

    unique_days = list(dict.fromkeys(days))
    for logged_day in unique_days:
        if logged_day == expected:
            streak += 1
            expected -= timedelta(days=1)
        elif logged_day < expected:
            break

    if hasattr(user, "userprofile") and user.userprofile.streak_days != streak:
        user.userprofile.streak_days = streak
        user.userprofile.save(update_fields=["streak_days"])
    return streak


def _update_goals(user, verses_read: int):
    goals = UserGoal.objects.filter(user=user, is_active=True).order_by("created_at")
    if goals.count() > 3:
        goals = goals[:3]

    from quran.services import get_progress_snapshot

    snapshot = get_progress_snapshot(user)
    mastered_count = HifzAssignment.objects.filter(user=user, is_mastered=True).count()
    today_log = DailyReadingLog.objects.filter(user=user, log_date=timezone.localdate()).first()
    for goal in goals:
        if goal.goal_type == "verses_day":
            goal.current_value = today_log.verses_read if today_log else 0
        elif goal.goal_type == "finish_quran":
            goal.current_value = snapshot["read_surah_count"]
        elif goal.goal_type == "memorize_surahs":
            goal.current_value = mastered_count
        if goal.current_value >= goal.target_value:
            goal.is_active = False
            create_notification(
                user,
                "reading",
                f"Objectif atteint: {goal.title or goal.get_goal_type_display()}",
                "Votre objectif spirituel a ete complete.",
                "/dashboard/",
            )
        goal.save(update_fields=["current_value", "is_active", "updated_at"])


def evaluate_user_badges(user):
    if not user.is_authenticated:
        return []

    ensure_badge_definitions()
    from community.models import ForumPost
    from quran.services import get_progress_snapshot

    snapshot = get_progress_snapshot(user)
    read_ids = set(snapshot["read_surah_ids"])
    streak = refresh_streak(user)
    in_ramadan = False
    today_hijri = get_today_hijri()
    if today_hijri:
        in_ramadan = today_hijri.get("hijri_month_number") == 9

    conditions = {
        "premier-pas": DailyReadingLog.objects.filter(user=user).exists(),
        "bismillah": DailyReadingLog.objects.filter(user=user).exists(),
        "al-fatiha": 1 in read_ids,
        "juz-amma": all(number in read_ids for number in range(78, 115)),
        "streak-7": streak >= 7,
        "streak-30": streak >= 30,
        "streak-100": streak >= 100,
        "streak-365": streak >= 365,
        "hafiz-debutant": HifzAssignment.objects.filter(user=user, is_mastered=True).exists()
        or HifzAssignment.objects.filter(user=user).exists(),
        "khatam": snapshot["read_surah_count"] >= snapshot["total_surahs"],
        "ramadan": in_ramadan and DailyReadingLog.objects.filter(user=user).exists(),
        "partageur": ForumPost.objects.filter(author=user).exists(),
    }

    unlocked = []
    for badge in BadgeDefinition.objects.all():
        if not conditions.get(badge.slug):
            continue
        user_badge, created = UserBadge.objects.get_or_create(user=user, badge=badge)
        if created:
            unlocked.append(user_badge)
            create_notification(
                user,
                "badge",
                f"Badge debloque: {badge.name}",
                badge.description,
                "/badges/",
            )
    return unlocked


def record_daily_reading(user, verses_read: int = 0, surah_number: int | None = None):
    if not user.is_authenticated:
        return None

    ensure_initial_content()
    today = timezone.localdate()
    log, _ = DailyReadingLog.objects.get_or_create(user=user, log_date=today)
    if verses_read:
        log.verses_read += max(0, verses_read)
    if surah_number and surah_number not in log.surahs_completed:
        log.surahs_completed = [*log.surahs_completed, surah_number]
    log.save()

    if hasattr(user, "userprofile") and verses_read:
        user.userprofile.total_verses_read += max(0, verses_read)
        user.userprofile.save(update_fields=["total_verses_read"])

    streak = refresh_streak(user)
    _update_goals(user, verses_read)
    unlocked = evaluate_user_badges(user)
    _update_challenges(user, verses_read)

    if streak in {7, 30, 100, 365}:
        create_notification(
            user,
            "streak",
            f"Felicitations, {streak} jours de streak",
            "Continuez votre lecture quotidienne avec constance.",
            "/dashboard/",
        )

    return {"log": log, "streak": streak, "unlocked": unlocked}


def _update_challenges(user, verses_read: int):
    if verses_read <= 0:
        return
    today = timezone.localdate()
    for challenge in CollectiveChallenge.objects.filter(start_date__lte=today, end_date__gte=today):
        participant, _ = ChallengeParticipant.objects.get_or_create(challenge=challenge, user=user)
        participant.contribution += verses_read
        participant.save(update_fields=["contribution", "updated_at"])
        challenge.current_value += verses_read
        challenge.save(update_fields=["current_value"])


def get_daily_dua():
    ensure_dua_catalog()
    duas = list(Dua.objects.select_related("category").all())
    if not duas:
        return None
    return duas[timezone.localdate().timetuple().tm_yday % len(duas)]


def get_daily_name_of_allah():
    ensure_asma_catalog()
    names = list(AsmaName.objects.order_by("number"))
    if not names:
        return None
    return names[(timezone.localdate().timetuple().tm_yday - 1) % len(names)]


def get_or_create_ramadan_log(user, hijri_year: int):
    logs = {
        item.day_number: item
        for item in RamadanDayLog.objects.filter(user=user, hijri_year=hijri_year).order_by("day_number")
    }
    for day_number in range(1, 31):
        if day_number not in logs:
            logs[day_number] = RamadanDayLog.objects.create(user=user, hijri_year=hijri_year, day_number=day_number)
    return [logs[index] for index in range(1, 31)]


def get_pending_notifications(user):
    if not user.is_authenticated:
        return []
    return list(user.app_notifications.filter(is_read=False)[:6])


def ensure_daily_reminders(user):
    if not user.is_authenticated:
        return []

    preferences = get_or_create_notification_preferences(user)
    now = timezone.localtime()
    today = now.date()
    notifications = []
    if (
        preferences.daily_reading
        and now.hour >= preferences.reminder_hour
        and not DailyReadingLog.objects.filter(user=user, log_date=today).exists()
    ):
        if not AppNotification.objects.filter(
            user=user,
            notification_type="reading",
            title__icontains=today.isoformat(),
            created_at__date=today,
        ).exists():
            notifications.append(
                create_notification(
                    user,
                    "reading",
                    f"Lecture quotidienne - {today.isoformat()}",
                    "Il est temps de lire quelques versets avant la fin de la journee.",
                    "/quran/",
                )
            )

    if preferences.morning_dua and now.hour >= 7 and now.hour < 12:
        if not AppNotification.objects.filter(user=user, notification_type="dua", created_at__date=today).exists():
            notifications.append(
                create_notification(
                    user,
                    "dua",
                    f"Dua du jour - {today.isoformat()}",
                    "Commencez la journee avec une invocation inspirante.",
                    "/duas/",
                )
            )
    return notifications


def get_profile_summary(user):
    if not user.is_authenticated:
        return {}

    from community.models import ForumPost
    from quran.models import HifzAssignment
    from quran.services import get_progress_snapshot

    snapshot = get_progress_snapshot(user)
    return {
        "streak": refresh_streak(user),
        "badges": user.badges.select_related("badge")[:6],
        "badge_count": user.badges.count(),
        "posts_count": ForumPost.objects.filter(author=user).count(),
        "memorized_count": HifzAssignment.objects.filter(user=user, is_mastered=True).count(),
        "quran_progress": snapshot,
        "followers_count": UserFollow.objects.filter(following=user).count(),
        "following_count": UserFollow.objects.filter(follower=user).count(),
    }


def get_active_challenges():
    ensure_challenge_catalog()
    today = timezone.localdate()
    return CollectiveChallenge.objects.filter(end_date__gte=today).order_by("end_date")


def get_global_verse_counter():
    return DailyReadingLog.objects.aggregate(total=Sum("verses_read")).get("total") or 0


def can_create_goal(user):
    return UserGoal.objects.filter(user=user, is_active=True).count() < 3
