from django.http import HttpResponse
from django.core import serializers
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.db.models import Q
import json

from users.models import User
from friends.models import Follow, FriendRequest
from friends.models import Follow

# Just get a list of Users on the server, minus the user making the request
def find(request):

    if not request.user.is_authenticated:
        return HttpResponseForbidden()



    server_users = User.objects.exclude(pk=request.user.id).filter(is_active=True)

    data = serializers.serialize('json', server_users, fields=('username'))

    return HttpResponse(data, content_type="application/json")


# Get a list of Users who the current user follows
def following(request):

    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    # E.g., look at Follow table results where I am the follower
    # following = User.objects.filter(followee__user1=request.user.id, is_active=True)
    user_query = Q()
    following_obj = Follow.objects.filter(user1=request.user.id)
    if len(following_obj) != 0:
        for followee in following_obj:

            user_query = user_query | Q(id=followee.user2)
        
        following = User.objects.filter(user_query)
    else:
        following = User.objects.none()
 
    
    data = serializers.serialize('json', following, fields=('username'))
    return HttpResponse(data, content_type="application/json")

# Get a list of Users who follow the current user
def followers(request):

    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    # Look at Follow table results where I am the followee
    # followers = User.objects.filter(follower__user2=request.user.id, is_active=True)
    follower_obj = Follow.objects.filter(Q(user2=request.user.id))
    if len(follower_obj) != 0:
        user_Q = Q()
        for follower in follower_obj:
            user_Q = user_Q | Q(id=follower.user1)
        followers = User.objects.filter(user_Q)
    else:
        followers = User.objects.none()

    
    data = serializers.serialize('json', followers, fields=('username'))
    return HttpResponse(data, content_type="application/json")

# Get a list of Users who the current user is friends with
def friends(request):

    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    # followers = User.objects.filter(follower__user2=request.user.id, is_active=True)
    # following = User.objects.filter(followee__user1=request.user.id, is_active=True)
    # friends = following & followers

    #TODO make more efficient
    uid = request.user.id
    user_Q = Q()
    follow_obj = Follow.objects.filter(Q(user2=uid)|Q(user1=uid))

    if len(follow_obj) != 0:
        for follow in follow_obj:
            if follow.user1==uid:
                recip_object = Follow.objects.filter(user1=follow.user2,user2=follow.user1)
                if len(recip_object) != 0:
                    user_Q = user_Q | Q(id=follow.user2)
            elif follow.user2==uid:
                recip_object = Follow.objects.filter(user1=follow.user2,user2=follow.user1)
                if len(recip_object) != 0:
                    user_Q = user_Q | Q(id=follow.user1)
        if len(user_Q) != 0:
            friends = User.objects.filter(user_Q)
        else:
            friends = User.objects.none()
    else:
        friends = User.objects.none()

    data = serializers.serialize('json', friends, fields=('username'))
    return HttpResponse(data, content_type="application/json") 

def follow(request):

    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    followerID = request.GET['followerID']
    followeeID = request.GET['followeeID']

    # TODO: Find a good way to error handle these two DB calls
    user1 = User.objects.get(pk=followerID)
    user2 = User.objects.get(pk=followeeID)
    Follow.objects.create(user1=user1.id, user2=user2.id)

     ####add into FriendRequest table####
    #Query to see if the person they want to follow is already following requestor
    exists_in_table = FriendRequest.objects.filter(requestor=user2.id,recipient=user1.id)

    if (len(exists_in_table) == 0) & (follows(user2.id,user1.id) == False):
        FriendRequest.objects.create(requestor= user1.id,recipient= user2.id)
    elif len(exists_in_table) != 0:
        exists_in_table.delete()

    data = {'followerID': followerID, 'followeeID': followeeID}
    return HttpResponse(json.dumps(data), content_type="application/json")
    #return HttpResponse()


def unfollow(request):

    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    followerID = request.GET['followerID']
    followeeID = request.GET['followeeID']

    # This should only delete one entry since we have a unique_together
    # constraint on the attributes user1 and user2
    Follow.objects.filter(user1=followerID, user2=followeeID).delete()

     ##check if there is pending friend request from them
    exists_requests = FriendRequest.objects.filter(requestor=followerID,recipient=followeeID)
    if len(exists_requests) != 0:
        exists_requests.delete()

    data = {'followerID': followerID, 'followeeID': followeeID}
    return HttpResponse(json.dumps(data), content_type="application/json")
    #return HttpResponse()


# Return a boolean stating if user1 follows user2
def follows(user1ID, user2ID):

        following = Follow.objects.filter(user1=user1ID, user2=user2ID)
        if following:
            return True
        else:
            return False


def friend_requests(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    print ("REQUEST FRIEND")
    friend_reqs = FriendRequest.objects.filter(recipient=request.user.id)
    host = request.get_host()
    data2 = {"posts": []}
    for reqs in friend_reqs:
        print(reqs.requestor)
        user_filter = user_filter | Q(username=reqs.requestor)
        user = User.objects.filter(id = reqs.requestor)
        if not user:
            user = get_user(reqs.requestor_server, reqs.requestor)
        else:
            user = user[0]
        host = strip_host(user.host)
        data2["posts"].append({'id':str(user.id), 'username':user.username, 'host': host})
    return HttpResponse(json.dumps(data2), content_type='application/json')


def strip_host(host):
    re_result = re.search("(^https?:\/\/)(.*)", host)
    if (re_result):
        host = re_result.group(2)
    return host


def get_user(server, id):
    user = User()
    build_request = server+'/service/author/'+str(id)
    print (build_request)
    try:
        r=requests.get(build_request)
        response = r.json()
    except:
        print("That user does not exist")
    user.username = response['displayName']
    user.id = response['id']
    user.host = server
    return user
