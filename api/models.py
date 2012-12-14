from django.db import models
from django.contrib.auth.models import User
from utilities import *
from django.conf import settings
from django.db.models import Sum
from django.template.loader import render_to_string
from django.contrib.auth import authenticate
import copy, json, datetime, math, time, re, uuid, stripe

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
      "unix_updated": time.mktime(self.date_updated.timetuple()),
      "unix_created": time.mktime(self.date_created.timetuple()),
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

    elif cls.email_exists(email):
      return {"email": "Email address is already in use."}

    elif re.search('^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', email, re.I) is None:
      return {"email": "Invalid email address."}

    elif password == '':
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
    
    code = AccountRequest.create_unique_code()

    AccountRequest.create_record({
      "account": account,
      "type": 'create-account',
      "hash": bcrypt.hashpw(code, bcrypt.gensalt(12)),
      "request": email
    })

    AccountEmail.create_and_send({
      "recipient": account.email,
      "subject": "Verify your email address",
      "template": "account-created",
      "context": {
        "account_id": account.user_id,
        "code": code,
      }
    })
    
    return account

  @classmethod
  def create_invitation_account(cls, email):
    email = email.strip().lower()

    if email == '':
      return {"email": "Email address must not be empty."}

    elif cls.email_exists(email):
      return {"email": "Email address is already in use."}

    elif re.search('^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', email, re.I) is None:
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

    code = AccountRequest.create_unique_code()

    AccountRequest.create_record({
      "account": account,
      "type": 'create-invitation-account',
      "hash": bcrypt.hashpw(code, bcrypt.gensalt(12)),
      "request": email
    })

    AccountEmail.create_and_send({
      "recipient": account.email,
      "subject": "Verify your invitation",
      "template": "invitation-account-created",
      "context": {
        "account_id": account.user_id,
        "code": code,
      }
    })
    
    return account

  @classmethod
  def request_password_reset(cls, email):
    try:
      account = Account.objects.get(email=email)
    except Account.DoesNotExist:
      return {"email": "Invalid email address."}
    
    code = AccountRequest.create_unique_code()
    
    AccountRequest.create_record({
      "account": account,
      "type": 'request-password-reset',
      "hash": bcrypt.hashpw(code, bcrypt.gensalt(12)),
      "request": email
    })

    AccountEmail.create_and_send({
      "recipient": account.email,
      "subject": "Set a new password",
      "template": "password-reset-requested",
      "context": {
        "account_id": account.user_id,
        "code": code,
      }
    })
    
    return True

  def verify_email(self, code):
    try:
      ar = AccountRequest.objects.get(account=self, status='pending', type__in=['create-account', 'request-email-change'])
    except AccountRequest.DoesNotExist:
      return {"code": "Invalid code."}

    if bcrypt.hashpw(code, ar.hash) != ar.hash:
      return {"code": "Invalid code."}

    ar.status = 'complete'
    ar.save()

    self.status = 'active'

    if ar.type == 'request-email-change':
      self.email = ar.request

    self.save()

    return True

  def verify_invitation(self, code, password):
    try:
      ar = AccountRequest.objects.get(account=self, code=code, type='create-invitation-account', status='pending')
    except AccountRequest.DoesNotExist:
      print self.id, code
      return {"code": "Invalid code."}

    if bcrypt.hashpw(code, ar.hash) != ar.hash:
      return {"code": "Invalid code."}
    
    password = str(password)
    if password == '':
      return {"password": "Invalid password."}

    ar.status = 'complete'
    ar.save()

    self.status = 'active'
    self.save()

    user = self.user
    user.set_password(password)
    user.save()

    return True

  def verify_password_reset(self, code, password):
    try:
      ar = AccountRequest.objects.get(account=self, status='pending', type='request-password-reset')
    except AccountRequest.DoesNotExist:
      return {"code": "Invalid code."}
    
    if bcrypt.hashpw(code, ar.hash) != ar.hash:
      return {"code": "Invalid code."}
    
    password = str(password)
    if password == '':
      return {"password": "Invalid password."}

    ar.status = 'complete'
    ar.save()

    user = self.user
    user.set_password(password)
    user.save()

    return True

  def update_record(self, data):
    changed = False
    
    if 'first_name' in data and self.first_name != data['first_name']:
      self.first_name = data['first_name']
      changed = True
    
    if 'last_name' in data and self.last_name != data['last_name']:
      self.last_name = data['last_name']
      changed = True
    
    if 'password' in data and not self.user.check_password(str(data['password'])):
      self.user.set_password(str(data['password']))
      changed = True
    
    if changed:
      self.save()
    
    if 'email' in data and str(data['email']).lower() != self.email:
      email = str(data['email']).lower()
      if email == '':
        return {"email": "Email address must not be empty."}
  
      if Account.email_exists(email):
        return {"email": "Email address is already in use."}
  
      if re.search('^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', email, re.I) is None:
        return {"email": "Invalid email address."}
      
      code = AccountRequest.create_unique_code()
      
      AccountRequest.create_record({
        "account": account,
        "type": 'request-email-change',
        "hash": bcrypt.hashpw(code, bcrypt.gensalt(12)),
        "request": email
      })
  
      AccountEmail.create_and_send({
        "recipient": self.email,
        "subject": "Verify your new email address",
        "template": "email-change-requested",
        "context": {
          "account_id": self.id,
          "code": code,
        }
      })
    
    return True

