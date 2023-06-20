from django.shortcuts import render, redirect, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.contrib.auth import update_session_auth_hash, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import cache_control

from . import forms
from . import models

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('main:home')
    
    if request.method == 'POST':
        form = forms.CustomAuthenticationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user, backend='main.backends.EmailBackend')
                return redirect('main:home')
    else:
        form = forms.CustomAuthenticationForm()

    return render(request,"main/login.html", { 'form':form, })

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup_view(request):
    if request.user.is_authenticated:   
        return redirect('main:home')

    if request.method == 'POST':
        form = forms.CustomUserCreationForm(request.POST)
        if form.is_valid():
            user_data = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
                'contact_number': form.cleaned_data['contact_number'],
                'password1': form.cleaned_data['password1'],
                'password2': form.cleaned_data['password2'],
            }
            request.session['user_data'] = user_data
            form.send_otp_email(request)
            return redirect('main:verify')  
    else:
        form = forms.CustomUserCreationForm()

    return render(request, 'main/signup.html', { 'form':form, })

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def verify_view(request):
    if request.user.is_authenticated:
        return redirect('main:home')

    user_data = request.session.get('user_data')
    if not user_data:
        return redirect('main:signup')

    if request.method == 'POST':
        form = forms.OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            if str(request.session.get('otp')) == str(otp):
                contact_number = user_data['contact_number']

                user_data['password'] = user_data['password1']
                user_data['username']=str(user_data['first_name']+'-'+user_data['last_name']+'-'+timezone.now().strftime('%Y%m%d%H%M%S')).lower()
                del user_data['password1']
                del user_data['password2']
                del user_data['contact_number']

                user = User.objects.create_user(**user_data)
                user_profile = models.UserProfile.objects.create(user=user, contact_number=contact_number)

                user.save()

                del request.session['user_data']
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return redirect('main:home')
            else:
                form.add_error('otp', 'Wrong OTP!')
    else:
        form = forms.OTPVerificationForm()

    return render(request, 'main/verify.html', { 'form':form, })


@login_required
def home_view(request):
    user = request.user
    reviews = models.Review.objects.all()
    rec_reviews = reviews.filter(to_user=user.username)
    giv_reviews = reviews.filter(from_user=user.username)  

    # upvote-downvote
    if request.method == 'POST':
        if 'action' in request.POST:
            review_id = request.POST.get('review_id')
            action = request.POST.get('action')
            review = models.Review.objects.get(id=review_id)

            if action == 'upvote':
                review.upvote(user)
            elif action == 'downvote':
                review.downvote(user)
            review.save()
            return redirect('main:home')

    return render(request, 'main/home.html',
        {
            'user': user,
            'reviews':reviews,
            'rec_reviews':rec_reviews,
            'giv_reviews':giv_reviews,
        }
    )


@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('main:login')
    

@login_required
def update_image_view(request):
    try:
        profile = request.user.userprofile
    except ObjectDoesNotExist:
        profile = models.UserProfile(user=request.user)

    if request.method == 'POST':
        form = forms.ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('main:home')
        else:
            print(form.errors)
    else:
        form = forms.ProfileForm(instance=profile)

    return render(request, 'main/update_image.html', { 'form':form, })


@login_required
def update_details_view(request):
    try:
        profile = request.user.userprofile
    except ObjectDoesNotExist:
        profile = models.UserProfile(user=request.user)

    if request.method == 'POST':
        form = forms.ProfileDetailsForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save(request.user)
            return redirect('main:home')
        else:
            print(form.errors)
    else:
        form = forms.ProfileDetailsForm(user=request.user)

    return render(request, 'main/update_details.html', { 'form':form, })
    

@login_required
def update_bio_view(request):
    try:
        profile = request.user.userprofile
    except ObjectDoesNotExist:
        profile = models.UserProfile(user=request.user)

    if request.method == 'POST':
        form = forms.BioForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save(request.user)
            return redirect('main:home')
        else:
            print(form.errors)
    else:
        form = forms.BioForm(user=request.user)

    return render(request, 'main/update_bio.html', { 'form':form, })

