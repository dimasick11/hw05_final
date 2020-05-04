from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


@cache_page(20)
def index(request):
    post_list = Post.objects.order_by('-pub_date').all()

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'index.html', {'page': page, 'paginator': paginator, })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).order_by('-pub_date').all()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'group.html', {'group': group, 'page': page, 'paginator': paginator})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=user.id).order_by('-pub_date')
    count_post = post_list.count()

    follow_count = Follow.objects.filter(user=user.id).count()
    following = Follow.objects.filter(author=user.id).count()

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'profile.html', {'page': page, 'paginator': paginator,
                                            'profile_user': user, 'count_post': count_post, 'following': following,
                                            'follow_count': follow_count})


def post_view(request, username, post_id):
    user = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id)
    count_post = Post.objects.filter(author=user.id).order_by('-pub_date').count()

    follow_count = Follow.objects.filter(user=user.id).count()
    following = Follow.objects.filter(author=user.id).count()

    comments = Comment.objects.filter(post_id=post_id).order_by('-created')
    comment_form = CommentForm()

    return render(request, 'post.html',
                  {'profile_user': user, 'post': post, 'count_post': count_post, 'form': comment_form,
                   'items': comments, 'following': following, 'follow_count': follow_count})


def page_not_found(request, exception):
    return render(request, 'misk/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'misk/500.html', status=500)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = get_object_or_404(User, username=username)

    if not request.user == user:
        return redirect('post', username, post_id)

    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('post', username=request.user.username, post_id=post_id)

    return render(request, 'post_new.html', {'form': form, 'post': post})


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None, request.FILES or None)

        if not form.is_valid():
            return render(request, 'post_new.html', {'form': form})

        form.instance.author = request.user
        form.save()

        return redirect('index')

    form = PostForm()
    return render(request, 'post_new.html', {'form': form})


@login_required
def add_comment(request, username, post_id):
    if request.method == 'POST':
        form = CommentForm(request.POST or None)

        if not form.is_valid():
            return redirect('post', username, post_id)

        form.instance.author = request.user
        form.instance.post_id = post_id
        form.save()

    return redirect('post', username, post_id)


@login_required
def follow_index(request):
    follow_authors = Follow.objects.filter(user=request.user).values('author')
    post_list = Post.objects.filter(author__in=follow_authors).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, "follow.html", {'page': page, 'paginator': paginator, })


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        Follow.objects.get_or_create(user=request.user, author=user)

    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        follow = Follow.objects.filter(user=request.user, author=user)
        follow.delete()

    return redirect('profile', username)
