from django.conf.urls import patterns, url
from django.conf import settings
from app.views import *
from project_api.views import *
from account_api.views import *

urlpatterns = patterns('',
    url(r'^$', App.as_view(), name='app'),
    
    #url(r'^home/?$', Home.as_view(), name='home'),
    #url(r'^signup/?$', Signup.as_view(), name='signup'),
    #url(r'^signin/?(?:\?.*)?$', Signin.as_view(), name='signin'),
    #url(r'^verify_email/?(?:\?.*)?$', VerifyEmail.as_view(), name='verifyemail'),
    #url(r'^reset_password/?(?:\?.*)?$', ResetPassword.as_view(), name='resetpassword'),
    #url(r'^verify_invitation/?(?:\?.*)?$', VerifyInvitation.as_view(), name='verifyinvitation'),
    
    #url(r'^contact/?$', ContactUs.as_view(), name='contact'),
    #url(r'^terms/?$', Terms.as_view(), name='terms'),
    #url(r'^privacy/?$', Privacy.as_view(), name='privacy'),
    
    url(r'^api/permissions/(?P<permission_id>[^/\?]+)/?(?:\?.*)?$', PermissionEditor.as_view(), name='permissioneditor'),
    url(r'^api/permissions/?(?:\?.*)?$', PermissionManager.as_view(), name='permissionmanager'),
    
    url(r'^api/projects/(?P<project_id>[^/\?]+)/?(?:\?.*)?$', ProjectEditor.as_view(), name='projecteditor'),
    url(r'^api/projects/?(?:\?.*)?$', ProjectManager.as_view(), name='projectmanager'),
    
    url(r'^api/groups/(?P<group_id>[^/\?]+)/?(?:\?.*)?$', GroupEditor.as_view(), name='groupeditor'),
    url(r'^api/groups/?(?:\?.*)?$', GroupManager.as_view(), name='groupmanager'),
    
    url(r'^api/requirements/(?P<req_id>[^/\?]+)/?(?:\?.*)?$', RequirementEditor.as_view(), name='requirementeditor'),
    url(r'^api/requirements/?(?:\?.*)?$', RequirementManager.as_view(), name='requirementmanager'),
    
    url(r'^api/assets/(?P<asset_id>[^/\?]+)/?(?:\?.*)?$', AssetEditor.as_view(), name='asseteditor'),
    url(r'^api/assets/?(?:\?.*)?$', AssetManager.as_view(), name='assetmanager'),
    
    url(r'^api/files/(?P<project_file_id>[^/\?]+)/?(?:\?.*)?$', FileEditor.as_view(), name='fileeditor'),
    url(r'^api/files/?(?:\?.*)?$', FileManager.as_view(), name='filemanager'),
    
    url(r'^api/sessions/(?P<session_id>[^/\?]+)/?(?:\?.*)?$', SessionEditor.as_view(), name='sessioneditor'),
    url(r'^api/sessions/?(?:\?.*)?$', SessionManager.as_view(), name='sessionmanager'),
    
    url(r'^api/accounts/?(?:\?.*)?$', AccountManager.as_view(), name='accountmanager'),
    url(r'^api/accounts(?:/(?P<account_id>[0-9]+)/?)?(?:\?.*)?$', AccountEditor.as_view(), name='accounteditor'),
    
    url(r'^api/contacts/(?P<contact_id>[^/\?]+)/?(?:\?.*)?$', ContactEditor.as_view(), name='contacteditor'),
    url(r'^api/contacts/?(?:\?.*)?$', ContactManager.as_view(), name='contactmanager'),
    
    #url(r'^api/payments/?(?:\?.*)?$', PaymentManager.as_view(), name='paymentmanager'),
    #url(r'^api/payments(?:/(?P<payment_id>[0-9]+)/?)?(?:\?.*)?$', PaymentEditor.as_view(), name='paymenteditor'),
)

urlpatterns += patterns('',
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)