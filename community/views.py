from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from users.engagement import create_notification, ensure_initial_content, evaluate_user_badges

from .forms import ForumPostForm, ForumReplyForm
from .models import ForumCategory, ForumPost


DEFAULT_CATEGORIES = [
    ("Versets", "versets", "Reflexions a partir des versets du Coran", "fa-solid fa-book-quran", False, 1),
    ("Duas", "duas", "Invocations quotidiennes et demandes de soutien", "fa-solid fa-hands-praying", False, 2),
    ("Hadiths", "hadiths", "Rappels prophetiques et explications", "fa-solid fa-scroll", False, 3),
    ("Questions", "questions", "Questions, entraide et conseils", "fa-solid fa-circle-question", False, 4),
]


def ensure_categories():
    for name, slug, description, icon, is_premium, order in DEFAULT_CATEGORIES:
        ForumCategory.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "description": description,
                "icon": icon,
                "is_premium": is_premium,
                "order": order,
            },
        )


class CommunityHomeView(ListView):
    model = ForumPost
    template_name = "community/feed.html"
    context_object_name = "posts"

    def get_queryset(self):
        ensure_initial_content()
        ensure_categories()
        filter_key = self.request.GET.get("filter", "recent")
        queryset = ForumPost.objects.select_related("author", "category").prefetch_related("replies", "liked_by")
        if filter_key == "trending":
            queryset = queryset.order_by("-likes_count", "-views_count", "-created_at")
        elif filter_key == "verses":
            queryset = queryset.filter(post_type="verse")
        elif filter_key == "duas":
            queryset = queryset.filter(post_type="dua")
        elif filter_key == "questions":
            queryset = queryset.filter(post_type="question")
        else:
            queryset = queryset.order_by("-created_at")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ForumCategory.objects.all()
        context["selected_filter"] = self.request.GET.get("filter", "recent")
        context["top_posts"] = (
            ForumPost.objects.annotate(reply_total=Count("replies")).order_by("-likes_count", "-reply_total")[:5]
        )
        context["liked_ids"] = (
            set(self.request.user.liked_forum_posts.values_list("id", flat=True))
            if self.request.user.is_authenticated
            else set()
        )
        return context


class CategoryPostsView(ListView):
    model = ForumPost
    template_name = "community/category_posts.html"
    context_object_name = "posts"

    def get_queryset(self):
        ensure_categories()
        self.category = get_object_or_404(ForumCategory, slug=self.kwargs["slug"])
        return ForumPost.objects.filter(category=self.category).select_related("author", "category")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


class ForumPostDetailView(DetailView):
    model = ForumPost
    template_name = "community/post_detail.html"
    context_object_name = "post"

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        post.views_count += 1
        post.save(update_fields=["views_count"])
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reply_form"] = ForumReplyForm()
        context["liked"] = (
            self.request.user.is_authenticated and self.object.liked_by.filter(id=self.request.user.id).exists()
        )
        return context


class ForumPostCreateView(LoginRequiredMixin, View):
    def post(self, request):
        ensure_categories()
        form = ForumPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            if not post.title.strip():
                post.title = post.get_post_type_display()
            post.save()
            evaluate_user_badges(request.user)
            messages.success(request, "Publication ajoutee au feed Ummah.")
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
            if post.author != request.user:
                create_notification(
                    post.author,
                    "community",
                    f"Nouvelle reponse sur {post.title}",
                    f"{request.user.username} a repondu a votre publication.",
                    f"/community/post/{post.id}/",
                )
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


class ForumPostLikeView(LoginRequiredMixin, View):
    def post(self, request, post_id):
        post = get_object_or_404(ForumPost, id=post_id)
        if post.liked_by.filter(id=request.user.id).exists():
            post.liked_by.remove(request.user)
            post.likes_count = max(0, post.likes_count - 1)
            messages.info(request, "Reaction retiree.")
        else:
            post.liked_by.add(request.user)
            post.likes_count += 1
            if post.author != request.user:
                create_notification(
                    post.author,
                    "community",
                    "Un Masha'Allah sur votre publication",
                    f"{request.user.username} a aime votre post.",
                    f"/community/post/{post.id}/",
                )
            messages.success(request, "Masha'Allah envoye.")
        post.save(update_fields=["likes_count"])
        return redirect(request.META.get("HTTP_REFERER") or "community:home")
