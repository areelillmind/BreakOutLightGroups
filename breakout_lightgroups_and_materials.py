import nuke
import re
import nukescripts

def divide_b_by_a(input_nodes, x_pos, y_pos):
    divide_node=nuke.nodes.MergeExpression(channel0 = 'rgb', channel1 = 'rgb', channel2 = 'rgb', expr0 = 'Ar>0?Br>0?Br/Ar:0:0', expr1 = 'Ag>0?Bg>0?Bg/Ag:0:0', expr2 = 'Ab>0?Bb>0?Bb/Ab:0:0', label = 'divide B by A', inputs = input_nodes)
    divide_node.setXYpos(x_pos, y_pos)
    return divide_node

def get_layers(node):
    '''returns a list of all the layers '''
    channels = node.channels()
    layers = list( set([c.split('.')[0] for c in channels]) )
    layers.sort()
    return layers

def get_aov_minicomp_settings():
    '''Customize lightgroup naming conventions used'''
    settings={}
    p = nuke.Panel('Lighrgroup Shuffle out settings')
    p.addSingleLineInput('lightgroup flags (comma separated)', 'LGT')
    p.addSingleLineInput('material flags (comma separated)', 'M_')
    p.addBooleanCheckBox('show shuffle postage stamps', False)
    p.addSingleLineInput('x_space', '300')
    p.addSingleLineInput('y_space', '150')
    ret = p.show()
    lg_flags = p.value('lightgroup flags (comma separated)')
    lg_flags = re.sub(' ', '', lg_flags)
    settings['lightgroup_flags'] = lg_flags.split(',')
    mat_flags = p.value('material flags (comma separated)')
    mat_flags = re.sub(' ', '', mat_flags)
    settings['mat_flags'] = mat_flags.split(',')
    settings['pstamps'] = p.value('show shuffle postage stamps')
    settings['x_space'] = p.value('x_space')
    settings['y_space'] = p.value('y_space')
    return settings



def get_lightgroups(node, lg_flags ):
    '''Returns a list of aovs which are lightgroups (based on naming convention flags set in LightGroupLabels list) ''' 
    
    light_group_layers=[]
    for aov in get_layers(node):
    
        for flag in lg_flags:
            if flag in aov and aov not in light_group_layers:
                light_group_layers.append(aov)
    light_group_layers.sort()
    return light_group_layers
    

def get_materials(node, mat_flags) :
    '''Returns a list of aovs which are materials (based on naming convention flags set in Material Labels list) '''
    material_layers =[]
    for aov in get_layers(node):
    
        for flag in mat_flags:
            if flag in aov and aov not in material_layers:
                material_layers.append(aov)
    material_layers.sort()
    return material_layers

def deselect_all_nodes():
    for n in nuke.selectedNodes():
        n['selected'].setValue(False)

#print get_lightgroups(nuke.selectedNode(),['_ASS_', '_L_', 'lights', 'Lights'] )
        
def shuffle_out_aovs (node, lightgroups = True , materials = False ):
    settings = get_aov_minicomp_settings()
    main_b_pipe = [node]
    x_pos, y_pos=int(node.xpos()), int(node.ypos())
    x_space, y_space = int(settings['x_space']), int(settings['y_space'])
    y_pos+=y_space
    b_pipe_root=nuke.nodes.NoOp(label = 'beauty', inputs=[node])
    b_pipe_root.setXYpos(node.xpos(), y_pos)
    y_pos+=y_space
    unpremult_all=nuke.nodes.Unpremult(channels='all', inputs=[b_pipe_root])
    unpremult_all.setXYpos(node.xpos(), y_pos)
    main_b_pipe.append(unpremult_all)
    original_dot = nuke.nodes.Dot(inputs = [b_pipe_root])
    original_dot.setXYpos(b_pipe_root.xpos()-int(x_space), b_pipe_root.ypos() )
    original_dots = [ original_dot ]
    if lightgroups == True :
        node = shuffle_out_lightgroups(main_b_pipe[-1], x_pos + x_space, y_pos, settings)
        
    if materials == True :
        node = shuffle_out_materials(main_b_pipe[-1])
    

    y_pos = node.ypos() + y_space
    dot = nuke.nodes.Dot(inputs = [ original_dots[-1] ] )
    original_dots.append( dot)
    original_dots[-1].setXYpos(original_dot.xpos(), y_pos )
    unpremult=nuke.nodes.Unpremult(inputs = [ original_dots[-1]])
    unpremult.setXYpos(original_dots[-1].xpos()+int(x_space/2), original_dots[-1].ypos() )
    divide_node = divide_b_by_a ( [ main_b_pipe[-1], unpremult], x_pos, y_pos)
    main_b_pipe.append(divide_node)
    y_pos = y_pos + y_space
    merge_multiply = nuke.nodes.Merge(inputs = [ main_b_pipe[-1], node], operation = 'multiply', output = 'rgb')
    merge_multiply.setXYpos(main_b_pipe[-1].xpos(), y_pos )
    main_b_pipe.append(merge_multiply)
    y_pos = y_pos + y_space


    dot = nuke.nodes.Dot(inputs = [ original_dots[-1] ] )
    original_dots.append( dot)

    y_pos+=y_space
    premult = nuke.nodes.Premult(inputs = [main_b_pipe[-1]] )
    premult.setXYpos(b_pipe_root.xpos(), y_pos)