class AccountRequest(models.Model):
  account = models.ForeignKey(Account)
  type = models.CharField(max_length=50)
  hash = models.CharField(max_length=32)
  status = models.CharField(max_length=20)
  request = models.CharField(max_length=255, blank=True)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)

  statuses = ['pending', 'complete', 'expired']
  types = ['create-account', 'create-invitation-account', 'request-password-reset', 'request-email-change']
  
  validation = {
    "account": 'model',
    "type": lambda x: x in AccountRequest.types,
    "hash": 'string',
    "status": lambda x: x in AccountRequest.statuses,
    "request": 'string'
  }
  
  @classmethod
  def create_unique_code(cls):
    return uuid.uuid1().hex + str(time.mktime(datetime.datetime.now().timetuple()))
  
  @classmethod
  def create_record(cls, raw_data):
    data = shim_schema(raw_data)
    ar = cls(
      account=data['account'],
      type=data['type'],
      hash=data['hash'],
      status='pending',
      request=data['request']
    )
    ar.save()
    return ar

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
      "unix_updated": time.mktime(self.date_updated.timetuple()),
      "unix_created": time.mktime(self.date_created.timetuple()),
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
      "unix_updated": time.mktime(self.date_updated.timetuple()),
      "unix_created": time.mktime(self.date_created.timetuple()),
    }
  
  def update_record(self, plan):
    if plan not in self.__class__.plans:
      return {"plan": "Invalid plan."}
    
    if self.plan != plan:
      self.plan = plan
      self.save()
      
      # Set it up with Stripe
    
    return self


