
from django.urls import reverse
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .tasks import process_video_validation
from profiles.pagination import CustomPageNumberPagination
from users.models import BlockedUser, CustomUser
from .models import Vlog, Comment, Like, VlogProcessingTask
from .serializers import VlogSerializer, VlogCreateSerializer, CommentSerializer, VlogLikersSerializer


class VlogListView(generics.ListAPIView):
    queryset = Vlog.objects.all().order_by('-created_at')
    serializer_class = VlogSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    # @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    # def get(self, request, *args, **kwargs):
    #     return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Optionally restricts the returned videos to those not blocked by the author.
        """
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            blocked_users = BlockedUser.objects.filter(blocker=user).values_list('blocked', flat=True)
            blocked_by_users = BlockedUser.objects.filter(blocked=user).values_list('blocker', flat=True)
            users_to_exclude = list(set(blocked_users).union(set(blocked_by_users)))
            queryset = Vlog.objects.exclude(user__in=users_to_exclude).exclude(processing_status='failed')
        return queryset.order_by('-created_at')


class VlogDetailView(generics.RetrieveAPIView):
    queryset = Vlog.objects.all()
    serializer_class = VlogSerializer
    permission_classes = [IsAuthenticated]


class VlogUpdateView(generics.UpdateAPIView):
    queryset = Vlog.objects.all()
    serializer_class = VlogSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        vlog_id = self.kwargs.get('pk')
        new_vlog_key = request.data.get('vlog_key')

        if not vlog_id or not new_vlog_key:
            return Response({'error': 'vlog_id and vlog_key are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            vlog = Vlog.objects.get(id=vlog_id)
        except Vlog.DoesNotExist:
            return Response({'error': 'Vlog not found'}, status=status.HTTP_404_NOT_FOUND)
        # Update vlog instance
        vlog.vlog_key = new_vlog_key
        vlog.processing_status = 'pending'
        vlog.save()

        process_video_validation.delay(vlog.id)
        return Response({'message': 'Video update initiated and is being processed',
                        'status_url': reverse('video-processing-status', args=[vlog.id])},
                        status=status.HTTP_200_OK)


class VlogDeleteView(generics.DestroyAPIView):
    queryset = Vlog.objects.all()
    serializer_class = VlogSerializer
    permission_classes = [IsAuthenticated]


class VlogCreateView(generics.CreateAPIView):
    queryset = Vlog.objects.all()
    serializer_class = VlogCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video = serializer.save(user=self.request.user, processing_status='pending')
        # Create the VideoProcessingTask to track the status
        VlogProcessingTask.objects.create(vlog=video)
        # Enqueue asynchronous tasks for processing
        process_video_validation.delay(video.id)
        # Return a response with the status endpoint
        return Response({
            'message': 'Video upload initiated and is being processed',
            'status_url': reverse('video-processing-status', args=[video.id]),
        }, status=status.HTTP_201_CREATED)


class VlogProcessingStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            vlog = Vlog.objects.get(id=pk)
            task = vlog.processing_task
            return Response({
                'status': task.status,
                'error_message': task.error_message
            })
        except Vlog.DoesNotExist:
            return Response({'error': 'Vlog not found'}, status=404)
        except VlogProcessingTask.DoesNotExist:
            return Response({'status': 'pending'})  # Default to 'pending' if task does not exist yet


class CommentListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        vlog_id = self.kwargs.get('vlog_id')
        try:
            vlog = Vlog.objects.get(pk=vlog_id)
        except Vlog.DoesNotExist:
            return Comment.objects.none()
        return Comment.objects.filter(vlog=vlog)


class CommentDetailView(generics.RetrieveAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]


class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        vlog_id = self.kwargs.get('vlog_id')
        serializer.save(vlog_id=vlog_id, user=self.request.user)


class CommentUpdateView(generics.UpdateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]


class CommentDeleteView(generics.DestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]


class ToggleLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        vlog_id = self.kwargs.get('vlog_id')

        try:
            vlog = Vlog.objects.get(pk=vlog_id)
        except Vlog.DoesNotExist:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            like = Like.objects.get(vlog=vlog, user=request.user)
            like.delete()
            return Response({'status': 'Disliked'}, status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            Like.objects.create(vlog=vlog, user=request.user)
            return Response({'status': 'Liked'}, status=status.HTTP_200_OK)


class VlogLikersList(generics.ListAPIView):
    """
        List all Vlog Likers.
    """
    serializer_class = VlogLikersSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        vlog_id = self.kwargs.get('pk')
        request_user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return Vlog.objects.none()
        # Get list of blocked user IDs
        blocked_users = BlockedUser.objects.filter(blocker=request_user).values_list('blocked', flat=True)
        blocked_by_users = BlockedUser.objects.filter(blocked=request_user).values_list('blocker', flat=True)
        users_to_exclude = list(set(blocked_users).union(set(blocked_by_users)))
        likers_ids = Like.objects.filter(vlog_id=vlog_id).values_list('user_id', flat=True).order_by('-created_at')
        return CustomUser.objects.filter(id__in=likers_ids).exclude(id__in=users_to_exclude)
