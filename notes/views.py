from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.http import Http404

from .models import User, Note
from notes.serializers import NoteSerializer


class RegisterView(APIView):
    def post(self, request):
        data = request.data
        required_fields = ['username', 'email', 'password']
        if not all(field in data for field in required_fields):
            return Response(
                {'error': 'Please provide username, email, and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=data['email']).exists():
            return Response(
                {'error': 'This email is already registered'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(email=email, password=password)

        if user is None:
            return Response(
                {'error': 'Wrong email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Logged in successfully',
        }, status=status.HTTP_200_OK)


class NoteListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notes = Note.objects.filter(user=request.user)
        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = NoteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NoteDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_note(self, id):
        try:
            return Note.objects.get(id=id)
        except Note.DoesNotExist:
            raise Http404

    def get(self, request, id):
        note = self.get_note(id)
        serializer = NoteSerializer(note)
        return Response(serializer.data)

    def put(self, request, id):
        note = self.get_note(id)
        serializer = NoteSerializer(note, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        note = self.get_note(id)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)