from djangorestframework.views import View
from account_api.models import AccountRequest, Account
from django.contrib.auth import authenticate, login
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.conf import settings

class App(View):
    
    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": "",
            "keywords": "",
            "page": "app"
        }
        
        try:
            session_id = int(request.session["_auth_user_id"])
        except KeyError:
            return redirect('/home')
        else:
            context['valid_session'] = True
            context['user_id'] = session_id
            return render_to_response('app.html', context, context_instance=RequestContext(request))

class Home(View):
    
    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": "",
            "keywords": "",
            "page": 'home',
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            context['valid_session'] = False
            context['user_id'] = None
        else:
            context['valid_session'] = True
            context['user_id'] = request.session["_auth_user_id"]

        return render_to_response('home.html', context, context_instance=RequestContext(request))

class Pricing(View):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": "",
            "keywords": "",
            "page": 'pricing',
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            context['valid_session'] = False
            context['user_id'] = None
        else:
            context['valid_session'] = True
            context['user_id'] = request.session["_auth_user_id"]

        return render_to_response('pricing.html', context, context_instance=RequestContext(request))

class Signin(View):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": "",
            "keywords": "",
            "page": "signin",
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            context['valid_session'] = False
        else:
            return redirect('/')

        return render_to_response('signin.html', context, context_instance=RequestContext(request))

class Signup(View):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": "",
            "keywords": "",
            "page": "signup",
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            context['valid_session'] = False
        else:
            return redirect('/')

        return render_to_response('signup.html', context, context_instance=RequestContext(request))

class VerifyEmail(View):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": "",
            "keywords": "",
            "page": "verify_email",
        }

        try:
            account_id = request.GET['account_id']
        except KeyError:
            return redirect('/')

        try:
            code = request.GET['code']
        except KeyError:
            return redirect('/')

        try:
            ar = AccountRequest.objects.get(account_id=account_id, code=code, status='pending', type__in=['create-account', 'change-email'])
        except AccountRequest.DoesNotExist:
            return redirect('/')

        context['email'] = ar.request
        context['code'] = code
        context['account_id'] = account_id

        return render_to_response('verify_email.html', context, context_instance=RequestContext(request))

class ResetPassword(View):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": "",
            "keywords": "",
            "page": "reset_password",
        }

        try:
            account_id = request.GET['account_id']
        except KeyError:
            return redirect('/')

        try:
            code = request.GET['code']
        except KeyError:
            return redirect('/')

        try:
            ar = AccountRequest.objects.get(account_id=account_id, code=code, status='pending', type='reset-password')
        except AccountRequest.DoesNotExist:
            return redirect('/')

        context['code'] = code
        context['account_id'] = account_id
        context['email'] = ar.account.email

        return render_to_response('reset_password.html', context, context_instance=RequestContext(request))

class VerifyInvitation(View):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": "",
            "keywords": "",
            "page": "verify_invitation",
        }

        try:
            account_id = request.GET['account_id']
        except KeyError:
            return redirect('/')

        try:
            code = request.GET['code']
        except KeyError:
            return redirect('/')

        try:
            ar = AccountRequest.objects.get(account_id=account_id, code=code, status='pending', type='create-invitation-account')
        except AccountRequest.DoesNotExist:
            return redirect('/')

        context['email'] = ar.request
        context['code'] = code
        context['account_id'] = account_id

        return render_to_response('verify_invitation.html', context, context_instance=RequestContext(request))

class ContactUs(View):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": "",
            "keywords": "",
            "page": "contact",
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            context['valid_session'] = False
            context['user_id'] = None
        else:
            context['valid_session'] = True
            context['user_id'] = request.session["_auth_user_id"]

        return render_to_response('contact.html', context, context_instance=RequestContext(request))

class Terms(View):
    
    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": "",
            "keywords": "",
            "page": 'terms',
            "company": "Projectionable",
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            context['valid_session'] = False
            context['user_id'] = None
        else:
            context['valid_session'] = True
            context['user_id'] = request.session["_auth_user_id"]

        return render_to_response('terms.html', context, context_instance=RequestContext(request))

class Privacy(View):
    
    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": "",
            "keywords": "",
            "page": 'privacy',
            "company": "Projectionable",
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            context['valid_session'] = False
            context['user_id'] = None
        else:
            context['valid_session'] = True
            context['user_id'] = request.session["_auth_user_id"]

        return render_to_response('privacy.html', context, context_instance=RequestContext(request))

