import nuke

toolbar = nuke.menu('Nodes')
toolbar.addCommand('Color/GradeAlbedo','nuke.createNode("GradeAlbedo")')
toolbar.addCommand('Color/GradeLight','nuke.createNode("GradeLight")')