from django.urls import path

from .views import (
    CategoryPostsView,
    CommunityHomeView,
    ForumPostCreateView,
    ForumPostDetailView,
    ForumPostReportView,
    ForumReplyCreateView,
)

app_name = "community"

urlpatterns = [
    path("", CommunityHomeView.as_view(), name="home"),
    path("post/new/", ForumPostCreateView.as_view(), name="post_create"),
    path("post/<int:pk>/", ForumPostDetailView.as_view(), name="post_detail"),
    path("post/<int:post_id>/reply/", ForumReplyCreateView.as_view(), name="reply_create"),
    path("post/<int:post_id>/report/", ForumPostReportView.as_view(), name="report"),
    path("category/<slug:slug>/", CategoryPostsView.as_view(), name="category_posts"),
]
