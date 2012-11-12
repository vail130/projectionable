class Projectionable.Stack extends Spine.Stack

  constructor: ->
    super
  
  controllers:
    Manager: Projectionable.Manager
    Editor: Projectionable.Editor
    Settings: Projectionable.Settings
    Exit: Projectionable.Exit
  
