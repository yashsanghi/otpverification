from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response

from .serializer import CreateUserSerializer
from .models import User, PhoneOTP
from django.shortcuts import get_object_or_404
import random

class ValidatePhoneSendOTP(APIView):
	
	def post(self, request, *args, **kwargs):
		phone_number = request.data.get('phone')
		if phone_number:
			phone = str(phone_number)
			user = User.objects.filter(phone__iexact = phone)
			if user.exists():
				return Response({
					'status': False,
					'details':'phone number already exists'
					})
			else:
				key = send_otp(phone)
				if key:
					old = PhoneOTP.objects.filter(phone__iexact = phone)
					if old.exists():
						old = old.first()
						count = old.count
						if count>10:
							return Response({
								'status': False,
								'details':'cant send OTP now. limit exceeded. pls call customer support'
								})	
						old.count = count+1
						old.save()
						print("count increase", count)
						return Response({
						'status' : True,
						'details' : 'OTP sent successfully'
						})

					else:
						
						PhoneOTP.objects.create(
								phone = phone,
								otp = key,

							)
					return Response({
						'status' : True,
						'details' : 'OTP sent successfully'
						})
				else:
					return Response({
						'status': False,
						'details':'cant send OTP now'
						})


		else:
			return Response({
				'status': False,
				'detail':'Phone number is not in database'
				})

def send_otp(phone):
	if phone:
		key= random.randint(999,9999)
		print(key)
		return key
	else:
		return False


class ValidateOTP(APIView):
	'''if u have received otp, post a request with phone and that otp and then u will be redirected to the password'''

	def post(self, request, *args, **kwargs):
		phone = request.data.get('phone', False)
		otp_sent = request.data.get('otp', False)

		if phone and otp_sent:
			old = PhoneOTP.objects.filter(phone__iexact = phone)
			if old.exists():
				old = old.first()
				otp = old.otp
				if str(otp_sent) == str(otp):
					old.validated = True
					old.save()
					return Response({
						'status': True,
						'details': 'OTP matched. please proceed for registration'
						})


				else:
					return Response({
						'status': False,
						'details':'OTP incorrect'
						})
			else:
				return Response({
					'status': False,
					'details': 'First proceed via sending otp request'
					})

		else:
			return Response({
				'status': False,
				'details': 'please provide both phone and otp for validation'
				})


class Register(APIView):
	def post(self, request, *args, **kwargs):
		phone = request.data.get('phone', False)
		password = request.data.get('password', False)

		if phone and password:
			old = PhoneOTP.objects.filter(phone__iexact = phone)
			if old.exists():
				old = old.first()
				validated = old.validated

				if validated:
					temp_data = {
						'phone': phone,
						'password': password
					}
					serializer = CreateUserSerializer(data = temp_data)
					serializer.is_valid(raise_exception = True)
					user = serializer.save()
					old.delete()

					return Response({
						'status': True,
						'details': 'Account created'
						})
				else:
					return Response({
						'status': False,
						'details': "OTP isnt verified"
						})
			else:
				return Response({
					'status': False,
					'details': 'Please verify phone first'
					})
		else:
			return Response({
				'status': False,
				'details': 'Both phone and password are not set'
				})
