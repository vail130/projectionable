// Generated by CoffeeScript 1.3.3
(function() {
  var __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  Projectionable.Stack = (function(_super) {

    __extends(Stack, _super);

    function Stack() {
      Stack.__super__.constructor.apply(this, arguments);
    }

    Stack.prototype.controllers = {
      Manager: Projectionable.Manager,
      Dashboard: Projectionable.Dashboard,
      Editor: Projectionable.Editor,
      Settings: Projectionable.Settings,
      Exit: Projectionable.Exit
    };

    return Stack;

  })(Spine.Stack);

}).call(this);