class Project(models.Model):
  account = models.ForeignKey(Account)
  title = models.CharField(max_length=100)
  deadline = models.DateTimeField(blank=True)
  rate = models.PositiveIntegerField(blank=True)
  budget = models.PositiveIntegerField(blank=True)
  status = models.CharField(max_length=20)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  statuses = ['open', 'locked']
  
  validation = {
    'title': ('string', (0, 100)),
    'rate': ('integer', (0, None)),
    'budget': ('integer', (0, None)),
    'deadline': 'string',
    'status': lambda x: x in Project.statuses,
  }
  
  @classmethod
  def get_dummy_schema(cls):
    return {
      'title': '',
      "status": '',
      'rate': 0,
      'budget': 0,
      'deadline': '',
    }
  
  @classmethod
  def create_record(cls, account, raw_schema):
    schema = shim_schema(cls, raw_schema)
    
    project_dict = {
      "account": account,
      "title": schema['title'],
      "status": cls.statuses[0]
    }
    
    for field in ['rate', 'deadline', 'budget']:
      if field in schema:
        project_dict[field] = schema[field]
        
    project = cls(**project_dict)
    project.save()
    perm = Permission.create_record(account, project, account, {"permission": "owner"})
    
    return project
  
  def read_record(self, permission):
    req_hours_data = {}
    for field_type in ['front-end', 'back-end']:
      for field in ['hours', 'hours_worked']:
        req_hours_data['_'.join(field_type.split('-')) + '_' + field] = 0
        try:
          result = Requirement.objects.filter(group__project=self, group__type=field_type).aggregate(Sum(field))
        except Requirement.DoesNotExist:
          pass
        else:
          if result[field + "__sum"] is not None:
            req_hours_data['_'.join(field_type.split('-')) + '_' + field] = float(result[field + "__sum"])
    
    asset_hours_data = {}
    for field in ['hours', 'hours_worked']:
      asset_hours_data[field] = 0
      try:
        result = ProjectAsset.objects.filter(project=self).aggregate(Sum(field))
      except ProjectAsset.DoesNotExist:
        pass
      else:
        if result[field + "__sum"] is not None:
          asset_hours_data[field] = float(result[field + "__sum"])
    
    return {
      "id": self.id,
      "account_id": self.account.id,
      "title": self.title,
      "rate": self.rate,
      "budget": self.budget,
      "deadline": self.deadline,
      "status": self.status,
      "front_end_hours": req_hours_data['front_end_hours'],
      "front_end_hours_worked": req_hours_data['front_end_hours_worked'],
      "back_end_hours": req_hours_data['back_end_hours'],
      "back_end_hours_worked": req_hours_data['back_end_hours_worked'],
      "asset_hours": asset_hours_data['hours'],
      "asset_hours_worked": asset_hours_data['hours_worked'],
      "date_updated": self.date_updated,
      "date_created": self.date_created,
      "unix_updated": time.mktime(self.date_updated.timetuple()),
      "unix_created": time.mktime(self.date_created.timetuple()),
    }
  
  def update_record(self, permission, raw_schema):
    if permission.permission != 'owner':
      return {"permission": "Invalid permissions."}
    
    schema = filter_valid(self.__class__, raw_schema)
    changed = False
    
    for prop in ['title', 'rate', 'budget', 'deadline']:
      if prop in schema and getattr(self, prop) != schema[prop]:
        setattr(self, prop, schema[prop])
        changed = True
    
    if 'status' in schema and self.status != schema['status'] and schema['status'] in self.__class__.statuses:
      self.status = schema['status']
      changed = True
        
    if changed:
      self.save()
      
    return self
    
  def delete_record(self, permission):
    if permission.permission != 'owner':
      return {"permission": "Invalid permissions."}
    
    try:
      Permission.objects.filter(project=self).delete()
    except Permission.DoesNotExist:
      pass
    
    self.delete()
    return True

