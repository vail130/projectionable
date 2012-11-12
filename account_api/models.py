from django.db import models
from django.contrib.auth.models import User
from utilities import *
from django.contrib.auth import authenticate
from django.conf import settings
import re, uuid
from django.template.loader import render_to_string

class Account(models.Model):
  user = models.OneToOneField(User)
  first_name = models.CharField(max_length=50)
  last_name = models.CharField(max_length=50)
  email = models.EmailField(max_length=128)
  status = models.CharField(max_length=20)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)

  statuses = ['pending', 'active', 'terminated']
  
  def record_to_dictionary(self, children=True):
    return {
      "id": self.user_id,
      "first_name": self.first_name,
      "last_name": self.last_name,
      "email": self.email,
      "status": self.status,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
    }

  @staticmethod
  def create_unique_username():
    while True:
      username = uuid.uuid1().hex[:30]
      try:
        User.objects.get(username=username)
      except User.DoesNotExist:
        break
    return username

  @classmethod
  def email_exists(cls, email):
    try:
      cls.objects.get(email=email)
    except cls.DoesNotExist:
      return False
    else:
      return True

  @classmethod
  def create_account(cls, email, password):
    email = email.strip().lower()

    if email == '':
      return {"email": "Email address must not be empty."}

    if cls.email_exists(email):
      return {"email": "Email address is already in use."}

    if re.search('^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', email, re.I) is None:
      return {"email": "Invalid email address."}

    if password == '':
      return {"password": "Password must not be empty."}

    username = cls.create_unique_username()
    user = User.objects.create_user(username, password=password)

    account = cls(
      user=user,
      email=email,
      first_name='',
      last_name='',
      status='pending',
    )
    account.save()

    ar = AccountRequest(
      account=account,
      type='create-account',
      code=AccountRequest.create_unique_code(),
      request=email,
      status='pending',
    )
    ar.save()

    AccountEmail.create_and_send(account, 'account-created', request=ar)
    return account

  @classmethod
  def create_invitation_account(cls, email):
    email = email.strip().lower()

    if email == '':
      return {"email": "Email address must not be empty."}

    if cls.email_exists(email):
      return {"email": "Email address is already in use."}

    if re.search('^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', email, re.I) is None:
      return {"email": "Invalid email address."}

    password = uuid.uuid1().hex
    username = cls.create_unique_username()
    user = User.objects.create_user(username, password=password)

    account = cls(
      user=user,
      email=email,
      first_name='',
      last_name='',
      status='pending',
    )
    account.save()

    ar = AccountRequest(
      account=account,
      type='create-invitation-account',
      code=AccountRequest.create_unique_code(),
      request=email,
      status='pending',
    )
    ar.save()

    AccountEmail.create_and_send(account, 'invitation-account-created', request=ar)
    return account

  def verify_email(self, code):
    try:
      ar = AccountRequest.objects.get(account=self, code=code, status='pending')
    except AccountRequest.DoesNotExist:
      return {"code": "Invalid code."}

    if ar.type not in ['create-account', 'change-email']:
      return {"code": "Invalid code."}

    ar.status = 'complete'
    ar.save()

    self.status = 'active'

    if ar.type == 'change-email':
      self.email = ar.request

    self.save()

    AccountEmail.create_and_send(self, 'email-verified', request=ar)
    return True

  def verify_invitation(self, code, password):
    try:
      ar = AccountRequest.objects.get(account=self, code=code, type='create-invitation-account', status='pending')
    except AccountRequest.DoesNotExist:
      print self.id, code
      return {"code": "Invalid code."}

    ar.status = 'complete'
    ar.save()

    self.status = 'active'
    self.save()

    user = self.user
    user.set_password(password)
    user.save()

    AccountEmail.create_and_send(self, 'invitation-verified', request=ar)
    return True

  def request_email_change(self, password, email):
    user = authenticate(username=self.user.username, password=password)
    if user is None:
      return {"password": "Invalid password."}

    if email == '':
      return {"email": "Email address must not be empty."}

    if Account.email_exists(email):
      return {"email": "Email address is already in use."}

    if re.search('^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', email, re.I) is None:
      return {"email": "Invalid email address."}

    ar = AccountRequest(
      account=self,
      type='change-email',
      code=AccountRequest.create_unique_code(),
      request=email,
      status='pending',
    )
    ar.save()

    AccountEmail.create_and_send(self, 'email-change-requested', request=ar)
    return True

  @classmethod
  def request_reset_password(cls, email):
    try:
      account = Account.objects.get(email=email)
    except Account.DoesNotExist:
      return {"email": "Invalid email address."}

    ar = AccountRequest(
      account=account,
      type='reset-password',
      code=AccountRequest.create_unique_code(),
      status='pending',
    )
    ar.save()

    AccountEmail.create_and_send(account, 'password-reset-requested', request=ar)
    return True

  def reset_password(self, code, password):
    try:
      ar = AccountRequest.objects.get(account=self, code=code, status='pending', type='reset-password')
    except AccountRequest.DoesNotExist:
      return {"code": "Invalid code."}

    ar.status = 'complete'
    ar.save()

    user = self.user
    user.set_password(password)
    user.save()

    return True

  def change_password(self, old, new):
    if authenticate(username=self.user.username, password=old) is None:
      return {"password": "Invalid password."}

    user = self.user
    user.set_password(new)
    user.save()

    return True

  def update_account(self, schema):
    fields = set(['first_name', 'last_name'])
    update_fields = {}
    for field in fields:
      try:
        update_fields[field] = schema[field]
      except KeyError:
        pass

    update_record(self, update_fields)

    return True

