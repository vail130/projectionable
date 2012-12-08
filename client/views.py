from rest_framework.views import APIView
from api.models import AccountRequest, Account
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.conf import settings

SITE_DESCRIPTION = """A structured workflow for developing modern applications with front-end clients
and back-end servers through RESTful APIs."""

SITE_KEYWORDS = "agile software development, workflow, web app, software application"

class App(APIView):
    
    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": SITE_DESCRIPTION,
            "keywords": SITE_KEYWORDS,
            "page": "app"
        }
        
        if request.user.is_authenticated():
            context['valid_session'] = True
            context['user_id'] = request.user.id
        else:
            context['valid_session'] = False
            
            ###
            # Remove before deployment
            
            try:
                account = Account.objects.latest('date_created')
            except Account.DoesNotExist:
                account = Account.create_account('vail130@gmail.com', 'asdf', code=list(settings.ADMIN_CODES)[0])
            
            user = authenticate(username=account.user.username, password='asdf')
            login(request, user)
            context['valid_session'] = True
            context['user_id'] = account.user.id
            
            # Remove before deployment
            ###
        
        return render_to_response('app.html', context, context_instance=RequestContext(request))

class Home(APIView):
    
    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": SITE_DESCRIPTION,
            "keywords": SITE_KEYWORDS,
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

class Pricing(APIView):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": SITE_DESCRIPTION,
            "keywords": SITE_KEYWORDS,
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

class Signin(APIView):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": SITE_DESCRIPTION,
            "keywords": SITE_KEYWORDS,
            "page": "signin",
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            context['valid_session'] = False
        else:
            return redirect('/')

        return render_to_response('signin.html', context, context_instance=RequestContext(request))

class Signup(APIView):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": SITE_DESCRIPTION,
            "keywords": SITE_KEYWORDS,
            "page": "signup",
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            context['valid_session'] = False
        else:
            return redirect('/')

        return render_to_response('signup.html', context, context_instance=RequestContext(request))

class VerifyEmail(APIView):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": SITE_DESCRIPTION,
            "keywords": SITE_KEYWORDS,
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

class ResetPassword(APIView):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": SITE_DESCRIPTION,
            "keywords": SITE_KEYWORDS,
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

class VerifyInvitation(APIView):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": SITE_DESCRIPTION,
            "keywords": SITE_KEYWORDS,
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

class ContactUs(APIView):

    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": SITE_DESCRIPTION,
            "keywords": SITE_KEYWORDS,
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

class Terms(APIView):
    
    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": SITE_DESCRIPTION,
            "keywords": SITE_KEYWORDS,
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

class Privacy(APIView):
    
    def get(self, request):
        context = {
            "site_name": settings.SITE_NAME.lower(),
            "site_url": settings.BASE_URL,
            "static_url": settings.STATIC_URL,
            "title": settings.SITE_NAME,
            "description": SITE_DESCRIPTION,
            "keywords": SITE_KEYWORDS,
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

