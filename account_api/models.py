from django.db import models
from django.contrib.auth.models import User
from utilities import *
from django.contrib.auth import authenticate
from django.conf import settings
import re, uuid, stripe
from django.template.loader import render_to_string

class Account(models.Model):
  user = models.OneToOneField(User, related_name='account', primary_key=True)
  first_name = models.CharField(max_length=50)
  last_name = models.CharField(max_length=50)
  email = models.EmailField(max_length=128)
  type = models.CharField(max_length=20)
  status = models.CharField(max_length=20)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)

  statuses = ['pending', 'active', 'terminated']
  types = ['user', 'administrator']
  
  def read_record(self):
    return {
      "id": self.user_id,
      "first_name": self.first_name,
      "last_name": self.last_name,
      "email": self.email,
      "type": self.type,
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
  def create_account(cls, email, password, code=None):
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
    
    if code is not None and code in settings.ADMIN_CODES:
      type = settings.ADMIN_CODES[code]
    else:
      type = 'user'

    account = cls(
      user=user,
      email=email,
      first_name='',
      last_name='',
      status='pending',
      type=type,
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

    AccountEmail.create_and_send({
      "recipient": account.email,
      "subject": "Verify your email address",
      "template": "account-created",
      "context": {
        "account_id": account.user_id,
        "code": ar.code,
      }
    })
    
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

    AccountEmail.create_and_send({
      "recipient": account.email,
      "subject": "Verify your invitation",
      "template": "invitation-account-created",
      "context": {
        "account_id": account.user_id,
        "code": ar.code,
      }
    })
    
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

    AccountEmail.create_and_send({
      "recipient": self.email,
      "subject": "Verify your email address",
      "template": "email-change-requested",
      "context": {
        "account_id": self.id,
        "code": ar.code,
      }
    })
    
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

    AccountEmail.create_and_send({
      "recipient": account.email,
      "subject": "Set a new password",
      "template": "password-reset-requested",
      "context": {
        "account_id": account.user_id,
        "code": ar.code,
      }
    })
    
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
  account = models.ForeignKey(Account, blank=True)
  sender = models.EmailField(max_length=255)
  recipient = models.EmailField(max_length=255)
  subject = models.CharField(max_length=255)
  status = models.CharField(max_length=20)
  html = models.TextField()
  text = models.TextField()
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)

  statuses = ['pending', 'sent']
  
  @classmethod
  def create_and_send(cls, data_dict):
    email = cls.create_email(data_dict)
    if isinstance(email, AccountEmail) and settings.ENVIRONMENT != 'local':
      email.send()
    return email

  @classmethod
  def create_email(cls, data_dict):
    sender = settings.EMAIL_HOST_USER

    context = dict({
      "url": settings.BASE_URL,
      "subject": data_dict['subject'],
      "site_name": settings.SITE_NAME,
    }, **data_dict['context'])
    
    html = render_to_string(data_dict['template'] + '.html', context)
    text = render_to_string(data_dict['template'] + '.txt', context)
    
    email_dictionary = {
      "sender": sender,
      "recipient": data_dict['recipient'],
      "subject": data_dict['subject'],
      "html": html,
      "text": text,
    }
    
    if 'account' in data_dict:
      email_dictionary['account'] = data_dict['account']

    email = cls(**email_dictionary)
    email.save()
    return email

  def send(self):
    from django.core.mail import EmailMultiAlternatives

    subject, from_email, to = self.subject, "Projectionable <" + str(self.sender) + ">", self.recipient
    text_content = self.text
    html_content = self.html
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")

    try:
      msg.send()
    except Exception:
      pass
    else:
      self.status = 'sent'
      self.save()
      
    return self

class Contact(models.Model):
  account = models.ForeignKey(Account, blank=True)
  reply_to = models.EmailField(max_length=255)
  subject = models.CharField(max_length=255)
  message = models.TextField()
  status = models.CharField(max_length=20)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  statuses = ['pending', 'complete', 'archived']
  
  def read_record(self):
    if self.account is None:
      account_id = None
    else:
      account_id = self.account.user_id
      
    return {
      "id": self.id,
      "account_id": account_id,
      "reply_to": self.reply_to,
      "subject": self.subject,
      "message": self.message,
      "status": self.status,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
    }
  
  def update_record(self, schema):
    if 'status' in schema and self.status != schema['status']:
      cls = self.__class__
      if schema['status'] in cls.statuses and cls.statuses.index(schema['status']) > 0:
        self.status = schema['status']
        self.save()
    
    return self
  
  @classmethod
  def create_record(cls, account, schema):
    contact_dictionary = {
      "status": "pending",
    }
    
    if 'reply_to' not in schema or schema['reply_to'] is None:
      return {"reply_to": "Missing reply_to field."}
    
    contact_dictionary["reply_to"] = str(schema['reply_to'])
    
    if re.search('^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', contact_dictionary["reply_to"], re.I) is None:
      return {"reply_to": "Invalid reply_to address."}

    if 'subject' not in schema or schema['subject'] is None:
      return {"subject": "Missing subject field."}
    
    contact_dictionary["subject"] = str(schema['subject'])
    
    if 'message' not in schema or schema['message'] is None:
      return {"message": "Missing message field."}
    
    contact_dictionary["message"] = str(schema['message'])
    
    if account is not None:
      contact_dictionary["account"] = account
    
    contact = cls(**contact_dictionary)
    contact.save()
    
    AccountEmail.create_and_send(contact, 'contact-created')
    AccountEmail.create_and_send({
      "account": contact.account,
      "recipient": contact.reply_to,
      "subject": "Receipt of your contact",
      "template": "contact-created",
      "context": {
        "reply_to": contact.reply_to,
        "subject": contact.subject,
        "message": contact.message,
      }
    })
    
    return contact

class Subscription(models.Model):
  account = models.ForeignKey(Account)
  customer_id = models.CharField(max_length=100)
  subscription_id = models.CharField(max_length=100)
  plan = models.CharField(max_length=20)
  status = models.CharField(max_length=20)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  plans = ['startup', 'freelancer', 'agency']
  statuses = ['paid', 'unpaid']
  
  @classmethod
  def create_record(cls, account, plan, stripe_token):
    if plan not in cls.plans:
      return {"plan": "Invalid plan."}
    
    # Set it up with Stripe
    customer = stripe.Customer.create(
      card=stripe_token,
      plan=plan,
      email=account.email
    )
    
    record = cls(
      account=account,
      plan=plan,
      customer_id=customer['id']
    )
    record.save()
    
    return record
  
  def read_record(self):
    return {
      "account_id": self.account.user_id,
      "plan": self.plan,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
    }
  
  def update_record(self, plan):
    if plan not in self.__class__.plans:
      return {"plan": "Invalid plan."}
    
    if self.plan != plan:
      self.plan = plan
      self.save()
      
      # Set it up with Stripe
    
    return self
