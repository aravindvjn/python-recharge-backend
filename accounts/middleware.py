from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings

User = get_user_model()

class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip authentication for certain paths
        skip_paths = [
            '/api/auth/signup/',
            '/api/auth/login/email/',
            '/api/auth/otp/generate/',
            '/api/auth/otp/verify/',
            '/admin/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
            
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
            
        token = auth_header.split(' ')[1]
        
        try:
            # Validate token
            UntypedToken(token)
            
            # Decode token to get user info
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            if user_id:
                user = User.objects.get(id=user_id)
                request.user = user
                return None
            else:
                return JsonResponse({'error': 'Invalid token'}, status=401)
                
        except (InvalidToken, TokenError, User.DoesNotExist):
            return JsonResponse({'error': 'Invalid token'}, status=401)
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)