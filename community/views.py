from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from .forms import ForumPostForm, ForumReplyForm
from .models import ForumCategory, ForumPost, ForumReply


class CommunityHomeView(ListView):
    model = ForumCategory
    template_name = "community/feed.html"
    context_object_name = "categories"

    def get_queryset(self):
        # Initialise des categories par defaut si la base est vide.
        if not ForumCategory.objects.exists():
            defaults = [
                ("Entraide generale", "entraide-generale", "Questions et entraide quotidienne", "💬", False, 1),
                ("Questions islamiques", "questions-islamiques", "Demandes autour des pratiques", "❓", False, 2),
                ("Annonces", "annonces", "Informations importantes", "📢", False, 3),
                ("Partage spirituel", "partage-spirituel", "Rappels et inspirations", "🌟", False, 4),
                ("Premium", "premium", "Espace reserve aux abonnes", "👑", True, 5),
            ]
            for name, slug, description, icon, is_premium, order in defaults:
                ForumCategory.objects.create(
                    name=name,
                    slug=slug,
                    description=description,
                    icon=icon,
                    is_premium=is_premium,
                    order=order,
                )
        return ForumCategory.objects.all()


class CategoryPostsView(ListView):
    model = ForumPost
    template_name = "community/category_posts.html"
    context_object_name = "posts"

    def get_queryset(self):
        self.category = get_object_or_404(ForumCategory, slug=self.kwargs["slug"])
        if self.category.is_premium:
            user = self.request.user
            is_premium = user.is_authenticated and hasattr(user, "userprofile") and user.userprofile.is_premium
            if not is_premium:
                return ForumPost.objects.none()
        return ForumPost.objects.filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


class ForumPostDetailView(DetailView):
    model = ForumPost
    template_name = "community/post_detail.html"
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reply_form"] = ForumReplyForm()
        return context


class ForumPostCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = ForumPostForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data["category"]
            if category.is_premium and not request.user.userprofile.is_premium:
                messages.error(request, "Categorie reservee aux membres Premium.")
                return redirect("community:home")
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Publication ajoutee.")
            return redirect("community:post_detail", pk=post.id)
        messages.error(request, "Formulaire invalide.")
        return redirect("community:home")


class ForumReplyCreateView(LoginRequiredMixin, View):
    def post(self, request, post_id):
        post = get_object_or_404(ForumPost, id=post_id)
        form = ForumReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.post = post
            reply.author = request.user
            reply.save()
            messages.success(request, "Reponse publiee.")
        else:
            messages.error(request, "Impossible d'ajouter la reponse.")
        return redirect("community:post_detail", pk=post.id)


class ForumPostReportView(LoginRequiredMixin, View):
    def post(self, request, post_id):
        post = get_object_or_404(ForumPost, id=post_id)
        post.is_reported = True
        post.save(update_fields=["is_reported"])
        messages.warning(request, "Contenu signale aux moderateurs.")
        return redirect("community:post_detail", pk=post.id)
