class Projectionable.Stack extends Spine.Stack

  constructor: ->
    super
  
  controllers:
    Manager: Projectionable.Manager
    Dashboard: Projectionable.Dashboard
    Editor: Projectionable.Editor
    Settings: Projectionable.Settings
    Exit: Projectionable.Exit
  
