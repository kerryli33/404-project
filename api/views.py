from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from rest_framework import pagination, generics, views, status, mixins
from rest_framework.response import Response
from rest_framework.views import APIView

import socket
import requests
import uuid

from users.models import User, Node, NodeSetting
from posts.models import Post
from comments.models import Comment
from friends.models import Follow, FriendRequest

from friends.views import follows

from .serializers import UserSerializer, PostSerializer, CommentSerializer, UserFriendSerializer
from .paginators import PostPagination, CommentPagination

# TODO: For privacy issues, send 403?

# TODO:
# As a server admin, I want to be able to add nodes to share with
# As a server admin, I want to be able to remove nodes and stop sharing with them.
# As a server admin, I can limit nodes connecting to me via authentication.
# As a server admin, node to node connections can be authenticated with HTTP Basic Auth
# As a server admin, I can disable the node to node interfaces for connections that are not authenticated!

# CAN POST COMMENTS TO OTHER SERVERS coool
# TODO: FOAF
# TODO:

def authorized(request):

    host = request.scheme + "://" + request.META['HTTP_HOST']

    # TODO: Authentication
    nodes = Node.objects.all()
    for node in nodes:
        if host == node.host:
            return True

    node_settings = NodeSetting.objects.all()[0]
    if host == node_settings.host:
        return True
    # If the request didn't come from one of our connected nodes,
    # then check if the request came from an authenticated user
    if not request.user.is_authenticated:
        return False

    return True


# Remove all image posts from a set of posts
def filter_out_image_posts(queryset):
    new_queryset = Post.objects.none()
    for post in queryset:
        if not post.is_image:
            new_queryset |= Post.objects.filter(id=post.id)
    return new_queryset

def get_requestor_id(request):

    # Get the requestors ID, but make sure it is a valid UUID
    requestor_id = ""
    try:
        if request.GET.get('user', None) is not None:
            return uuid.UUID(request.GET['user'])
        # TODO: The request needs to have come from our server for the below
        # to be guaranteed to work
        else:
            return request.user.id
    except:
        return None

class UserAPIView(generics.GenericAPIView):

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):

        if not authorized(request):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if 'author_id' in kwargs.keys():
            author_id = self.kwargs['author_id']
            try:
                queryset = User.objects.get(id=author_id, is_active=True)
            except:
                return Response(status=status.HTTP_404_NOT_FOUND)

        else:
            queryset = User.objects.filter(is_active=True)

        followers = User.objects.filter(follower__user2=author_id, is_active=True)
        following = User.objects.filter(followee__user1=author_id, is_active=True)
        friends = following & followers

        serializer = UserSerializer(queryset, many=False, context={'friends':friends})
        return Response(serializer.data)


