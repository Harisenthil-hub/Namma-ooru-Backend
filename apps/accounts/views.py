from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework import status

# Create your views here.

class AdminLoginAPIView(APIView):
    permission_classes=[AllowAny]

    def post(self,request):
        username=request.data.get("username")
        password=request.data.get("password")
        user = authenticate(username=username,password=password)

        if not user or not user.is_staff:
            return Response({"error": "Invalid Credentials"},status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        response = Response({ 'message': 'Login Successfull' }, status=status.HTTP_200_OK)

        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,
            secure=False, # Should be True in Production
            samesite='Lax'
        )

        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=False, # Should be True in Production
            samesite='Lax'
        )

        return response


class AdminLogoutAPIView(APIView):
    def post(self,request):
        response = Response({ 'message': 'Logout Successfull' }, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response