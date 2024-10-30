from django.shortcuts import render
import jwt
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .models import User, Chat
from .serializers import UserSerializer,LoginSerializer,UserTokenSerializer, ChatSerializer
from rest_framework import status
from django.conf import settings
import datetime
import google.generativeai as genai
from drf_yasg import openapi

SignupRequestSchema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'username': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Unique username for the user',
            example='Adityauttarwar'  # Example value for the username
        ),
        'password': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Password for the user account',
            example='AdityaU29'  # Example value for the password
        )
    },
    required=['username', 'password']
)

genai.configure(api_key= 'AIzaSyCsbomJIP27hrr6j2ppNcKPhDQ9gcozJFI')
# Create your views here.
class SignupView(APIView):
    @swagger_auto_schema(
        request_body=SignupRequestSchema,
        responses={
            201: openapi.Response(description="User created successfully"),
            400: openapi.Response(description="Invalid credentials or errors")
        }
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = generate_jwt_token(user)
            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Login view for user authentication
class LoginView(APIView):
    @swagger_auto_schema(
        request_body=SignupRequestSchema,
        responses={
            201: openapi.Response(description="User logged in successfully"),
            400: openapi.Response(description="Invalid credentials or errors")
        }
    )
    def post(self, request):
        # Use serializer to validate request data
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['username']
            password = serializer.validated_data['password']
            try:
                user = User.objects.get(username=email)
                user_serializer = UserSerializer(user)
                if user.check_password(password):
                    token = generate_jwt_token(user)
                    return Response({'token': token, 'user': user_serializer.data}, status=status.HTTP_200_OK)
                return Response({'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'error': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def get_user_from_token(request):
    token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')

    if not token:
        return Response({'error': 'Missing token'}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(id=payload['user_id'])
        serializer = UserSerializer(user)
        return serializer.data
    except jwt.ExpiredSignatureError:
        return Response({'error': 'Signature expired'}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.DecodeError:
        return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Function to generate JWT token for a user
def generate_jwt_token(user):
    payload = {
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token


class ChatView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, description='User message for AI',example='What is the capital of India?')
            },
            required=['message']
        ),
        responses={
            200: openapi.Response(
                description="Successful response",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='The original message'),
                        'response': openapi.Schema(type=openapi.TYPE_STRING, description='AI generated response'),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, description='Response timestamp')
                    }
                )
            ),
            400: openapi.Response(description="Insufficient tokens or errors")
        },
        operation_description="This endpoint allows authenticated users to send a message to the AI chat system. " +
                              "Each message deducts 100 tokens from the user's balance. " +
                              "Ensure you have enough tokens before sending a message." +
                              "\n Please make sure you pass JWT Token in the Authorization header using Authorize button. "
    )
    def post(self, request):
        user = get_user_from_token(request)
        if isinstance(user, Response):
            return user

        message = request.data.get('message')
        myuser = User.objects.get(username=user['username'])

        if myuser.tokens < 100:
            return Response({'message': 'Insufficient tokens'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(message)
            print(response.text)
            myuser.tokens = myuser.tokens - 100
            myuser.save()
            Chat.objects.create(user=myuser,message=message, response=response.text)

            return Response({
                'message': message,
                'response': response.text
                ,'timestamp': datetime.datetime.now()}, status=status.HTTP_200_OK)
            

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'user': user}, status=status.HTTP_200_OK)


class TokenBalanceView(APIView):
    @swagger_auto_schema(
        responses={
            200: UserTokenSerializer,
            400: openapi.Response(description="Authorization issue or errors")
        },
        operation_description="Please make sure you pass JWT Token in the Authorization header using Authorize button. "
    )
    def get(self, request):
        user = get_user_from_token(request)
        if isinstance(user, Response):
            return user
        myuser = User.objects.get(username=user['username'])
        serializer = UserTokenSerializer(myuser)
        return Response({'user': serializer.data}, status=status.HTTP_200_OK)