# TODO: As a server admin, I want to share or not share posts with users on other servers.
# TODO: As a server admin, I want to share or not share images with users on other servers.
class PostAPIView(generics.GenericAPIView):

    queryset = Post.objects.all()
    serializer_class = PostSerializer
    pagination_class = PostPagination

    def get(self, request, *args, **kwargs):

        if not authorized(request):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Check if we have enabled sharing posts with other servers
        node_settings = None
        host = request.scheme + "://" + request.META['HTTP_HOST']

        try:
            node_settings = NodeSetting.objects.all()[0]
            if node_settings.share_posts is False:
                if not host == node_settings.host:
                    return Response(status=status.HTTP_401_UNAUTHORIZED)
        except:
            pass

        server_only = False
        if host == node_settings.host:
            server_only = True

        data = ""
        queryset = ""
        path = request.path
        requestor_id = get_requestor_id(request)

        if requestor_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if 'author_id' in self.kwargs.keys():
            author_id = self.kwargs['author_id']
            try:
                author = User.objects.get(id=author_id)
            except:
                return Response(status=status.HTTP_404_NOT_FOUND)

            queryset = Post.objects.none()
            if requestor_id == author_id:
                queryset = Post.objects.filter(user=requestor_id, unlisted=False)
            else:
                queryset = Post.objects.filter_user_visible_posts_by_user_id(user_id=requestor_id, server_only=server_only).filter(user=author_id)
                queryset = queryset | Post.objects.filter(user=author_id, privacy=Post.PUBLIC)

        elif 'post_id' in kwargs.keys():
            post_id = self.kwargs['post_id']
            queryset = Post.objects.filter_user_visible_posts_by_user_id(user_id=requestor_id, server_only=server_only).filter(id=post_id)

        elif path == "/service/author/posts":
            # Get all posts visible to the requesting user
            queryset = Post.objects.filter_user_visible_posts_by_user_id(user_id=requestor_id, server_only=server_only)

        else:
            queryset = Post.objects.filter(privacy=Post.PUBLIC)

        if node_settings is not None and node_settings.share_imgs is False:
            if not host == node_settings.host:
                queryset = filter_out_image_posts(queryset)

        serializer = PostSerializer(queryset, many=True)
        data = serializer.data

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(data)

    def post(self, request, *args, **kwargs):

        if not authorized(request):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # TODO: We need to incorporate UUIDs for posts first
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, *args, **kwargs):

        if not authorized(request):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # TODO: We need to incorporate UUIDs for posts first
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class CommentAPIView(generics.GenericAPIView):

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    pagination_class = CommentPagination

    def get(self, request, *args, **kwargs):

        if not authorized(request):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        requestor_id = get_requestor_id(request)
        if requestor_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        server_only = False
        node_settings = None
        host = request.scheme + "://" + request.META['HTTP_HOST']

        try:
            node_settings = NodeSetting.objects.all()[0]
            if host == node_settings.host:
                server_only = True
        except:
            pass

        if 'post_id' in self.kwargs.keys():
            post_id = self.kwargs['post_id']
            try:
                queryset = Post.objects.filter_user_visible_posts_by_user_id(user_id=requestor_id, server_only=server_only).filter(id=post_id)[0].comments
            except:
                Response(status=status.HTTP_404_NOT_FOUND)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CommentSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):

        response_failed = {
           "query": "addComment",
           "success": False,
           "message": "Comment not allowed"
        }

        response_ok = {
            "query": "addComment",
            "success": True,
            "message": "Comment Added"
        }

        if not authorized(request):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        requestor_id = get_requestor_id(request)
        if requestor_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        server_only = False
        node_settings = None
        host = request.scheme + "://" + request.META['HTTP_HOST']

        try:
            node_settings = NodeSetting.objects.all()[0]
            if host == node_settings.host:
                server_only = True
        except:
            pass

        # Retrieves JSON data
        data = request.data
        try:
            #post_id = data['post'].split("/")[-1]
            post_id = kwargs['post_id']
            content = data['comment']['comment']
            content_type = "text/plain"
            author_id = data['comment']['author']['id'].split("/")[-1]
        except:
            # If the JSON was not what we wanted, send a 400
            Response(status=status.HTTP_400_BAD_REQUEST)

        # Check that the requesting user has visibility of that post
        post = Post.objects.filter_user_visible_posts_by_user_id(user_id=requestor_id, server_only=server_only).filter(id=post_id)
        if post is None:

            return Response(response_failed, status=status.HTTP_403_FORBIDDEN)

        # TODO: Create the actual post
        failed = False
        try:
            # ERROR: ["'<built-in function id>' is not a valid UUID."]
            post=post[0]
            instance = get_object_or_404(Post, id=post.id)
            comment = Comment(parent=None, user=author_id, content=content, object_id=post.id, content_type=post.get_content_type)
            comment.save()
        except Exception as e:
            print(e)
            failed = True

        return Response(response_ok, status=status.HTTP_200_OK)
# {
# 	"comment":{
# 	    "author":{
#                    "id":"http://127.0.0.1:5454/author/1d698d25ff008f7538453c120f581471"
# 	   },
# 	   "comment":"Sick Olde English"
# 	}
# }

