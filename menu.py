import nuke

toolbar = nuke.menu('Nodes')
toolbar.addCommand('Color/GradeAlbedo','nuke.createNode("GradeAlbedo")')
toolbar.addCommand('Color/GradeLight','nuke.createNode("GradeLight")')
toolbar.addCommand('Channel/Breakout AOVs','breakout_lightgroups_and_materials.create_minicomp(nuke.selectedNode())')
