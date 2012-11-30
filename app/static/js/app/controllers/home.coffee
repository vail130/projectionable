class Projectionable.Home extends Spine.Controller
  constructor: ->
    super
    @routes
      '/home': =>
        App.navigation.render()
        @render().active()
  
  className: 'home'
  
  render: =>
    @html @view 'home_home'
    $('#home').append @$el
    @