class FriendAPIView(generics.GenericAPIView):

    queryset = Follow.objects.all()
    serializer_class = UserFriendSerializer

    def get(self, request, *args, **kwargs):

        if not authorized(request):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if 'author_id' in self.kwargs.keys():
            author_id = self.kwargs['author_id']

            friends = ""
            try:
                followers = User.objects.filter(follower__user2=author_id, is_active=True)
                following = User.objects.filter(followee__user1=author_id, is_active=True)
                friends = following & followers
            except:
                return Response(status=status.HTTP_404_NOT_FOUND)

            friend_list = list()
            for friend in friends:
                friend_list.append(str(friend.id))

            return Response({"query": "friends", "authors": friend_list})

        if 'author_id1' in self.kwargs.keys() and 'author_id2' in self.kwargs.keys():

            author_id1 = self.kwargs['author_id1']
            author_id2 = self.kwargs['author_id2']

            friend_list = ""
            try:
                followers = User.objects.filter(follower__user2=author_id1, is_active=True)
                following = User.objects.filter(followee__user1=author_id1, is_active=True)
                friend_list = following & followers
            except:
                return Response(status=status.HTTP_404_NOT_FOUND)

            friends = False
            for friend in friend_list:
                if friend.id == author_id2:
                    friends = True
                    break

            # Whether there is friendship or not, we need some author data
            author1 = User
            author2 = User
            try:
                author1 = User.objects.get(id=author_id1)
                author2 = User.objects.get(id=author_id2)
            except:
                return Response(status=status.HTTP_404_NOT_FOUND)

            response = {
                "query":"friends",
                "authors":[
                    str(author1.host) + str(author1.id),
                    str(author2.host) + str(author2.id)
                ],
                "friends": friends
            }

            return Response(response)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):

        if not authorized(request):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Retrieves JSON data
        data = request.data
        try:
            author = data['author']
            authors = data['authors']
        except:
            # If the JSON was not what we wanted, send a 400
            Response(status=status.HTTP_400_BAD_REQUEST)

        author_id = author.split("/")[-1]
        followers = User.objects.filter(follower__user2=author_id, is_active=True)
        following = User.objects.filter(followee__user1=author_id, is_active=True)
        friends = following & followers

        friend_list = list()
        for potential_friend in authors:
            potential_friend_id = potential_friend.split("/")[-1]
            for friend in friends:
                if str(friend.id) == potential_friend_id:
                    friend_list.append(potential_friend)
                    break

        response = {
            "query":"friends",
            "author": author,
            "authors": friend_list
        }

        return Response(response)


class FriendRequestAPIView(generics.GenericAPIView):

    queryset = FriendRequest.objects.all()

    def post(self, request, *args, **kwargs):

        if not authorized(request):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Retrieves JSON data
        data = request.data
        try:
            author_id = data['author']['id'].split("/")[-1]
            friend_id = data['friend']['id'].split("/")[-1]
        except:
            # If the JSON was not what we wanted, send a 400
            Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            followers = User.objects.filter(follower__user2=author_id, is_active=True)
            following = User.objects.filter(followee__user1=author_id, is_active=True)
            friends = following & followers
        except:
            # TODO: What is the correct status code here?
            Response(status=status.HTTP_200_OK)

        already_following = False
        for followee in following:
            if str(friend_id) == str(followee.id):
                already_following = True

        # If user1 is already following user2, then a request must have previously been made
        if not already_following:
            try:
                user1 = User.objects.get(pk=author_id)
                user2 = User.objects.get(pk=friend_id)
                Follow.objects.create(user1=user1, user2=user2)

                # Query to see if the person they want to follow is already following requestor
                exists_in_table = FriendRequest.objects.filter(requestor=user2,recipient=user1)

                if (len(exists_in_table) == 0) & (follows(user2,user1) == False):
                    FriendRequest.objects.create(requestor= user1,recipient= user2)
                elif len(exists_in_table) != 0:
                    exists_in_table.delete()

            except:
                # TODO: What is the correct status code here?
                Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_200_OK)
