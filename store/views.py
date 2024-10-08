from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Profile, Review, Wishlist, WishlistItem
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .forms import (
    SignUpForm,
    UpdateUserForm,
    ChangePasswordForm,
    UserInfoForm,
    ReviewForm,
)
from payment.forms import ShippingForm
from payment.models import ShippingAddress
from django import forms
from django.db.models import Q
import json
from cart.cart import Cart


def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        messages.success(request, "You Must Be In Logged In To Use Feature")
        return redirect("home")

    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
    messages.success(request, "Added to Wishlist")
    return redirect("product", pk=product.id)


def remove_from_wishlist(request, product_id):
    if not request.user.is_authenticated:
        messages.success(request, "You Must Be In Logged In To Use Feature")
        return redirect("home")

    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()
    messages.success(request, "Removed from Wishlist")
    return redirect("wishlist_view")


def wishlist_view(request):
    if not request.user.is_authenticated:
        messages.success(request, "You Must Be In Logged In To Use Feature")
        return redirect("home")

    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    items = WishlistItem.objects.filter(wishlist=wishlist)
    return render(request, "wishlist.html", {"items": items})


def home(request):
    # fetch all products from the DB
    products = Product.objects.all()
    categories = Category.objects.all()
    # render with list of products
    return render(request, "home.html", {"products": products})


def about(request):
    return render(request, "about.html", {})


def login_user(request):
    # if the request method if POST
    if request.method == "POST":
        # get the user and pass from the submitted form data
        username = request.POST["username"]
        password = request.POST["password"]
        # authenticate the user with the provided credentials
        user = authenticate(request, username=username, password=password)
        # if user exists and credentials are valid
        if user is not None:
            # log the user in and displat a success message
            login(request, user)

            # cart persistance
            current_user = Profile.objects.get(user__id=request.user.id)

            # get saved cart from DB
            saved_cart = current_user.old_cart

            # convert DB string to dict
            if saved_cart:
                # convert to dict
                converted_cart = json.loads(saved_cart)
                # add the loaded cart dict to session
                cart = Cart(request)
                # loop through cart and add items from DB
                for key, value in converted_cart.items():
                    cart.db_add(product=key, quantity=value)

            messages.success(request, ("You Have Been Logged In!"))
            return redirect("home")
        else:
            # diplay if authentication fails
            messages.success(request, ("There was an error, please try again..."))
            return redirect("login")
    else:
        return render(request, "login.html", {})


def logout_user(request):
    # log the user out
    logout(request)
    messages.success(request, ("You Have Been Logged Out..."))
    return redirect("home")


def register_user(request):
    # create an empty instance
    form = SignUpForm()
    # check if the request method is POST
    if request.method == "POST":
        # create a form instance populated with the submitted data
        form = SignUpForm(request.POST)
        # validate form data
        if form.is_valid():
            # save the valif form data to DB (creates a new user)
            form.save()
            # extract username and password
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            # authenticater user with the provided username and password
            user = authenticate(username=username, password=password)
            # log the user (creates a session)
            login(request, user)
            messages.success(
                request,
                ("Username Created - Please Fill Out Your Billing Info Below..."),
            )
            return redirect("update_info")
        else:
            messages.success(
                request, ("There was a problem Registering, please try again")
            )
            return redirect("register")
    else:
        return render(request, "register.html", {"form": form})


def product(request, pk):
    # fetch the product with the give pk from the DB
    product = Product.objects.get(id=pk)

    reviews_list = product.reviews.all()

    paginator = Paginator(reviews_list, 5)  # 5 reviews per page
    page_number = request.GET.get("page")
    reviews = paginator.get_page(page_number)

    # render the html page with product details
    return render(request, "product.html", {"product": product, "reviews": reviews})


# click on a category name and it'll take you there
def category(request, foo):
    foo = foo.replace("-", " ")
    # grab the category from the url
    try:
        # look up the category by name
        category = Category.objects.get(name=foo)
        # fetch the products belonging to the category
        products = Product.objects.filter(category=category)
        # render the html with products and category
        return render(
            request, "category.html", {"products": products, "category": category}
        )
    except:
        messages.success(request, ("Category Not Found"))
        return redirect("home")


def category_list(request):
    # fetch all categories from the DB
    categories = Category.objects.all()
    # return the html with the list of categories
    return render(request, "category_list.html", {"categories": categories})


def update_user(request):
    # check if user is authenticated
    if request.user.is_authenticated:
        # fetch the curernt users's data
        current_user = User.objects.get(id=request.user.id)
        # create a form pre-filled with the user data
        user_form = UpdateUserForm(request.POST or None, instance=current_user)

        # if form is valid (submitted). update the user data, and log them in
        if user_form.is_valid():
            user_form.save()

            login(request, current_user)
            messages.success(request, "User Has Been Updated!")
            return redirect("home")
        return render(request, "update_user.html", {"user_form": user_form})
    else:
        messages.success(request, "You Must Be In Logged In To Access Page")
        return redirect("home")


def update_password(request):
    # check if user is authenticated
    if request.user.is_authenticated:
        # get the current user
        current_user = request.user

        # check if request is 'POST'
        if request.method == "POST":
            # create a password change form
            form = ChangePasswordForm(current_user, request.POST)

            # if form is valid, save the password, log in the user, and redirect them
            if form.is_valid():
                form.save()
                messages.success(request, "Your Password Has Been Updated...")
                login(request, current_user)
                return redirect("update_user")
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
                    return redirect("update_password")
        else:
            # if request method is 'GET' display the password change form
            form = ChangePasswordForm(current_user)
            return render(request, "update_password.html", {"form": form})

    else:
        messages.success(request, "You Must Be In Logged In To Access Page")
        return redirect("home")


def update_info(request):
    # check if the user authenticated
    if request.user.is_authenticated:
        # get the current user profile
        current_user = Profile.objects.get(user__id=request.user.id)
        # get the current user shipping info
        shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
        # create a form pre filled with the user profile data
        form = UserInfoForm(request.POST or None, instance=current_user)
        # create form pre filled with user shipping info
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
        # if form valid- save profile data, display msg, redirect to home page
        if form.is_valid() or shipping_form.is_valid():
            form.save()
            shipping_form.save()

            messages.success(request, "Your Info Has Been Updated!")
            return redirect("home")
        # render the html with profile form
        return render(
            request, "update_info.html", {"form": form, "shipping_form": shipping_form}
        )
    else:
        messages.success(request, "You Must Be In Logged In To Access Page")
        return redirect("home")


def search(request):
    # check if request is 'POST'
    if request.method == "POST":
        # get the search term from the submitted data
        searched = request.POST["searched"]

        # query the Products DB Model for products matching the search term
        searched = Product.objects.filter(
            Q(name__icontains=searched) | Q(description__icontains=searched)
        )

        # test for null
        # if no product found- display error, and render html with no results
        if not searched:
            messages.success(request, "That Product Does Not Exist...")
            return render(request, "search.html", {})

        else:
            # render html with results
            return render(request, "search.html", {"searched": searched})
    else:
        # if the request is 'GET' display the search form
        return render(request, "search.html", {})


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        rating = request.POST.get("rating")
        text = request.POST.get("text")

        Review.objects.create(
            product=product, user=request.user, rating=rating, text=text
        )
        messages.success(request, "Your Review Has Been Added!")

        return redirect("product", pk=product.id)
    return redirect("product", pk=product.id)
