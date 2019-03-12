
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect

from posts.models import Post
from posts.forms import PostForm
from users.models import User
from friends.models import FriendRequest
from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.core.exceptions import ObjectDoesNotExist

from .forms import ProfileChangeForm as changeForm

from django.urls import reverse

from friends.views import follows

import requests
import re
import pytz

import base64



# TODO: use the REST API once it is established
def home(request):
	utc=pytz.UTC

	# TODO: If the user is not authenticated then don't show the home page,
	# but instead show soe other page reporting the error. (Maybe just the login page).

	# Searches for content
	# Needs to search for user name as well
	# Needs a way to show the searched results
	# maybe pagination
	# Need to filter properly
	###################################################################################
	# queryset_list = Post.objects.all()
	# query = request.GET.get("query")
	# if query:
	# 	queryset_list = queryset_list.filter(content__icontains=query)
	# 	print("These are the queries", queryset_list)
	#####################################################################################


	
	# public_posts_list = []
	# private_posts_list = []
	# friends_posts_list = []
	# foaf_posts_list = []
	# server_posts_list = []
	# only_me_posts_list = []
	streamlist = []


	instance = None
	if request.method == "POST":

		form = PostForm(request.POST or None, request.FILES or None)
		if form.is_valid():
			instance = form.save(commit=False)
			instance.user = request.user
			instance.publish = datetime.now()
			instance.save()
			form = PostForm()
		print(form.errors)
		
		user = request.user


		privacy = request.GET.get('privacy', None)

		if privacy is not None:
			streamlist = Post.objects.filter(privacy=privacy)
			print("GET", streamlist)
		else:
			streamlist = Post.objects.filter_user_visible_posts(user=request.user)
		query = request.GET.get("query")
		if query:
			streamlist = streamlist.filter(content__icontains=query)

		print("Stream list len: ", len(streamlist))
		print("Stream list: ", streamlist)


		# print("Privacy:", instance.privacy)
		# if instance.privacy == 0:
		# 	streamlist = Post.objects.filter_by_public()
		# 	print("public length: ", len(streamlist))
		# 	print("Public list: ", streamlist)
		
		# elif instance.privacy == 1:
		# 	streamlist = Post.objects.filter_by_private()
		# 	print("private length: ", len(streamlist))
		# 	print("Private list: ", streamlist)

		# elif instance.privacy == 2:
		# 	streamlist = Post.objects.filter_by_friends()
		# 	print("Friends length: ", len(streamlist))
		# 	print("Friends list: ", streamlist)


		# elif instance.privacy == 3:
		# 	streamlist = Post.objects.filter_by_foaf()
		# 	print("FOAF length: ", len(streamlist))
		# 	print("FOAF list: ", streamlist)
		
		# elif instance.privacy == 4:
		# 	streamlist = Post.objects.filter_by_only_server()
		# 	print("server length: ", len(streamlist))
		# 	print("Server list: ", streamlist)

		# elif instance.privacy == 5:
		# 	streamlist = Post.objects.filter_by_only_me(user=request.user)
		# 	print("only me length: ", len(streamlist))
		# 	print("Private list: ", streamlist)

		# streamlist = Post.objects.filter_user_visible_posts(user=request.user)

		
		

		
		
	

		#TODO: increase rate limit with OAuth?
		#if so, do pagination of API call
		#make call to Github API
		build_request = 'https://api.github.com/users/' + request.user.github + '/events'
		r=requests.get(build_request)
		response = r.json()

		if r.status_code == 200:
			for event in response:
				#parse through output of API call and formulate into readable message
				event_type = ''
				#Parse event type into multiple words
				#eg: PushEvent -> Push event
				#https://stackoverflow.com/questions/2277352/split-a-string-at-uppercase-letters
				#Credit: Mark Byers (https://stackoverflow.com/users/61974/mark-byers)
				for word in re.findall('[A-Z][^A-Z]*', event['type']):
					event_type += word + ' '
				#Parse date into more readbale format
				#https://stackoverflow.com/questions/18795713/parse-and-format-the-date-from-the-github-api-in-python
				#Credit: IQAndreas (https://stackoverflow.com/users/617937/iqandreas)
				date = datetime.strptime(event['created_at'], "%Y-%m-%dT%H:%M:%SZ")
				event_datetime = date.strftime('%A %b %d, %Y at %H:%M GMT')
				#Parse url
				event_repo = 'https://github.com/' + event['repo']['name']
				message = "You had a " + event_type + 'on ' + event_datetime + ' for repo ' + event_repo

				#Flag for determining if a github event is older than all posts
				is_oldest = True
				#sort based on datetime
				for item in streamlist:
					if isinstance(item, Post):
						#Note that the time returned by the github api is timezone naive
						#We must give it local timezone information in order to compare with timestamp
						#of a post
						#https://stackoverflow.com/questions/15307623/cant-compare-naive-and-aware-datetime-now-challenge-datetime-end
						#Credit: Viren Rajput (https://stackoverflow.com/users/997562/viren-rajput)
						if item.timestamp < utc.localize(date):
							is_oldest = False
							streamlist.insert(streamlist.index(item), message)
							break

				if is_oldest:
					streamlist.append(message)


		context = {
			"object_list": streamlist,
			"user": user,
			"form": form,
		}
	else:

		form = PostForm()
		user = request.user


		privacy = request.GET.get('privacy', None)

		if privacy is not None:
			streamlist = Post.objects.filter(privacy=privacy)
			print("GET", streamlist)
		else:
			streamlist = Post.objects.filter_user_visible_posts(user=request.user)
			query = request.GET.get("query")
		if query:
			streamlist = streamlist.filter(content__icontains=query)

		print("Stream list len: ", len(streamlist))
		print("Stream list: ", streamlist)

	




		#TODO: increase rate limit with OAuth?
		#if so, do pagination of API call
		#Validate user github?
		#make call to Github API
		build_request = 'https://api.github.com/users/' + request.user.github + '/events'
		r=requests.get(build_request)
		response = r.json()

		if r.status_code == 200:
			for event in response:
				#parse through output of API call and formulate into readable message
				event_type = ''
				#Parse event type into multiple words
				#eg: PushEvent -> Push event
				#https://stackoverflow.com/questions/2277352/split-a-string-at-uppercase-letters
				#Credit: Mark Byers (https://stackoverflow.com/users/61974/mark-byers)
				for word in re.findall('[A-Z][^A-Z]*', event['type']):
					event_type += word + ' '
				#Parse date into more readbale format
				#https://stackoverflow.com/questions/18795713/parse-and-format-the-date-from-the-github-api-in-python
				#Credit: IQAndreas (https://stackoverflow.com/users/617937/iqandreas)
				date = datetime.strptime(event['created_at'], "%Y-%m-%dT%H:%M:%SZ")
				event_datetime = date.strftime('%A %b %d, %Y at %H:%M GMT')
				#Parse url
				event_repo = 'https://github.com/' + event['repo']['name']
				message = "You had a " + event_type + 'on ' + event_datetime + ' for repo ' + event_repo

				#Flag for determining if a github event is older than all posts
				is_oldest = True
				#sort based on datetime
				for item in streamlist:
					if isinstance(item, Post):
						#Note that the time returned by the github api is timezone naive
						#We must give it local timezone information in order to compare with timestamp
						#of a post
						#https://stackoverflow.com/questions/15307623/cant-compare-naive-and-aware-datetime-now-challenge-datetime-end
						#Credit: Viren Rajput (https://stackoverflow.com/users/997562/viren-rajput)
						if item.timestamp < utc.localize(date):
							is_oldest = False
							streamlist.insert(streamlist.index(item), message)
							break

				if is_oldest:
					streamlist.append(message)

		##Friend Requests##
		#Query to see if any pending friend requests
		friend_requests = FriendRequest.objects.filter(recipient=user)
		

		context = {
			"object_list": streamlist,
			"user": user,
			"form": form,
			"friend_requests": friend_requests,
		}
	if instance and instance.unlisted is True:
		context["unlisted_instance"] = instance

	return render(request, "home.html", context)