class RequirementGroup(models.Model):
  project = models.ForeignKey(Project)
  title = models.TextField()
  uri = models.CharField(max_length=255)
  index = models.PositiveIntegerField()
  type = models.CharField(max_length=20)
  method = models.CharField(max_length=20)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  types = ['front_end', 'back_end']
  methods = ['get', 'post', 'put', 'delete', 'head', 'options']
  
  validation = {
    'uri': ('string', (0, 200)),
    'title': ('string', (0, 200)),
    'type': lambda x: x in RequirementGroup.types,
    'index': ('integer', (0, None)),
    'method': lambda x: str(x).lower() in RequirementGroup.methods,
  }
  
  @staticmethod
  def get_dummy_schema():
    return {
      "title": '',
      "uri": '',
      "index": 0,
      "type": '',
      "method": '',
    }
  
  @classmethod
  def create_record(cls, permission, project, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permissions."}
    
    if permission.permission != 'owner' and project.status == 'locked':
      return {"project": "Project is locked."}
    
    schema = shim_schema(cls, raw_schema)
    
    record_dict = {
      "project": project,
      "title": schema['title'],
      "uri": schema['uri'],
      "type": schema['type'],
      "index": schema['index'],
      "method": schema['method'],
    }
    
    record = cls(**record_dict)
    record.save()
    return record
  
  def read_record(self):
    hours_data = {}
    for field in ['hours', 'hours_worked']:
      hours_data[field] = 0
      try:
        result = Requirement.objects.filter(group=self).aggregate(Sum(field))
      except Requirement.DoesNotExist:
        pass
      else:
        if result[field + "__sum"] is not None:
          hours_data[field] = result[field + "__sum"]
    
    return {
      "id": self.id,
      "account_id": self.project.account.id,
      "project_id": self.project.id,
      "index": self.index,
      "title": self.title,
      "method": self.method,
      "uri": self.uri,
      "type": self.type,
      "hours": hours_data['hours'],
      "hours_worked": hours_data['hours_worked'],
      "date_updated": self.date_updated,
      "date_created": self.date_created,
      "unix_updated": time.mktime(self.date_updated.timetuple()),
      "unix_created": time.mktime(self.date_created.timetuple()),
    }
  
  def update_record(self, permission, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and self.project.status == 'locked':
      return {"permission": "Invalid permission."}
    
    schema = filter_valid(self.__class__, raw_schema)
    changed = False
    
    for prop in ['title', 'index', 'method', 'uri']:
      if prop in schema and getattr(self, prop) != schema[prop]:
        setattr(self, prop, schema[prop])
        changed = True
    
    if changed:
      self.save()
      
    return self
  
  def delete_record(self, permission):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and self.project.status == 'locked':
      return {"permission": "Invalid permission."}
    
    self.delete()
    return self

class Requirement(models.Model):
  group = models.ForeignKey(RequirementGroup)
  title = models.TextField()
  index = models.PositiveIntegerField()
  status = models.CharField(max_length=20)
  hours = models.FloatField(null=True, blank=True)
  hours_worked = models.FloatField()
  requester = models.ForeignKey(Account, blank=True)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  statuses = ['pending', 'working', 'completed', 'approved', 'rejected']
  
  validation = {
    'title': 'string',
    'index': ('integer', (0, None)),
    'status': lambda x: x in Requirement.statuses,
    'hours': ('float', (0, None)),
    'hours_worked': ('float', (0, None)),
  }
  
  @staticmethod
  def get_dummy_schema():
    return {
      "title": '',
      "index": 0,
      "status": '',
      "hours": None,
      "hours_worked": 0,
    }
  
  @classmethod
  def create_record(cls, permission, group, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and group.project.status == 'locked':
      return {"project": "Project is locked."}
    
    schema = shim_schema(cls, raw_schema)
    
    requester = None
    if 'requester_id' in raw_schema:
      try:
        perm = Permission.objects.get(account_id=int(raw_schema['requester_id']), project=group.project)
      except Permission.DoesNotExist:
        pass
      else:
        requester = perm.account
    
    record = cls(
      group=group,
      title=schema['title'],
      index=schema['index'],
      status=cls.statuses[0],
      hours=schema['hours'],
      hours_worked=0,
      requester=requester,
    )
    
    record.save()
    return record
    
  def read_record(self):
    if self.requester is None:
      requester_id = None
    else:
      requester_id = self.requester.id
    
    return {
      "id": self.id,
      "account_id": self.group.project.account.id,
      "project_id": self.group.project.id,
      "group_id": self.group.id,
      "index": self.index,
      "title": self.title,
      "status": self.status,
      "requester_id": requester_id,
      "hours": self.hours,
      "hours_worked": self.hours_worked,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
      "unix_updated": time.mktime(self.date_updated.timetuple()),
      "unix_created": time.mktime(self.date_created.timetuple()),
    }
  
  def update_record(self, permission, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if self.group.project.status == 'locked' and permission.permission != 'owner':
      return {"permission": "Invalid permission."}
    
    schema = filter_valid(self.__class__, raw_schema)
    changed = False
    
    if 'requester_id' in schema and self.requester.id != schema['requester_id']:
      try:
        perm = Permission.objects.get(account_id=int(schema['requester_id']), project=self.group.project)
      except Permission.DoesNotExist:
        pass
      else:
        self.requester = perm.account
        changed = True
    
    # If status is in schema AND different
    if 'status' in schema and self.status != schema['status']:
      status_changed = True
      
      # Starting
      if schema['status'] == 'working':
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "start",
        })
      
      # Stopping
      if self.status == 'working':
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "stop",
        })
        
        self.hours_worked = self.calculate_hours_worked()
      
      # Completing
      if self.status in ['pending', 'working'] and schema['status'] == 'completed':
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "complete",
        })
        
        self.hours_worked = self.calculate_hours_worked()
        
        if self.requester is not None:
          if self.type == 'front-end':
            subject = "Front-End Story Completed"
          else:
            subject = "Back-End Story Completed"
          
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": self.requester.email,
            "subject": subject,
            "template": "requirement-completed",
            "context": {
              "full_name": full_name,
              "requirement_type": self.type,
              "requirement_title": self.title,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
      
      # Approving
      if schema['status'] == 'approved':
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "approve",
        })
        
        try:
          log = WorkLog.objects.filter(requirement=self, action='completed').order_by('-date_updated').reverse()[0]
        except WorkLog.DoesNotExist:
          pass
        else:
          if self.type == 'front-end':
            subject = "Front-End Story Approved"
          else:
            subject = "Back-End Story Approved"
          
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": log.account.email,
            "subject": subject,
            "template": "requirement-approved",
            "context": {
              "full_name": full_name,
              "requirement_type": self.type,
              "requirement_title": self.title,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
      
      # Rejecting
      elif schema['status'] == 'rejected':
        if 'note' in raw_schema:
          log_note = raw_schema['note']
        else:
          log_note = None
        
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "reject",
          "note": log_note
        })
        
        try:
          log = WorkLog.objects.filter(requirement=self, action='completed').order_by('-date_updated').reverse()[0]
        except WorkLog.DoesNotExist:
          pass
        else:
          if self.type == 'front-end':
            subject = "Front-End Story Rejected"
          else:
            subject = "Back-End Story Rejected"
          
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": log.account.email,
            "subject": subject,
            "template": "requirement-rejected",
            "context": {
              "full_name": full_name,
              "requirement_type": self.type,
              "requirement_title": self.title,
              "note": log_note,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
      
      # Reverting
      if self.status in ['approved', 'rejected', 'completed'] and schema['status'] in ['pending', 'working']:
        if 'note' in raw_schema:
          log_note = raw_schema['note']
        else:
          log_note = None
        
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "revert",
          "note": log_note
        })
        
        if self.requester is not None and self.requester.id != permission.account.id:
          if self.type == 'front-end':
            subject = "Front-End Story Reverted"
          else:
            subject = "Back-End Story Reverted"
          
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": self.requester.email,
            "subject": subject,
            "template": "requirement-reverted",
            "context": {
              "full_name": full_name,
              "requirement_type": self.type,
              "requirement_title": self.title,
              "note": log_note,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
        
      else:
        status_changed = False
      
      if status_changed is True:
        self.status = schema['status']
        changed = True
  
    for prop in ['title', 'index', 'hours']:
      if prop in schema and getattr(self, prop) != schema[prop]:
        setattr(self, prop, schema[prop])
        changed = True
    
    if changed:
      self.save()
    
    return self
  
  def calculate_hours_worked(self):
    hours_worked = 0
    try:
      logs = list(WorkLog.objects.filter(requirement=self, action__in=['start', 'stop']).order_by('-date_created'))
    except WorkLog.DoesNotExist:
      return hours_worked
    else:
      num_logs = len(logs)
      for i in range(num_logs):
        if logs[i].action == 'start' and i < num_logs - 1 and logs[i+1].action == 'stop':
          hours_worked += (logs[i+1].date_created - logs[i].date_created).seconds / 3600.0
      return hours_worked
  
  def delete_record(self, permission):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and self.group.project.status == 'locked':
      return {"permission": "Invalid permission."}
    
    if self.hours_worked > 0:
      self.status = 'deleted'
      self.save()
    else:
      self.delete()
    
    return True

class ProjectAsset(models.Model):
  project = models.ForeignKey(RequirementGroup)
  title = models.TextField()
  index = models.PositiveIntegerField()
  status = models.CharField(max_length=20)
  asset = models.FileField(upload_to='/', blank=True)
  content_type = models.CharField(max_length=64, blank=True)
  hours = models.FloatField(null=True, blank=True)
  hours_worked = models.FloatField()
  requester = models.ForeignKey(Account, blank=True)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  statuses = ['pending', 'working', 'completed', 'approved', 'rejected']
  
  validation = {
    'title': 'string',
    'index': ('integer', (0, None)),
    'status': lambda x: x in ProjectAsset.statuses,
    'hours': ('float', (0, None)),
    'hours_worked': ('float', (0, None)),
  }
  
  @staticmethod
  def get_dummy_schema():
    return {
      "title": '',
      "index": 0,
      "status": '',
      "hours": None,
      "hours_worked": 0,
    }
  
  @classmethod
  def create_record(cls, permission, project, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and project.status == 'locked':
      return {"project": "Project is locked."}
    
    schema = shim_schema(cls, raw_schema)
    
    requester = None
    if 'requester_id' in raw_schema:
      try:
        perm = Permission.objects.get(account_id=int(raw_schema['requester_id']), project=project)
      except Permission.DoesNotExist:
        pass
      else:
        requester = perm.account
    
    record = cls(
      project=project,
      title=schema['title'],
      index=schema['index'],
      status=cls.statuses[0],
      hours=schema['hours'],
      hours_worked=0,
      requester=requester,
    )
    
    record.save()
    return record
    
  def read_record(self):
    if self.requester is None:
      requester_id = None
    else:
      requester_id = self.requester.id
    
    return {
      "id": self.id,
      "account_id": self.project.account.id,
      "project_id": self.project.id,
      "index": self.index,
      "title": self.title,
      "asset_url": self.asset.url,
      "file_size": self.asset.size,
      "content_type": self.content_type,
      "status": self.status,
      "requester_id": requester_id,
      "hours": self.hours,
      "hours_worked": self.hours_worked,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
      "unix_updated": time.mktime(self.date_updated.timetuple()),
      "unix_created": time.mktime(self.date_created.timetuple()),
    }
  
  def update_record(self, permission, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if self.project.status == 'locked' and permission.permission != 'owner':
      return {"permission": "Invalid permission."}
    
    schema = filter_valid(self.__class__, raw_schema)
    changed = False
    
    if 'requester_id' in schema and self.requester.id != schema['requester_id']:
      try:
        perm = Permission.objects.get(account_id=int(schema['requester_id']), project=self.project)
      except Permission.DoesNotExist:
        pass
      else:
        self.requester = perm.account
        changed = True
    
    # If status is in schema AND different
    if 'status' in schema and self.status != schema['status']:
      status_changed = True
      
      # Starting
      if schema['status'] == 'working':
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "start",
        })
      
      # Stopping
      if self.status == 'working':
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "stop",
        })
        
        self.hours_worked = self.calculate_hours_worked()
      
      # Completing
      if self.status in ['pending', 'working'] and schema['status'] == 'completed':
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "complete",
        })
        
        self.hours_worked = self.calculate_hours_worked()
        
        if self.requester is not None:
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": self.requester.email,
            "subject": "Project Asset Completed",
            "template": "requirement-completed",
            "context": {
              "full_name": full_name,
              "requirement_type": "project asset",
              "requirement_title": self.title,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
      
      # Approving
      if schema['status'] == 'approved':
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "approve",
        })
        
        try:
          log = WorkLog.objects.filter(asset=self, action='completed').order_by('-date_updated').reverse()[0]
        except WorkLog.DoesNotExist:
          pass
        else:
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": log.account.email,
            "subject": "Project Asset Approved",
            "template": "requirement-approved",
            "context": {
              "full_name": full_name,
              "requirement_type": "project asset",
              "requirement_title": self.title,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
      
      # Rejecting
      elif schema['status'] == 'rejected':
        if 'note' in raw_schema:
          log_note = raw_schema['note']
        else:
          log_note = None
        
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "reject",
          "note": log_note
        })
        
        try:
          log = WorkLog.objects.filter(asset=self, action='completed').order_by('-date_updated').reverse()[0]
        except WorkLog.DoesNotExist:
          pass
        else:
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": log.account.email,
            "subject": "Project Asset Rejected",
            "template": "requirement-rejected",
            "context": {
              "full_name": full_name,
              "requirement_type": "project asset",
              "requirement_title": self.title,
              "note": log_note,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
      
      # Reverting
      if self.status in ['approved', 'rejected', 'completed'] and schema['status'] in ['pending', 'working']:
        if 'note' in raw_schema:
          log_note = raw_schema['note']
        else:
          log_note = None
        
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "revert",
          "note": log_note
        })
        
        if self.requester is not None and self.requester.id != permission.account.id:
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": self.requester.email,
            "subject": "Project Asset Reverted",
            "template": "requirement-reverted",
            "context": {
              "full_name": full_name,
              "requirement_type": "project asset",
              "requirement_title": self.title,
              "note": log_note,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
        
      else:
        status_changed = False
      
      if status_changed is True:
        self.status = schema['status']
        changed = True
  
    for prop in ['title', 'index', 'hours']:
      if prop in schema and getattr(self, prop) != schema[prop]:
        setattr(self, prop, schema[prop])
        changed = True
    
    if changed:
      self.save()
    
    return self
  
  def calculate_hours_worked(self):
    hours_worked = 0
    try:
      logs = list(WorkLog.objects.filter(asset=self, action__in=['start', 'stop']).order_by('-date_created'))
    except WorkLog.DoesNotExist:
      return hours_worked
    else:
      num_logs = len(logs)
      for i in range(num_logs):
        if logs[i].action == 'start' and i < num_logs - 1 and logs[i+1].action == 'stop':
          hours_worked += (logs[i+1].date_created - logs[i].date_created).seconds / 3600.0
      return hours_worked
  
  def delete_record(self, permission):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and self.project.status == 'locked':
      return {"permission": "Invalid permission."}
    
    if self.hours_worked > 0:
      self.status = 'deleted'
      self.save()
    else:
      self.delete()
    
    return True
  
  def update_asset(self, files):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if self.project.status == 'locked' and permission.permission != 'owner':
      return {"permission": "Invalid permission."}
    
    if 'asset' not in dict(files):
      return {"asset": "Missing asset."}

    elif len(files) is not 1:
      return {"asset": "Only one asset can be uploaded at once."}

    asset = files['asset']
    if not hasattr(asset, 'content_type'):
      return {"asset": "Invalid asset content-type."}

    # Get uploaded file data
    for chunk in asset.chunks():
      data = chunk

    data_size = len(data)

    # Make sure file attachment is there
    if data_size is 0:
      return {"asset": "No content found."}
    elif data_size > 2097152*16:
      return {"asset": "Asset size must be under 32MB."}

    self.asset = asset
    self.content_type = asset.content_type
    self.save()
    return self

class ProjectFile(models.Model):
  project = models.ForeignKey(RequirementGroup)
  title = models.TextField()
  index = models.PositiveIntegerField()
  asset = models.FileField(upload_to='/', blank=True)
  content_type = models.CharField(max_length=64, blank=True)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  validation = {
    'title': 'string',
    'index': ('integer', (0, None)),
  }
  
  @staticmethod
  def get_dummy_schema():
    return {
      "title": '',
      "index": 0,
    }
  
  @classmethod
  def create_record(cls, permission, project, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and project.status == 'locked':
      return {"project": "Project is locked."}
    
    schema = shim_schema(cls, raw_schema)
    
    record = cls(
      project=project,
      title=schema['title'],
      index=schema['index'],
    )
    
    record.save()
    return record
    
  def read_record(self):
    return {
      "id": self.id,
      "account_id": self.project.account.id,
      "project_id": self.project.id,
      "index": self.index,
      "title": self.title,
      "asset_url": self.asset.url,
      "file_size": self.asset.size,
      "content_type": self.content_type,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
      "unix_updated": time.mktime(self.date_updated.timetuple()),
      "unix_created": time.mktime(self.date_created.timetuple()),
    }
  
  def update_record(self, permission, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if self.project.status == 'locked' and permission.permission != 'owner':
      return {"permission": "Invalid permission."}
    
    schema = filter_valid(self.__class__, raw_schema)
    changed = False
    
    for prop in ['title', 'index']:
      if prop in schema and getattr(self, prop) != schema[prop]:
        setattr(self, prop, schema[prop])
        changed = True
    
    if changed:
      self.save()
    
    return self
  
  def delete_record(self, permission):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and self.project.status == 'locked':
      return {"permission": "Invalid permission."}
    
    self.delete()
    return True
  
  def update_asset(self, files):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if self.project.status == 'locked' and permission.permission != 'owner':
      return {"permission": "Invalid permission."}
    
    if 'asset' not in dict(files):
      return {"asset": "Missing asset."}

    elif len(files) is not 1:
      return {"asset": "Only one asset can be uploaded at once."}

    asset = files['asset']
    if not hasattr(asset, 'content_type'):
      return {"asset": "Invalid asset content-type."}

    # Get uploaded file data
    for chunk in asset.chunks():
      data = chunk

    data_size = len(data)

    # Make sure file attachment is there
    if data_size is 0:
      return {"asset": "No content found."}
    elif data_size > 2097152*16:
      return {"asset": "Asset size must be under 32MB."}

    self.asset = asset
    self.content_type = asset.content_type
    self.save()
    return self

class Permission(models.Model):
  account = models.ForeignKey(Account)
  project = models.ForeignKey(Project, related_name='permissions')
  permission = models.CharField(max_length=20)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  permissions = ['client', 'coworker', 'owner']
  
  validation = {
    'permission': lambda x: x in Permission.permissions,
  }
  
  @classmethod
  def get_dummy_schema(cls):
    return {
      'permission': cls.permissions[0],
    }
  
  @classmethod
  def create_record(cls, account, project, p_account, raw_schema):
    schema = shim_schema(cls, raw_schema)
    record = cls(
      account=p_account,
      project=project,
      permission=schema['permission']
    )
    record.save()
    return record
  
  def update_record(self, account, raw_schema):
    schema = shim_schema(self.__class__, raw_schema)
    
    # Only project owner can change permissions
    if self.project.account.id is not account.id or schema['permission'] not in Permission.permissions[:1]:
      return self
    
    self.permission = schema['permission']
    self.save()
    return self
  
  def read_record(self):
    return {
      "id" : self.id,
      "account_id": self.account.user_id,
      "email": self.account.email,
      "project_id": self.project.id,
      "permission": self.permission,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
      "unix_updated": time.mktime(self.date_updated.timetuple()),
      "unix_created": time.mktime(self.date_created.timetuple()),
    }

  def delete_record(self, account):
    # Owner cannot remove self from account permissions, unless project is deleted
    if self.project.account.id is self.account.id:
      return {"permission": "Invalid permissions."}
    
    self.delete()
    return True

class WorkLog(models.Model):
  account = models.ForeignKey(Account)
  asset = models.ForeignKey(ProjectAsset, blank=True)
  requirement = models.ForeignKey(Requirement, blank=True)
  action = models.CharField(max_length=20)
  note = models.TextField(blank=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  actions = ['start', 'stop', 'complete', 'approve', 'reject', 'revert']
  
  @classmethod
  def create_record(cls, schema):
    log_dict = {
      "account": schema['account'],
      "action": schema['action']
    }
    
    for prop in ['requirement', 'asset', 'note']:
      if prop in schema:
        log_dict[prop] = schema[prop]
    
    record = cls(**log_dict)
    record.save()
    return record
  
  def read_record(self):
    record_dict = {
      "account_id": self.account.id,
      "action": self.action,
      "note": self.note,
      "date_created": self.date_created,
      "unix_created": time.mktime(self.date_created.timetuple()),
    }
    
    if self.asset is not None:
      record_dict['asset_id'] = self.asset.id
    
    if self.requirement is not None:
      record_dict['requirement_id'] = self.requirement.id
    
    return record_dict

