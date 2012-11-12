class Projectionable.Manager extends Spine.Controller
  constructor: ->
    super
    
    App.Manager = @
    $('#work').html @view 'work_work-structure'
    
    Project.bind 'create', @addOne
    Project.bind 'refresh change', @addAll
    @routes
      '/manager': =>
        App.project = null
        App.trigger 'renderNavigation', 'manager'
        @render().active()
        @lock = new App.Lock el: $('#work')
        @lock.start()
        $.when(App.projectPromise).done => @lock.stop().remove()
  
  className: 'work-manager'
  
  elements:
    '.manager-projects': '$projectList'
    
  events:
    'click .new-project-button' : 'new'
    
  new: (event) ->
    event.preventDefault()
    project = Project.create App.makeProjectTemplate()
    @addOne project
  
  addOne: (project) =>
    controller = new ProjectPreview project: project
    @$projectList.append controller.render().el

  addAll: =>
    @$projectList.empty()
    projects = Project.all()
    if projects.length > 0
      @addOne project for project in projects
    else
      @$projectList.html @view 'work_manager_manager-no-previews'
    @
    
  render: ->
    @html @view 'work_manager_manager'
    $('#work-manager').html @$el
    @addAll()
    @

class ProjectPreview extends Spine.Controller
  constructor: ->
    super
    @project.bind 'update', @render
    @project.bind 'destroy', @release
      
  tag: 'li'
  className: 'project-wrapper clearfix'
    
  events:
    'click a.edit-link' : 'editProject'
    'click a.delete' : 'remove'
    'mousedown' : 'pressPreview'
    'mouseup' : 'unpressPreview'
    'mouseout' : 'unpressPreview'
    'click' : 'processClick'
    
  pressPreview: (event) =>
    $target = $(event.target)
    if not $target.hasClass('options-button') and not $target.parent().hasClass('options-button')
      @$el.addClass 'pressed'
  
  unpressPreview: => @$el.removeClass 'pressed'
  
  processClick: (event) =>
    $target = $(event.target)
    if not $target.hasClass('options-button') and not $target.parent().hasClass('options-button')
      event.preventDefault() if $target.hasClass 'title'
      App.project = @project
      @navigate '/editor'
    
  editProject: (event) =>
    event.preventDefault()
    App.project = @project
    @navigate '/editor'
    
  preventDefault: (event) ->
    event.preventDefault()
    
  remove: (event) ->
    event.preventDefault()
    event.stopPropagation()
    @project.destroy()
    @release()
    App.project = null

  render: =>
    @html(@view('work_manager_manager-preview')(project: @project))
    @