@login_required
def user_view(request, username):
    if request.user.username == username:
        return redirect('main:home')
    
    else:
        user = User.objects.get(username=username)
        reviews = models.Review.objects.all()
        rec_reviews = reviews.filter(to_user=username)
        giv_reviews = reviews.filter(anonymous_from=username)

        existing_review = reviews.filter(to_user=username, from_user=request.user.username).first()

        if request.method == 'POST':
            # upvote-downvote
            if 'action' in request.POST:
                review_id = request.POST.get('review_id')
                action = request.POST.get('action')
                review = models.Review.objects.get(id=review_id)

                if action == 'upvote':
                    review.upvote(request.user)
                elif action == 'downvote':
                    review.downvote(request.user)
                review.save()
                return redirect('main:user', username=username)

            # review form
            else:
                reviewform = forms.ReviewForm(request.POST, instance=existing_review)
                if reviewform.is_valid():
                    review = reviewform.save(commit=False)
                    review.to_user = username
                    if reviewform.cleaned_data['is_anonymous']:
                        review.anonymous_from = 'Anonymous'
                    else:
                        review.anonymous = request.user.username
                    review.from_user = request.user.username
                    review.save()
                    return redirect('main:user', username=username)
                else:
                    reviewform = forms.ReviewForm(instance=existing_review)
        else:
            reviewform = forms.ReviewForm(instance=existing_review)

        return render(request, 'main/user.html',
            {
                'user':user,
                'reviewform':reviewform if not existing_review else None,
                'reviews':reviews,
                'rec_reviews':rec_reviews,
                'giv_reviews':giv_reviews,
                'existing_review':existing_review,
            }
        )


@login_required
def search_view(request):
    query = request.GET.get('q')
    
    if not query:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if len(query.split()) > 1:
        first = query.split()[0]
        second = query.split()[1]
        users = User.objects.filter(
            first_name__icontains=first,
            last_name__icontains=second
        ).exclude(username=request.user.username).exclude(is_superuser=True)
    else:
        first = query.split()[0]
        users = User.objects.filter(
            Q(first_name__icontains=first) | Q(last_name__icontains=first)
        ).exclude(username=request.user.username).exclude(is_superuser=True)

    return render(request, 'main/search.html', { 'users': users, 'query': query, })


@login_required
def edit_view(request, review_id):
    try:
        review = models.Review.objects.get(id=review_id)
    except ObjectDoesNotExist:
        return redirect('main:home')
    
    if str(request.user.username) == str(review.from_user):
        if request.method == 'POST':
            if 'edit-review' in request.POST:
                form = forms.ReviewForm(request.POST, instance=review)
                if form.is_valid():
                    updated_review = form.save(commit=False)
                    if form.cleaned_data['is_anonymous']:
                        updated_review.anonymous_from = 'Anonymous'
                    else:
                        updated_review.anonymous_from = request.user.username
                    updated_review.save()
                    return redirect('main:user', username=str(review.to_user))
            else:
                form = forms.ReviewForm(instance=review)
                return render(request, 'main/edit.html', { 'form':form, 'review_id':review_id, 'review':review, 'username':review.to_user, })
            
        else:
            form = forms.ReviewForm(instance=review)
            return render(request, 'main/edit.html', { 'form':form, 'review_id':review_id, 'review':review, 'username':review.to_user, })
        
    return redirect('main:user', username=str(review.to_user))


@login_required
def delete_view(request, review_id):
    review = models.Review.objects.get(id=review_id)

    if str(request.user) == str(review.from_user):
        if request.method == 'POST':
            if 'delete-review' in request.POST:
                review.delete()
                return redirect('main:user', username=str(review.to_user))
            else:
                return render(request, 'main/delete.html', { 'review_id':review_id, 'username':review.to_user, })

        else:
            return render(request, 'main/delete.html', { 'review_id':review_id, 'username':review.to_user, })
    
    return redirect('main:user', username=str(review.to_user))


@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = forms.CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect('main:home')
        else:
            print(form.errors)
    else:
        form = forms.CustomPasswordChangeForm(request.user)

    return render(request, 'main/password_change.html', { 'form':form, })


