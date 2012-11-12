class window.Projectionable extends Spine.Controller
  constructor: ->
    super
    window.App = @
    
    @html @view 'structure'
    @Lock = Lock
    @navigation = new Navigation
    @footer = new Footer
    @project = null
    
    @bind 'renderNavigation', (page) =>
      @navigation.render(page)
    
    projectDeferred = $.Deferred()
    Project.one 'refresh', => projectDeferred.resolve()
    @projectPromise = projectDeferred.promise()
    
    accountDeferred = $.Deferred()
    Account.one 'refresh', => accountDeferred.resolve()
    @accountPromise = accountDeferred.promise()
    
    Account.fetch()
    Project.fetch()
    Permission.fetch()
    RequirementGroup.fetch()
    Requirement.fetch()
    
    @stack = new Projectionable.Stack
    Spine.Route.setup()
    
    hash = window.location.hash
    if hash.substr(0, 2) isnt '#/' or hash.split('/')[1] not in ['manager', 'editor', 'settings', 'exit']
      @navigate '/manager'
    
  makeProjectTemplate: ->
    title: ""
    rate: ""
    hours: ""
    hours_worked: ""
    date_updated: ""
    date_created: ""
    
  makePermissionTemplate: (email, project_id) ->
    email: email
    project_id: project_id
    
  makeGroupTemplate: (pid, idx=0) ->
    project_id: pid
    title: ""
    status: ""
    index: idx
    hours: ""
    hours_worked: ""
    date_updated: ""
    date_created: ""
    
  makeRequirementTemplate: (gid, idx=0) ->
    project_id: ""
    group_id: gid
    title: ""
    status: ""
    index: idx
    hours: ""
    hours_worked: ""
    date_updated: ""
    date_created: ""
   
  formatNumber: (number) ->
    return '' if typeof(number) is 'undefined'
    
    parts = number.toString().split '.'
    decimal = parts[1] || ''
    number = parts[0]
    
    negative = false
    if number.substr(0, 1) is '-'
      negative = true
      number = number.substr(1)
    
    number = number.replace /[^0-9]/ig, ''
    decimal = decimal.replace /[^0-9]/ig, ''
    output = ''
    while number.length > 0
      output = ',' + output if output.length > 0
      
      if number.length > 3
        output = number.substr(-3, 3) + output
        number = number.substr(0, number.length - 3)
      else
        output = number + output
        number = ''
    
    output =  '-'+output if negative
    output += '.'+decimal if decimal.length > 0
    output

class Lock extends Spine.Controller
  constructor: ->
    super
    @$lock = $('<div></div>').css(
      display: 'none'
      position: 'absolute'
      top: 0
      left: 0
      width: '100%'
      height: '100%'
      'background-color': 'white'
      opacity: .5
      filter: 'alpha(opacity=50)'
      'z-index': 999999999999999999
    )
    @$el.append @$lock
    @state = 'stopped'

  start: =>
    @initialPosition = @$el.css('position')
    if @initialPosition not in ['absolute', 'fixed']
      @$el.css 'position', 'relative'
    
    @$lock.show()
    @spinner = new Spinner(
      lines: 13
      length: 15
      width: 4
      radius: 18
      color: '#222'
      trail: 60
      shadow: true
    ).spin(@$lock.get(0))
    @$lock.children('.spinner').css
      top: '50%'
      left: '50%'
    @state = 'started'
    @
  
  stop: =>
    @spinner.stop()
    @$lock.hide()
    @$el.css 'position', @initialPosition
    @initialPosition = null
    @state = 'stopped'
    @
  
  remove: =>
    @stop() if @state is 'started'
    @$lock.remove()
    @

class Navigation extends Spine.Controller
  constructor: ->
    @el = $('#navigation')
    super
    @render('manager')
    
  render: (page) =>
    context =
      page: if typeof(page) is 'undefined' then 'manager' else page
    @html(@view('navigation')(context))
    @
  
class Footer extends Spine.Controller
  constructor: ->
    @el = $('#footer')
    super
    @render()
    
  render: =>
    @html @view 'footer'
    @
  
$ ->
  new Projectionable el: $('#projectionable')