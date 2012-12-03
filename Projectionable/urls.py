from django.conf.urls import patterns, url
from django.conf import settings
from client import views
from api import views as apiviews

urlpatterns = patterns('',
    url(r'^$', views.App.as_view(), name='app'),
    
    #url(r'^home/?$', Home.as_view(), name='home'),
    #url(r'^signup/?$', Signup.as_view(), name='signup'),
    #url(r'^signin/?(?:\?.*)?$', Signin.as_view(), name='signin'),
    #url(r'^verify_email/?(?:\?.*)?$', VerifyEmail.as_view(), name='verifyemail'),
    #url(r'^reset_password/?(?:\?.*)?$', ResetPassword.as_view(), name='resetpassword'),
    #url(r'^verify_invitation/?(?:\?.*)?$', VerifyInvitation.as_view(), name='verifyinvitation'),
    
    #url(r'^contact/?$', ContactUs.as_view(), name='contact'),
    #url(r'^terms/?$', Terms.as_view(), name='terms'),
    #url(r'^privacy/?$', Privacy.as_view(), name='privacy'),
    
    url(r'^api/permissions/(?P<permission_id>[^/\?]+)/?(?:\?.*)?$', apiviews.PermissionEditor.as_view(), name='permissioneditor'),
    url(r'^api/permissions/?(?:\?.*)?$', apiviews.PermissionManager.as_view(), name='permissionmanager'),
    
    url(r'^api/projects/(?P<project_id>[^/\?]+)/?(?:\?.*)?$', apiviews.ProjectEditor.as_view(), name='projecteditor'),
    url(r'^api/projects/?(?:\?.*)?$', apiviews.ProjectManager.as_view(), name='projectmanager'),
    
    url(r'^api/groups/(?P<group_id>[^/\?]+)/?(?:\?.*)?$', apiviews.GroupEditor.as_view(), name='groupeditor'),
    url(r'^api/groups/?(?:\?.*)?$', apiviews.GroupManager.as_view(), name='groupmanager'),
    
    url(r'^api/requirements/(?P<req_id>[^/\?]+)/?(?:\?.*)?$', apiviews.RequirementEditor.as_view(), name='requirementeditor'),
    url(r'^api/requirements/?(?:\?.*)?$', apiviews.RequirementManager.as_view(), name='requirementmanager'),
    
    url(r'^api/assets/(?P<asset_id>[^/\?]+)/?(?:\?.*)?$', apiviews.AssetEditor.as_view(), name='asseteditor'),
    url(r'^api/assets/?(?:\?.*)?$', apiviews.AssetManager.as_view(), name='assetmanager'),
    
    url(r'^api/files/(?P<project_file_id>[^/\?]+)/?(?:\?.*)?$', apiviews.FileEditor.as_view(), name='fileeditor'),
    url(r'^api/files/?(?:\?.*)?$', apiviews.FileManager.as_view(), name='filemanager'),
    
    url(r'^api/sessions/(?P<session_id>[^/\?]+)/?(?:\?.*)?$', apiviews.SessionEditor.as_view(), name='sessioneditor'),
    url(r'^api/sessions/?(?:\?.*)?$', apiviews.SessionManager.as_view(), name='sessionmanager'),
    
    url(r'^api/accounts(?:/(?P<account_id>[0-9]+)/?)?(?:\?.*)?$', apiviews.AccountEditor.as_view(), name='accounteditor'),
    url(r'^api/accounts/?(?:\?.*)?$', apiviews.AccountManager.as_view(), name='accountmanager'),
    
    url(r'^api/contacts/(?P<contact_id>[^/\?]+)/?(?:\?.*)?$', apiviews.ContactEditor.as_view(), name='contacteditor'),
    url(r'^api/contacts/?(?:\?.*)?$', apiviews.ContactManager.as_view(), name='contactmanager'),
    
    #url(r'^api/payments/?(?:\?.*)?$', PaymentManager.as_view(), name='paymentmanager'),
    #url(r'^api/payments(?:/(?P<payment_id>[0-9]+)/?)?(?:\?.*)?$', PaymentEditor.as_view(), name='paymenteditor'),
)

urlpatterns += patterns('',
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)