import uuid
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from profiles.pagination import CustomPageNumberPagination
from users.models import CustomUser, BlockedUser
from .models import Post, Comment, Like, HiddenPost
from .serializers import PostSerializer, PostCommentSerializer, LikerSerializer, HiddenPostSerializer


class PostListView(generics.ListAPIView):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        '''
        Restrict the user from viewing posts if blocked. This means the posts will not be available for liking or commenting, effectively preventing a blocked user from liking or commenting
        '''
        queryset = super().get_queryset().select_related('user').prefetch_related('post_likes', 'post_comments')
        user = self.request.user
        if user.is_authenticated:
            blocked_users = BlockedUser.objects.filter(blocker=user).values_list('blocked', flat=True)
            blocked_by_users = BlockedUser.objects.filter(blocked=user).values_list('blocker', flat=True)
            users_to_exclude = list(set(blocked_users).union(set(blocked_by_users)))
            # Retrieve IDs of posts hidden by any user
            hidden_post_ids = HiddenPost.objects.filter(user=user).values_list('post_id', flat=True)
            queryset = Post.objects.exclude(user__in=users_to_exclude).exclude(id__in=hidden_post_ids)

        return queryset.order_by('-created_at')


class PostDetailView(generics.RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]




class PostCreateView(generics.CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        #  file_key is obtained from the client after upload
        file_key = self.request.data.get('file_key')
        serializer.save(user=self.request.user, image_key=file_key)
        # serializer.save(user=self.request.user)


class PostUpdateView(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]


class PostDeleteView(generics.DestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]


class CommentListView(generics.ListAPIView):
    serializer_class = PostCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            return Comment.objects.none()
        return Comment.objects.filter(post=post)


class CommentDetailView(generics.RetrieveAPIView):
    queryset = Comment.objects.all()
    serializer_class = PostCommentSerializer
    permission_classes = [IsAuthenticated]


class CommentCreateView(generics.CreateAPIView):
    serializer_class = PostCommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        serializer.save(post_id=post_id, user=self.request.user)


class CommentUpdateView(generics.UpdateAPIView):
    queryset = Comment.objects.all()
    serializer_class = PostCommentSerializer
    permission_classes = [IsAuthenticated]


class CommentDeleteView(generics.DestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = PostCommentSerializer
    permission_classes = [IsAuthenticated]


class ToggleLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_id')

        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            like = Like.objects.get(post=post, user=request.user)
            like.delete()
            return Response({'status': 'Disliked'}, status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            Like.objects.create(post=post, user=request.user)
            return Response({'status': 'Liked'}, status=status.HTTP_200_OK)


class UserPostsListView(generics.ListAPIView):
    """
    List all posts created by a specific user.
    """
    serializer_class = PostSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Post.objects.filter(user__id=user_id).order_by('-created_at')


class PostLikersList(generics.ListAPIView):
    """
        List all post Likers.
    """
    serializer_class = LikerSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        request_user = self.request.user
        if not post_id:
            return CustomUser.objects.none()
        # Get list of blocked user IDs
        blocked_users = BlockedUser.objects.filter(blocker=request_user).values_list('blocked', flat=True)
        blocked_by_users = BlockedUser.objects.filter(blocked=request_user).values_list('blocker', flat=True)
        users_to_exclude = list(set(blocked_users).union(set(blocked_by_users)))
        likers_ids = Like.objects.filter(post_id=post_id).values_list('user_id', flat=True).order_by('-created_at')
        return CustomUser.objects.filter(id__in=likers_ids).exclude(id__in=users_to_exclude).select_related('profile')


class HideorUnhidePostView(generics.GenericAPIView):
    """
     allows authenticated users to hide or unhide  posts.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = HiddenPostSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        post_id = self.kwargs.get('post_id')
        post = Post.objects.get(id=post_id)
        # Create the hidden post relationship
        HiddenPost.objects.get_or_create(user=user, post=post)
        return Response({"success": True}, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        post_id = self.kwargs.get('post_id')
        post = Post.objects.get(id=post_id)

        HiddenPost.objects.filter(user=user, post=post).delete()
        return Response({"success": True}, status=status.HTTP_204_NO_CONTENT)
