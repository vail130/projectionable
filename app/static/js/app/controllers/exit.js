// Generated by CoffeeScript 1.3.3
(function() {
  var __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  Projectionable.Exit = (function(_super) {

    __extends(Exit, _super);

    function Exit() {
      var _this = this;
      Exit.__super__.constructor.apply(this, arguments);
      this.routes({
        '/exit': function() {
          return $.ajax({
            type: 'DELETE',
            dataType: 'json',
            contentType: 'application/json',
            url: '/api/sessions',
            complete: function() {
              return window.location.href = 'http://' + window.location.host;
            }
          });
        }
      });
    }

    return Exit;

  })(Spine.Controller);

}).call(this);
