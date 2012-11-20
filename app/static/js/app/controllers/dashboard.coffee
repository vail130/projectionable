class Projectionable.Dashboard extends Spine.Controller
  constructor: ->
    super
    
    App.Dashboard = @
    
    @routes
      '/dashboard': =>
        @render().active()
        App.trigger 'renderNavigation', 'dashboard'
        @lock = new App.Lock el: $('#dashboard')
        @lock.start()
        $.when(App.accountPromise).done => @lock.stop().remove()
  
  className: 'dashboard'
  
  elements:
    '.account-list': '$accountList'
    
  addOne: (account) =>
    controller = new DashboardAccount
      parent: @
      account: account
    @$accountList.append controller.render().el

  addAll: =>
    @$accountList.empty()
    accounts = Projectionable.Account.all()
    if accounts.length > 0
      @addOne account for account in accounts
    else
      @$accountList.html @view 'dashboard_dashboard-no-previews'
    @
    
  render: ->
    @html @view 'dashboard_dashboard'
    $('#dashboard').html @$el
    @addAll()
    @

class DashboardAccount extends Spine.Controller
  constructor: ->
    super
  
  tag: 'li'
  className: 'account-wrapper clearfix'
  
  getContext: =>
    account: @account
  
  render: =>
    @html @view('dashboard_dashboard-preview')(@getContext())
    @
