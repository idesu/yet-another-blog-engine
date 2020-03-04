from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User

#from django.views.decorators.cache import cache_page


# Create your views here.


def index(request):
    post_list = (
        Post.objects.select_related('author')
        .select_related('group')
        .order_by('-pub_date')
        .annotate(comment_count=Count('post_comments'))
    )
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "index.html", {'page': page, 'paginator': paginator})


@login_required
def follow_index(request):
    post_list = (
        Post.objects.select_related('author')
        # выбрать посты автора__подписанногона__request.user
        .filter(author__following__user=request.user)
        .order_by("-pub_date")
        .annotate(comment_count=Count('post_comments'))
    )

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_list = (
        Post.objects.select_related('author', 'group')
        .filter(group=group)
        .order_by('-pub_date')
        .annotate(comment_count=Count('post_comments'))
    )
    paginator = Paginator(group_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group, 'page': page, 'paginator': paginator})


@login_required
def new_post(request):
    if request.method == 'POST':
        author = Post(author=request.user)
        form = PostForm(
            request.POST, files=request.FILES or None, instance=author)
        if form.is_valid():
            form.save()
            return redirect('index')
        return render(request, 'new.html', {'form': form, })

    form = PostForm()
    return render(request, 'new.html', {'form': form, })


def profile(request, username):
    user = get_object_or_404(User, username=username)
    following = (
        Follow.objects.filter(user=request.user, author=user).exists()
        if not request.user.is_anonymous
        else False
    )
    post_list = (
        Post.objects.select_related('author')
        .filter(author=user)
        .order_by('-pub_date')
        .annotate(comment_count=Count('post_comments'))
    )

    user_followers = Follow.objects.filter(author=user).count
    user_follow = Follow.objects.filter(user=user).count
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "profile.html",
        {
            'page': page,
            'profile': user,
            'paginator': paginator,
            'following': following,
            "user_followers": user_followers,
            "user_follow": user_follow
        }
    )


def post_view(request, username, post_id):
    user = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author=user.id)
    user_followers = Follow.objects.filter(author=user).count
    user_follow = Follow.objects.filter(user=user).count
    posts_count = Post.objects.filter(
        author=user).count()
    comments = Comment.objects.select_related(
        'author').filter(post=post).order_by("-created")
    form = CommentForm(request.POST or None)
    return render(
        request,
        "post.html",
        {
            'post': post,
            'items': comments,
            'form': form,
            'posts_count': posts_count,
            'author': user,
            "user_followers": user_followers,
            "user_follow": user_follow}
    )


def post_delete(request, username, post_id):
    if request.user.username == username:
        user = get_object_or_404(User, username=username)
        post = Post.objects.filter(author=user).filter(id=post_id).delete()
        cache.clear()
        return redirect('profile', username=username)
    redirect('profile', username=username)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = get_object_or_404(User, username=username)
    if request.user != user:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('post', username=username, post_id=post_id)

    return render(request, 'edit.html', {'form': form, 'post': post})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = get_object_or_404(User, username=username)
    comment = Comment(author=user, post=post)
    form = CommentForm(request.POST, instance=comment)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    exist = Follow.objects.filter(user=user, author=author).exists()
    if user != author and not exist:
        Follow.objects.create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    obj = Follow.objects.filter(user=user, author=author)
    if obj:
        obj.delete()
    return redirect('profile', username=username)


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)
