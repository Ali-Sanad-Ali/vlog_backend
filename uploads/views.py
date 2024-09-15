from rest_framework.views import APIView
from rest_framework.response import Response
from trend.s3_utils import S3
import uuid


class GetPresignedURLAPIView(APIView):

    def get(self, request, *args, **kwargs):
        # Get the file type (avatar or background_pic) from query params
        file_type = request.query_params.get('type', 'avatar')
        file_extension = request.query_params.get('extension')
        ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'mp4', 'mov', 'avi']
        if not file_extension or file_extension.lower() not in ALLOWED_EXTENSIONS:
            return Response({'error': 'Invalid or missing file extension'}, status=400)
        # Generate the appropriate key based on file type and extension
        file_uuid = str(uuid.uuid4())
        if file_type == 'background_pic':
            file_key = f'media/background_pics/{file_uuid}.{file_extension.lower()}'
        elif file_type == 'avatar':
            file_key = f'media/avatars/{file_uuid}.{file_extension.lower()}'
        elif file_type == 'vlog':
            file_key = f'media/vlogs/{file_uuid}.{file_extension.lower()}'
        elif file_type == 'post':
            file_key = f'media/posts/{file_uuid}.{file_extension.lower()}'
        else:
            return Response({'error': 'Invalid file type'}, status=400)    
        url = S3().get_presigned_url(file_key)
        return Response({'url': url, 'file_key': file_key})