def shuffle_out_lightgroups(node, x_pos, y_pos, settings ):
    '''This will create a mini comp from the layers flagged as lightgroups in the user defined settings. Flags, spacing and use of postage stamps can be set in the panel as per the lightgroup_minicomp_settings function() '''
    x_space, y_space = int(settings['x_space']), int(settings['y_space'])
    y_pos+=y_space
    index_no =0
    loop_b_pipe_x = node.xpos() + x_space
    loop_top_node=nuke.nodes.NoOp(label = 'beauty', inputs=[node] )
    loop_top_node.setXYpos(loop_b_pipe_x, node.ypos() )
    b_pipe_nodes=[loop_top_node] #all the merge_plus nodes will be added to this list
    top_dots = [loop_top_node]
    light_groups = get_lightgroups(node, settings['lightgroup_flags'])
    for lg in light_groups:
        deselect_all_nodes()
        selected=[]
        x_pos +=x_space
        y_pos +=y_space

        dot=nuke.nodes.Dot( inputs=[ top_dots [index_no] ] )
        top_dots.append(dot)
        dot.setXpos (x_pos)
        dot.setYpos(node.ypos())
        shuffle_node = nuke.nodes.Shuffle2( label=lg, inputs=[top_dots[index_no+1]] )
        shuffle_node['in1'].setValue( lg )
        shuffle_node['in2'].setValue( 'alpha')
        shuffle_node['mappings'].setValue([('rgba.alpha','rgba.alpha')])
        shuffle_node['postage_stamp'].setValue( settings['pstamps'])
        shuffle_node.setYpos(dot.ypos()+ 100)
        tempDot=nuke.nodes.Dot( ) #defines corner of backdrop
        tempDot.setXpos(x_pos+int(x_space/2))
        tempDot.setYpos(shuffle_node.ypos()+ y_space*3)
        y_pos +=y_space
        bottom_corner = nuke.nodes.Dot( inputs=[ shuffle_node ], tile_color='536805631.0', label = '<i>'+lg )
        y_pos +=int(y_space/2)
        bottom_corner.setXYpos(x_pos, y_pos )
        merge_plus = nuke.nodes.Merge2 (operation ='plus', label = '<i>'+lg, tile_color='536805631.0', inputs=[ b_pipe_nodes[index_no], bottom_corner ], output = 'rgb' )
        b_pipe_nodes.append( merge_plus )
        merge_plus.setXYpos(loop_b_pipe_x, y_pos)
        for n in [dot, shuffle_node, tempDot]:
            n['selected'].setValue(True)
        bg = nukescripts.autoBackdrop()
        bg['label'].setValue(lg)
        nuke.delete(tempDot)

        index_no +=1
        final_x_pos = x_pos + x_space
    y_pos +=y_space
    # pipe for unnasigned lights.
    unassigned_light_dot = nuke.nodes.Dot( inputs = [top_dots[-1]], label = '<i> unassigned lights' )
    unassigned_light_pipe = [unassigned_light_dot]
    unassigned_light_dot.setXpos (final_x_pos)
    unassigned_y_pos = dot.ypos()
    unassigned_light_dot.setYpos(unassigned_y_pos)
    index_no = 0
    for lg in light_groups:
        
        merge_from=nuke.nodes.Merge2 (operation ='from', tile_color='4278190335.0', label = '<i>'+lg, inputs=[ unassigned_light_pipe[index_no], unassigned_light_pipe[index_no] ], Achannels=lg, output = 'rgb' )
        unassigned_y_pos += int ( merge_from.screenHeight() + merge_from.screenHeight() / 5)
        merge_from.setXYpos(final_x_pos, unassigned_y_pos)
        unassigned_light_pipe.append(merge_from)
        index_no +=1
    tempDot=nuke.nodes.Dot( ) #defines corner of backdrop
    tempDot.setXpos(final_x_pos+int(x_space/2))
    tempDot.setYpos(unassigned_light_pipe[1].ypos()+ y_space*3)

    deselect_all_nodes()
    tempDot['selected'].setValue(True)
    for n in unassigned_light_pipe:
        n['selected'].setValue(True)

    bg = nukescripts.autoBackdrop()
    bg['label'].setValue('unassigned lights')
    nuke.delete(tempDot)
    bottom_corner = nuke.nodes.Dot( tile_color='536805631.0', label = '<i> unassigned lights', inputs = [ unassigned_light_pipe[-1] ]  )
    bottom_corner.setXYpos(final_x_pos, y_pos )
    merge_plus = nuke.nodes.Merge2 (operation ='plus', label = '<i> unassigned lights', tile_color='536805631.0', inputs=[ b_pipe_nodes[index_no], bottom_corner ], disable = True)
    merge_plus.setXYpos(b_pipe_nodes[-1].xpos(), y_pos)
    b_pipe_nodes.append( merge_plus )
    return b_pipe_nodes[-1]



        


