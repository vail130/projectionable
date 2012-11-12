class Projectionable.Exit extends Spine.Controller
  constructor: ->
    super
    @routes
      '/exit': =>
        $.ajax
          type: 'DELETE'
          dataType: 'json'
          contentType: 'application/json'
          url: '/api/sessions'
          complete: ->
            window.location.href = 'http://' + window.location.host
  
  