class AccountRequest(models.Model):
  account = models.ForeignKey(Account)
  type = models.CharField(max_length=50)
  code = models.CharField(max_length=32)
  status = models.CharField(max_length=20)
  request = models.CharField(max_length=255, blank=True)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)

  statuses = ['pending', 'complete', 'expired']

  @classmethod
  def create_unique_code(cls):
    while True:
      code = uuid.uuid1().hex
      try:
        cls.objects.get(code=code)
      except cls.DoesNotExist:
        break
    return code

class AccountEmail(models.Model):
  account = models.ForeignKey(Account)
  sender = models.EmailField(max_length=255)
  recipient = models.EmailField(max_length=255)
  subject = models.CharField(max_length=255)
  status = models.CharField(max_length=20)
  html = models.TextField()
  text = models.TextField()
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)

  ###
  #
  enabled = True
  #
  ###
  
  statuses = ['pending', 'sent', 'opened']

  @classmethod
  def create_and_send(cls, account, action, request=None):
    email = cls.create_email(account, action, request=request)
    if isinstance(email, AccountEmail) and cls.enabled is True:
      email.send()
    return email

  @classmethod
  def create_email(cls, account, action, request=None):
    sender = settings.SMTP['username']

    if action == 'account-created' and request is not None:
      recipient = account.email
      subject = "Verify your email address"

    elif action == 'invitation-account-created' and request is not None:
      recipient = account.email
      subject = "Invitation to share a project"

    elif action == 'email-change-requested':
      recipient = account.email
      subject = "Verify your updated email address"

    elif action == 'password-reset-requested':
      recipient = account.email
      subject = "Reset your password"

    else:
      return False
    
    context = dict(context, **{
      "url": settings.BASE_URL,
      "subject": subject,
      "site_name": settings.SITE_NAME,
      "code": request.code,
      "account_id": account.id,
    })
    
    html = render_to_string(action + '.html', context)
    text = render_to_string(action + '.txt', context)

    email = cls(
      account=account,
      sender=sender,
      recipient=recipient,
      subject=subject,
      html=html,
      text=text,
      status=cls.statuses[0],
    )
    email.save()
    return email

  def send(self):
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import smtplib
    # From: http://stackoverflow.com/questions/882712/sending-html-email-in-python

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = self.subject
    msg['From'] = self.sender
    msg['To'] = self.recipient

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(self.text, 'plain')
    part2 = MIMEText(self.html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    try:
      s = smtplib.SMTP(settings.SMTP['host'], settings.SMTP['port'])
    except smtplib.SMTPConnectError:
      return False
    
    s.login(settings.SMTP['username'], settings.SMTP['password'])

    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    try:
      s.sendmail(sender, recipient, msg.as_string())
    except (smtplib.SMTPRecipientsRefused, smtplib.SMTPHeloError, smtplib.SMTPSenderRefused, smtplib.SMTPDataError):
      pass
    else:
      self.status = 'sent'
      self.save()

    s.quit()

