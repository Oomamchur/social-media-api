from user.models import Post, User

from celery import shared_task


@shared_task
def create_post(user_id: int) -> int:
    user = User.objects.get(id=user_id)
    text = f"New post from user: {user.username}"
    hashtag = "celery"
    Post.objects.create(user=user, text=text, hashtag=hashtag)
    return Post.objects.count()