def shuffle_out_materials(node, source_cg, settings):
    '''This will create a mini comp from the layers flagged as materials in the user defined settings. Flags, spacing and use of postage stamps can be set in the panel as per the lightgroup_minicomp_settings function() '''

    xPos, yPos=int(node.xpos() + node.screenWidth()/2 ), int(node.ypos() + node.screenHeight()/2)
    x_space, y_space = int(settings['x_space']), int(settings['y_space'])
    yPos+=y_space
    b_pipe_root=nuke.nodes.NoOp(label = 'beauty', inputs=[node])
    b_pipe_root.setXYpos(node.xpos(), yPos)
    yPos+=y_space
    divide_node=divide_b_by_a()
    divide_node.setXYpos(node.xpos(), yPos)
    yPos+=y_space


    index_no =0
    bPipeNodes=[divide_node] #all the merge nodes will be added to this list
    topDots = [divide_node]
    
    
    divide_node.setXYpos(node.xpos(), yPos)
    divide_node.setInput(0, b_pipe_root)
    

    yPos+=y_space
    yPos+=y_space
    unpremult_all=nuke.nodes.Unpremult(channels='all', inputs=[source_cg])
    unpremult_all.setXYpos(node.xpos(), yPos)
    yPos+=y_space
    
    for mat in get_materials(node, settings['mat_flags']):
        deselect_all_nodes()
        selected=[]
        xPos +=x_space
        yPos +=y_space

        dot=nuke.nodes.Dot( inputs=[ topDots [index_no] ] )
        topDots.append(dot)
        dot.setXpos (xPos)
        dot.setYpos(unpremult_all.ypos())
        shuffleNode = nuke.nodes.Shuffle2( label=mat, inputs=[topDots[index_no+1]] )
        shuffleNode['in1'].setValue( mat )
        shuffleNode['postage_stamp'].setValue( settings['pstamps'])
        shuffleNode.setYpos(dot.ypos()+ 100)
        tempDot=nuke.nodes.Dot( ) #defines corner of backdrop
        tempDot.setXpos(xPos+int(x_space/2))
        tempDot.setYpos(shuffleNode.ypos()+ y_space*3)
        yPos +=y_space
        fromNode=nuke.nodes.Merge2 (operation ='from', output = 'rgb', tile_color='4278190335.0', label = '<i>'+mat, inputs=[ bPipeNodes[index_no], bPipeNodes[index_no] ], Achannels=mat)
        fromNode.setXYpos(node.xpos(), yPos )
        bottomCorner = nuke.nodes.Dot( inputs=[ shuffleNode ], tile_color='536805631.0', label = '<i>'+mat )
        yPos +=int(y_space/2)
        bottomCorner.setXYpos(xPos, yPos )
        merge = nuke.nodes.Merge2 (operation ='plus', output = 'rgb', label = '<i>'+mat, tile_color='536805631.0', inputs=[ fromNode, bottomCorner ])
        bPipeNodes.append( merge )
        merge.setXYpos(node.xpos(), yPos)
        for n in [dot, shuffleNode, tempDot]:
            n['selected'].setValue(True)
        bg = nukescripts.autoBackdrop()
        bg['label'].setValue(mat)
        nuke.delete(tempDot)

        index_no +=1

