// Generated by CoffeeScript 1.3.3
(function() {
  var Credentials, Terminate,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  Projectionable.Settings = (function(_super) {

    __extends(Settings, _super);

    function Settings() {
      this.renderChildren = __bind(this.renderChildren, this);

      this.render = __bind(this.render, this);

      this.getContext = __bind(this.getContext, this);

      var _this = this;
      Settings.__super__.constructor.apply(this, arguments);
      this.routes({
        '/settings': function() {
          return _this.navigate('/settings/credentials');
        },
        '/settings/:page': function(params) {
          App.navigation.render();
          return _this.render(params.page).active();
        }
      });
    }

    Settings.prototype.className = 'settings';

    Settings.prototype.elements = {
      '.settings-wrapper': '$wrapper',
      '.settings-tabs': '$tabs',
      '.settings-content': '$content'
    };

    Settings.prototype.getContext = function() {
      return {};
    };

    Settings.prototype.render = function(page) {
      var context,
        _this = this;
      if (page == null) {
        page = 'credentials';
      }
      context = this.getContext();
      this.html(this.view('settings_settings')(context));
      $('#settings').html(this.$el);
      this.lock = new App.Lock({
        el: this.$wrapper
      });
      this.lock.start();
      $.when(App.accountPromise).done(function() {
        return _this.renderChildren(page).lock.stop().remove();
      });
      return this;
    };

    Settings.prototype.renderChildren = function(page) {
      var _this = this;
      this.children = {
        credentials: new Credentials({
          parent: this
        }),
        terminate: new Terminate({
          parent: this
        })
      };
      _.each(this.children, function(child) {
        return _this.$content.append(child.render().el);
      });
      if (!this.children.hasOwnProperty(page)) {
        this.navigate('/settings/credentials');
      } else {
        this.children[page].activate();
        this.$tabs.find("a." + page + "-link").addClass('active');
        setTimeout((function() {
          var $el;
          $el = _this.children[page].$el.find('input').first();
          if ($el.length > 0) {
            return $el.get(0).focus();
          }
        }), 1);
      }
      return this;
    };

    return Settings;

  })(Spine.Controller);

  Credentials = (function(_super) {

    __extends(Credentials, _super);

    function Credentials() {
      this.render = __bind(this.render, this);

      this.getContext = __bind(this.getContext, this);

      this.updateAccount = __bind(this.updateAccount, this);

      this.submitNewPassword = __bind(this.submitNewPassword, this);

      this.updateNewPasswordButtonStatus = __bind(this.updateNewPasswordButtonStatus, this);

      this.submitNewEmail = __bind(this.submitNewEmail, this);

      this.updateNewEmailButtonStatus = __bind(this.updateNewEmailButtonStatus, this);
      Credentials.__super__.constructor.apply(this, arguments);
    }

    Credentials.prototype.className = 'credentials';

    Credentials.prototype.elements = {
      '.new-email-message': '$newEmailMessage',
      '.new-email-input': '$newEmailInput',
      '.new-email-password-input': '$newEmailPasswordInput',
      '.new-email-button': '$newEmailButton',
      '.new-password-message': '$newPasswordMessage',
      '.new-password-current-input': '$newPasswordCurrentInput',
      '.new-password-new-input': '$newPasswordNewInput',
      '.new-password-verify-input': '$newPasswordVerifyInput',
      '.new-password-button': '$newPasswordButton'
    };

    Credentials.prototype.events = {
      'keyup .new-email-input': 'updateNewEmailButtonStatus',
      'keyup .new-email-password-input': 'updateNewEmailButtonStatus',
      'click .new-email-button': 'submitNewEmail',
      'keyup .new-password-current-input': 'updateNewPasswordButtonStatus',
      'keyup .new-password-new-input': 'updateNewPasswordButtonStatus',
      'keyup .new-password-verify-input': 'updateNewPasswordButtonStatus',
      'click .new-password-button': 'submitNewPassword'
    };

    Credentials.prototype.updateNewEmailButtonStatus = function(event) {
      var code;
      code = event.keyCode ? event.keyCode : event.charCode;
      if (code === 13) {
        return this.$newEmailButton.trigger('click');
      } else if ('' === $.trim(this.$newEmailInput.val()) || '' === this.$newEmailPasswordInput.val()) {
        return this.$newEmailButton.addClass('disabled');
      } else {
        return this.$newEmailButton.removeClass('disabled');
      }
    };

    Credentials.prototype.submitNewEmail = function(event) {
      var email, password, payload;
      event.preventDefault();
      if (this.$newEmailButton.hasClass('disabled')) {
        return;
      }
      this.$newEmailMessage.hide().text('').removeClass('alert-error alert-success');
      email = $.trim(this.$newEmailInput.val());
      password = this.$newEmailPasswordInput.val();
      if (email.search(/^.+@.+\..+$/) === -1) {
        this.$newEmailMessage.addClass('alert-error').text('Invalid email address').show();
        this.$newEmailInput.get(0).focus();
        this.$newEmailButton.addClass('disabled');
        return;
      }
      payload = {
        action: 'change_email',
        password: password,
        email: email
      };
      return this.updateAccount(payload);
    };

    Credentials.prototype.updateNewPasswordButtonStatus = function(event) {
      var code;
      code = event.keyCode ? event.keyCode : event.charCode;
      if (code === 13) {
        return this.$newPasswordButton.trigger('click');
      } else if ('' === this.$newPasswordCurrentInput.val() || '' === this.$newPasswordNewInput.val() || '' === this.$newPasswordVerifyInput.val()) {
        return this.$newPasswordButton.addClass('disabled');
      } else {
        return this.$newPasswordButton.removeClass('disabled');
      }
    };

    Credentials.prototype.submitNewPassword = function(event) {
      var current, newPass, payload, verify;
      event.preventDefault();
      if (this.$newPasswordButton.hasClass('disabled')) {
        return;
      }
      this.$newPasswordMessage.hide().text('').removeClass('alert-error alert-success');
      current = this.$newPasswordCurrentInput.val();
      newPass = this.$newPasswordNewInput.val();
      verify = this.$newPasswordVerifyInput.val();
      if (newPass !== verify) {
        this.$newPasswordMessage.addClass('alert-error').text('Mismatching passwords').show();
        this.$newPasswordNewInput.get(0).focus();
        this.$newPasswordButton.addClass('disabled');
        return;
      }
      this.$newPasswordButton.button('loading');
      payload = {
        action: 'change_password',
        old_password: current,
        new_password: newPass
      };
      return this.updateAccount(payload);
    };

    Credentials.prototype.updateAccount = function(payload) {
      var $button, $fields, $message, successText,
        _this = this;
      switch (payload.action) {
        case 'change_email':
          $message = this.$newEmailMessage;
          successText = 'Please check your email to confirm your new address.';
          $fields = this.$newEmailInput.add(this.$newEmailPasswordInput);
          $button = this.$newEmailButton;
          break;
        case 'change_password':
          $message = this.$newPasswordMessage;
          successText = 'Your password has been changed successfully.';
          $fields = this.$newPasswordCurrentInput.add(this.$newPasswordNewInput).add(this.$newPasswordVerifyInput);
          $button = this.$newPasswordButton;
      }
      this.lock = new App.Lock({
        el: this.parent.$wrapper
      });
      this.lock.start();
      $.ajax({
        url: '/api/accounts/' + Projectionable.Account.findByAttribute('id', window.sessionID),
        type: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(payload),
        success: function() {
          $message.addClass('alert-success').text(successText).show();
          return $fields.each(function() {
            return this.value = '';
          });
        },
        error: function(jqXHR) {
          var response;
          response = JSON.parse(jqXHR.responseText);
          return $message.addClass('alert-error').text(response[_.keys(response)[0]]).show();
        },
        complete: function() {
          _this.lock.stop().remove();
          return $button.button('reset').addClass('disabled');
        }
      });
      return this;
    };

    Credentials.prototype.getContext = function() {
      return {
        account: Projectionable.Account.findByAttribute('id', window.sessionID)
      };
    };

    Credentials.prototype.render = function() {
      this.html(this.view('settings_settings-credentials')(this.getContext()));
      this.$newEmailMessage.add(this.$newPasswordMessage).hide();
      return this;
    };

    return Credentials;

  })(Spine.Controller);

  Terminate = (function(_super) {

    __extends(Terminate, _super);

    function Terminate() {
      this.render = __bind(this.render, this);

      this.getContext = __bind(this.getContext, this);

      this.submitTermination = __bind(this.submitTermination, this);

      this.updateTerminateButtonStatus = __bind(this.updateTerminateButtonStatus, this);
      Terminate.__super__.constructor.apply(this, arguments);
    }

    Terminate.prototype.className = 'terminate';

    Terminate.prototype.elements = {
      '.terminate-message': '$terminateMessage',
      '.terminate-password-input': '$terminatePasswordInput',
      '.terminate-button': '$terminateButton'
    };

    Terminate.prototype.events = {
      'keyup .terminate-password-input': 'updateTerminateButtonStatus',
      'click .terminate-button': 'submitTermination'
    };

    Terminate.prototype.updateTerminateButtonStatus = function(event) {
      var code;
      code = event.keyCode ? event.keyCode : event.charCode;
      if (code === 13) {
        return this.$terminateButton.trigger('click');
      } else if ('' === this.$terminatePasswordInput.val()) {
        return this.$terminateButton.addClass('disabled');
      } else {
        return this.$terminateButton.removeClass('disabled');
      }
    };

    Terminate.prototype.submitTermination = function(event) {
      var password,
        _this = this;
      event.preventDefault();
      if (this.$terminateButton.hasClass('disabled')) {
        return;
      }
      this.$terminateMessage.hide().text('').removeClass('alert-error alert-success');
      password = this.$terminatePasswordInput.val();
      this.lock = new App.Lock({
        el: this.parent.$wrapper
      });
      this.lock.start();
      $.ajax({
        url: '/api/accounts/' + Projectionable.Account.findByAttribute('id', window.sessionID) + '?password=' + password,
        type: 'DELETE',
        success: function() {
          $message.addClass('alert-success').text('Your account was successfully delete...').show();
          _this.$terminatePasswordInput.val('');
          return setTimeout((function() {
            return _this.navigate('/exit');
          }), 1000);
        },
        error: function(jqXHR) {
          var response;
          response = JSON.parse(jqXHR.responseText);
          _this.$terminatePasswordInput.val('').get(0).focus();
          return _this.$terminateMessage.addClass('alert-error').text(response[_.keys(response)[0]]).show();
        },
        complete: function() {
          _this.lock.stop().remove();
          return _this.$terminateButton.button('reset').addClass('disabled');
        }
      });
      return this;
    };

    Terminate.prototype.getContext = function() {
      return {};
    };

    Terminate.prototype.render = function() {
      this.html(this.view('settings_settings-terminate')(this.getContext()));
      return this;
    };

    return Terminate;

  })(Spine.Controller);

  /*
  
  class Notifications extends Spine.Controller
    constructor: ->
      super
      
    className: 'notifications'
    
    getContext: =>
      account: Projectionable.Account.findByAttribute('id', window.sessionID)
    
    render: =>
      @html(@view('settings_settings-notifications')(@getContext()))
      @
  
  class Payments extends Spine.Controller
    constructor: ->
      super
      
    className: 'payments'
    
    getContext: =>
      {}
    
    render: =>
      @html(@view('settings_settings-payments')(@getContext()))
      @
  */


}).call(this);
