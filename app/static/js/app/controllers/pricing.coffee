class Projectionable.Pricing extends Spine.Controller
  constructor: ->
    super
    @routes
      '/pricing': =>
        App.navigation.render()
        @render().active()
  
  className: 'pricing'
  
  render: =>
    @html @view 'pricing_pricing'
    $('#pricing').append @$el
    @