def profile(request, pk = None):

	if not request.user.is_authenticated:
		return HttpResponseForbidden()

	# If no pk is provided, just default to the current user's page
	if pk is None:
		pk = request.user.id

	try:
		user = User.objects.get(pk=pk)
	except ObjectDoesNotExist:
		# TODO: Return a custom 404 page
		return HttpResponseNotFound("That user does not exist")

	# Check if we follow the user whose profile we are looking at
	following = False
	if request.user.id is not pk:
		following = follows(request.user.id, pk)

	return render(request, 'profile.html', {'user': user, 'following': following})


def edit_profile(request):
	
	if not request.user.is_authenticated:
		return HttpResponseForbidden()

	#if they submitted new changes create change form
	if request.method == "POST":
		form = changeForm(request.POST,instance=request.user)
	   
		#check for validity of entered data. save to db if valid and redirect
		# back to profile page
		if form.is_valid():
			form.save()
			return HttpResponseRedirect('http://127.0.0.1:8000/home/profile/') #TODO need to fix this so not hardcoded
		
		#TODO else statement when form isn't valid

	#if not POST, then must be GET'ing the form itself. so pass context
	else:
		form = changeForm(instance=request.user,initial={'first_name':request.user.first_name,
														'last_name':request.user.last_name,
														'email':request.user.email,
														'github':request.user.github})
		
		context = {'form':form}
		return render(request,'profileEdit.html',context)

