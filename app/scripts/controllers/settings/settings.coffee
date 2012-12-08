define [
  'jquery'
  'underscore'
  'spine'
  'text!views/settings/settings.html'
  'controllers/settings/credentials'
  'controllers/settings/terminate'
], ($, _, Spine, settingsTemplate, Credentials, Terminate) ->
  
  class Settings extends Spine.Controller
    constructor: ->
      super
      @routes
        '/settings': => @navigate '/settings/credentials'
        '/settings/:page': (params) =>
          App.navigation.render()
          @render(params.page).active()
    
    className: 'settings main-stack'
    
    elements:
      '.settings-wrapper' : '$wrapper'
      '.settings-tabs' : '$tabs'
      '.settings-content' : '$content'
    
    getContext: =>
      {}
    
    render: (page='credentials') =>
      context = @getContext()
      @html _.template settingsTemplate, context
      $('#app-body').append @$el
      
      @lock = new App.Lock el: @$wrapper
      @lock.start()
      
      $.when(App.accountPromise).done =>
        @renderChildren(page).lock.stop().remove()
        
      @
      
    renderChildren: (page) =>
      @children =
        credentials: new Credentials(parent: @)
        terminate: new Terminate(parent: @)
        
      _.each @children, (child) =>
        @$content.append child.render().el
        
      if not @children.hasOwnProperty page
        @navigate '/settings/credentials'
      else
        @children[page].activate()
        @$tabs.find("a.#{page}-link").addClass('active')
        setTimeout (=>
            $el = @children[page].$el.find('input').first()
            $el.get(0).focus() if $el.length > 0
          ), 1
      
      @
  
