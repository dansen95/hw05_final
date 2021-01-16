from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, Comment, Follow

User = get_user_model()


def index(request):
    post_list = Post.objects.select_related('group')
    paginator = Paginator(post_list, 10) 
    page_number = request.GET.get('page') 
    page = paginator.get_page(page_number) 
    return render(
         request,
         'posts/index.html',
         {'page': page,
          'paginator': paginator}
    ) 


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.all()
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number) 
    return render(request, 'group.html', {'group': group,
                                         'page': page, 'paginator': paginator})


def profile(request, username): 
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    post_count = post_list.count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    if request.user.is_authenticated:
        following = request.user.follower.filter(author=author).exists()
    else:
        following = False
    context = {
        'page': page,
        'author': author,
        'paginator': paginator,
        'post_count': post_count,
        'following': following
    }
    return render(request, 'users/profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    count = post.author.posts.count()
    comments = Comment.objects.filter(post_id=post_id)
    form = CommentForm(request.POST or None)
    context = {
        'post': post, 
        'author': post.author, 
        'count': count,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post.html', context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = PostForm(request.POST or None,
        files=request.FILES or None, instance=post)
    if post.author != request.user:
        return redirect('post', username=post.author, post_id=post_id)
    if request.method == 'GET' or not form.is_valid():
        return render(
            request, 
            'posts/new_post.html', 
            {
                'form': form,
                'post': post,
                'is_edit': True,
            }
        )
    post.save()
    return redirect('post', username=post.author, post_id=post_id)


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            return redirect('index')

        return render(request, 'posts/new_post.html', {'form': form})

    form = PostForm()
    return render(request, 'posts/new_post.html', {'form': form})


def page_not_found(request, exception):
    return render(
        request, 
        "misc/404.html", 
        {"path": request.path}, 
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, post_id, username):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect("post", username, post_id)
    return render(
        request, "comments.html", {"form": form, "post": post}
    )


@login_required
def follow_index(request):
    post_list = Post.objects.select_related('group').filter(
        author__following__user=request.user
    )
    paginator = Paginator(post_list, 10) 
    page_number = request.GET.get('page') 
    page = paginator.get_page(page_number) 

    return render(
        request, 
        "follow.html", 
        {'page': page,
        'paginator': paginator}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user and not Follow.objects.filter(
        user=request.user, author=author).exists():
        
        Follow.objects.get_or_create(user=request.user, author=author)
        return redirect('profile', username=username)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username=username)
