from turtle import update
from unicodedata import category
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User,Category,Listing,Comment,Bid


def index(request):
    activeListings = Listing.objects.filter(active = True)
    allcategory = Category.objects.all()
    return render(request, "auctions/index.html",{
        "listings" : activeListings,
        "category" : allcategory,
    })
def displaycategory(request):
    if request.method == "POST":
        categorySelected = request.POST['category']
        category = Category.objects.get(categoryName = categorySelected)
        activeListings = Listing.objects.filter(active = True,category = category)
        allcategory = Category.objects.all()
        return render(request, "auctions/index.html",{
            "listings" : activeListings,
            "category" : allcategory,
    })
def detail(request,id):
    listingData = Listing.objects.get(pk=id)
    watchlist = request.user in listingData.watchlist.all()
    isOwner = request.user.username == listingData.owner.username
    allComments = Comment.objects.filter(listing = listingData)
    return render(request, "auctions/detail.html" , {
        "listing" : listingData,
         "listingInWatchlist" : watchlist,
         "comments" : allComments,  
         "isOwner" : isOwner
    })
def addBid(request, id):
    newBid = request.POST["bid"]
    listingData = Listing.objects.get(pk=id)
    watchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing = listingData)
    isOwner = request.user.username == listingData.owner.username
    if float(newBid) > listingData.price.bid:
        updateBid = Bid(
            bid = newBid,
            user = request.user, 
        )
        updateBid.save()
        listingData.price = updateBid
        listingData.save()
        return render(request, "auctions/detail.html",{
            "listing" : listingData,
            "message" : "Bid was updated successfully",
            "update" : True,
            "listingInWatchlist" : watchlist,
            "comments" : allComments,
            "isOwner": isOwner,
            "dispalyMessage":True
        })
    else:
        return render(request, "auctions/detail.html",{
            "listing" : listingData,
            "message" : "Bidding failed! Bid was too low",
            "update" : False,
            "listingInWatchlist" : watchlist,
            "comments" : allComments,
            "dispalyMessage":True,
            "isOwner": isOwner,
        })
def closeAuction(request,id):
    listingData = Listing.objects.get(pk=id)
    listingData.active = False
    isOwner = request.user.username == listingData.owner.username
    watchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing = listingData)
    listingData.save()
    return render(request, "auctions/detail.html",{
        "listing" : listingData,
        "message" : "Congratulations! Your Auction is Closed successfully.",
        "update" : True,
        "listingInWatchlist" : watchlist,
        "comments" : allComments,
        "dispalyMessage":True,
        "isOwner": isOwner,
        })
def addComment(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    message = request.POST['comment']
    comment = Comment(
        author = currentUser,
        listing = listingData,
        message = message,
    ) 
    comment.save()
    return HttpResponseRedirect(reverse("detail",args=(id, )))

def addWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.add(currentUser)
    return HttpResponseRedirect(reverse("detail",args=(id, )))

def removeWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.remove(currentUser)
    return HttpResponseRedirect(reverse("detail",args=(id, )))

def displayWatchlist(request):
    currentUser = request.user
    listings = currentUser.watchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listing" : listings
    })

def createListing(request):
    if request.method == "GET":
        allcategory = Category.objects.all()
        return render(request, "auctions/create.html", {
        "categories" : allcategory
        })
    else :
        #Get data
        title = request.POST["title"]
        description = request.POST["description"]
        imageurl = request.POST["imageurl"]
        price = request.POST["price"]
        category = request.POST["category"]
        #user
        currentUser = request.user
        categoryData = Category.objects.get(categoryName = category)
        #Adding Bidding
        bid = Bid(
            bid = float(price),
            user = currentUser
        )
        bid.save()
        #new Listing
        newListing = Listing(
            title = title,
            description = description,
            imageUrl = imageurl,
            price = bid,
            category = categoryData,
            owner = currentUser
        )
        newListing.save()
        return HttpResponseRedirect(reverse(index))


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
