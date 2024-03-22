'''
Module to create minicomps from CG renders, can split by lightgroups, materials or both. Uses default flags expected in the aov naming but these can be user defined.
'''
import nuke
import re
import nukescripts
import logging

logging.basicConfig(level=logging.DEBUG)

## default beahviours
LIGHTGROUP_FLAGS = 'C_'
#LIGHTGROUP_REJECT_FLAGS = ''
MATERIAL_FLAGS = 'M_'
#MATERIAL_REJECT_FLAGS = '_direct, _indirect'
SHOW_POSTAGE_STAMPS = False
BREAKOUT_MATERIALS = True
BREAKOUT_LIGHTGROUPS = True
X_SPACE = '300'
Y_SPACE = '150'
TILE_COLOURS_LIGHT= [0x6bb2b2ff,0x3f7f7fff]
TILE_COLOURS_MAT = [0xcc8c65ff, 0x99694bff ]
DIRECT_INDIRECT_FLAGS = ['_direct','_indirect']
LG_SPLIT = True
MAT_SPLIT = False


def divide_b_by_a(input_nodes, x_pos, y_pos):
    divide_node=nuke.nodes.MergeExpression(inputs = input_nodes, channel0 = 'r', channel1 = 'g', channel2 = 'b', expr0 = 'Ar>0?Br>0?Br/Ar:0:0', expr1 = 'Ag>0?Bg>0?Bg/Ag:0:0', expr2 = 'Ab>0?Bb>0?Bb/Ab:0:0', label = 'divide B by A' )
    divide_node.setXYpos(x_pos, y_pos)
    return divide_node

def get_layers(node):
    '''returns a list of all the layers '''
    channels = node.channels()
    layers = list( set([c.split('.')[0] for c in channels]) )
    layers.sort()
    return layers

def comma_seperated_to_list(comma_seperated_string):
    comma_seperated_string = re.sub(' ', '', comma_seperated_string)
    output_list = comma_seperated_string.split(',')
    return output_list

def check_strings_in_string(list_of_strings, check_string):
    result = False
    for string in list_of_strings:
        if string in check_string:
            result = True
    return result

def get_aov_minicomp_settings():
    '''Customize lightgroup naming conventions used'''
    settings={}
    p = nuke.Panel('AOV Minicomp Settings')
    p.addSingleLineInput('lightgroup flags (comma separated)', LIGHTGROUP_FLAGS)
    p.addEnumerationPulldown('light aov style', 'direct+indirect combined')
    #p.addSingleLineInput('lightgroup flags to reject (comma separated)', LIGHTGROUP_REJECT_FLAGS)
    p.addSingleLineInput('material flags (comma separated)', MATERIAL_FLAGS)
    p.addEnumerationPulldown('material aov style', 'combined direct+indirect')
    #p.addSingleLineInput('material flags to reject (comma separated)', MATERIAL_REJECT_FLAGS)
    p.addBooleanCheckBox('show shuffle postage stamps', SHOW_POSTAGE_STAMPS)
    p.addBooleanCheckBox('breakout lightgroups', BREAKOUT_LIGHTGROUPS)
    p.addBooleanCheckBox('breakout materials', BREAKOUT_MATERIALS)
    p.addSingleLineInput('x_space', X_SPACE)
    p.addSingleLineInput('y_space', Y_SPACE)
    ret = p.show()
    if ret == 0:
        return {}
    ## collate and items to settings dictionary
    lg_flags = comma_seperated_to_list( p.value('lightgroup flags (comma separated)') )
    if p.value('light aov style') == 'direct+indirect':
        lg_split=True
    else:
        lg_split=False
    mat_flags = comma_seperated_to_list( p.value('material flags (comma separated)') )
    if p.value('material aov style') == 'direct+indirect':
        mat_split=True
    else:
        mat_split=False
    breakout_materials = p.value ('breakout materials')
    breakout_lightgroups = p.value ('breakout lightgroups')
    settings['flags'] = [(breakout_lightgroups, lg_flags, TILE_COLOURS_LIGHT, lg_split), (breakout_materials, mat_flags, TILE_COLOURS_MAT, mat_split)]
    settings['pstamps'] = p.value('show shuffle postage stamps')
    settings['x_space'] = p.value('x_space')
    settings['y_space'] = p.value('y_space')
    
    return settings


def get_lightgroups(node, flags ):
    '''Returns a list of aovs which are lightgroups (based on naming convention flags set in LightGroupLabels list) ''' 
    
    aov_layers=[]
    for aov in get_layers(node):
    
        for flag in flags:
            if flag in aov and aov not in aov_layers:
                aov_layers.append(aov)
    aov_layers.sort()
    return aov_layers
    

def deselect_all_nodes():
    for n in nuke.selectedNodes():
        n['selected'].setValue(False)


        
def create_minicomp(node, get_user_settings=True):
    if get_user_settings == True:
        settings = get_aov_minicomp_settings()
        if settings == {}:
            return
    else:
        settings = {"flags":[[BREAKOUT_LIGHTGROUPS, comma_seperated_to_list(LIGHTGROUP_FLAGS),TILE_COLOURS_LIGHT, LG_SPLIT ], 
                            [BREAKOUT_MATERIALS, comma_seperated_to_list(MATERIAL_FLAGS), TILE_COLOURS_MAT, MAT_SPLIT]],
                "pstamps":SHOW_POSTAGE_STAMPS,
                "x_space":X_SPACE,
                "y_space": Y_SPACE}
    materials = True
    main_b_pipe = [node]
    x_pos, y_pos=int(node.xpos()), int(node.ypos())
    x_space, y_space = int(settings['x_space']), int(settings['y_space'])
    y_pos+=y_space
    b_pipe_root=nuke.nodes.NoOp(label = 'beauty', inputs=[node])
    b_pipe_root.setXYpos(node.xpos(), y_pos)
    main_b_pipe.append(b_pipe_root)
    y_pos+=y_space
    unpremult_all=nuke.nodes.Unpremult(channels='all', inputs=[b_pipe_root])
    unpremult_all.setXYpos(node.xpos(), y_pos)
    main_b_pipe.append(unpremult_all)
    original_dot = nuke.nodes.Dot(inputs = [b_pipe_root])
    original_dot.setXYpos(b_pipe_root.xpos()-int(x_space), b_pipe_root.ypos() )
    original_dots = [ original_dot ]
    loop_b_pipe=[main_b_pipe[:1]]
    
    # main breakout loop
    for flag in settings['flags']:
        logging.debug(flag)
        if flag[0]  == True :
            node = shuffle_out_aovs(main_b_pipe[-1], x_pos + x_space, y_pos, settings, flag)
            loop_b_pipe.append(node)
            y_pos= node.ypos()+y_space

            y_pos = node.ypos() + y_space
            dot = nuke.nodes.Dot(inputs = [ original_dots[-1] ] )
            original_dots.append( dot)
            original_dots[-1].setXYpos(original_dot.xpos(), y_pos )
            unpremult = nuke.nodes.Unpremult(inputs = [original_dots[-1]] )
            unpremult.setXYpos(int((x_pos+original_dots[-1].xpos())/2), y_pos )
            divide_node = divide_b_by_a ( [ main_b_pipe[-1], unpremult], x_pos, y_pos)
            main_b_pipe.append(divide_node)
            y_pos = y_pos + y_space
            merge_multiply = nuke.nodes.Merge(inputs = [ main_b_pipe[-1], node], operation = 'multiply', output = 'rgb')
            merge_multiply.setXYpos(main_b_pipe[-1].xpos(), y_pos )
            main_b_pipe.append(merge_multiply)
            y_pos = y_pos + y_space
            


    dot = nuke.nodes.Dot(inputs = [ original_dots[-1] ] )
    dot.setXYpos(original_dots[-1].xpos(),y_pos)
    original_dots.append( dot)
    y_pos+=y_space
    copy_alpha = nuke.nodes.Copy(inputs = [ main_b_pipe[-1] , original_dots[-1] ], from0 = 'rgba.alpha', to0 = 'rgba.alpha')
    copy_alpha.setXYpos(x_pos, y_pos)
    main_b_pipe.append(copy_alpha)
    y_pos+=y_space
    premult = nuke.nodes.Premult(inputs = [main_b_pipe[-1]] )
    premult.setXYpos(b_pipe_root.xpos(), y_pos)

def shuffle_out_aovs(node, x_pos, y_pos, settings, flag):
    '''This will create a mini comp from the layers flagged as lightgroups or materials in the user defined settings. Flags, spacing and use of postage stamps can be set in the panel as per the lightgroup_minicomp_settings function() '''
    x_space, y_space = int(settings['x_space']), int(settings['y_space'])
    y_pos+=y_space
    index_no =0
    loop_b_pipe_x = node.xpos() + x_space
    loop_top_node=nuke.nodes.Dot( inputs=[node])
    loop_top_node.setXYpos(loop_b_pipe_x, node.ypos() )
    remove_node = nuke.nodes.Remove(operation="remove", channels ="rgb", inputs=[loop_top_node])
    y_pos+=y_space
    remove_node.setXYpos(loop_b_pipe_x, y_pos)
    b_pipe_nodes=[loop_top_node, remove_node] #all the merge_plus nodes will be added to this list
    top_dots = [loop_top_node]

    aov_layers = get_lightgroups(node, flag[1])
    toggle_switch = {0:1,1:0}
    switch_pos = 0
    for aov in aov_layers:
        logging.info(aov)
        ## check if aovs need splitting into direct/indirect - currently it's all the avos or none of them
        if flag[3]  ==  True and check_strings_in_string(DIRECT_INDIRECT_FLAGS , aov ) == False:
            continue
        if flag[3] == False and check_strings_in_string(DIRECT_INDIRECT_FLAGS , aov ) == True:
            continue
        deselect_all_nodes()
        selected=[]
        x_pos +=x_space
        y_pos +=y_space

        dot=nuke.nodes.Dot( inputs=[ top_dots [index_no] ] )
        top_dots.append(dot)
        dot.setXpos (x_pos)
        dot.setYpos(node.ypos())
        shuffle_node = nuke.nodes.Shuffle2( label=aov, inputs=[top_dots[index_no+1]] )
        shuffle_node['in1'].setValue( aov )
        shuffle_node['in2'].setValue( 'alpha')
        shuffle_node['mappings'].setValue([('rgba.alpha','rgba.alpha')])
        shuffle_node['postage_stamp'].setValue( settings['pstamps'])
        shuffle_node.setYpos(dot.ypos()+ 100)
        #tempDot=nuke.nodes.Dot( ) #defines corner of backdrop
        #tempDot.setXpos(x_pos+int(x_space/2))
        #tempDot.setYpos(shuffle_node.ypos()+ y_space*3)
        y_pos +=y_space
        bottom_corner = nuke.nodes.Dot( inputs=[ shuffle_node ], tile_color='536805631.0', label = '<i>'+aov )
        y_pos +=int(y_space/2)
        bottom_corner.setXYpos(x_pos, y_pos )
        merge_plus = nuke.nodes.Merge2 (operation ='plus', label = '<i>'+aov, tile_color='536805631.0', inputs=[ b_pipe_nodes[-1], bottom_corner ], output = 'rgb' )
        b_pipe_nodes.append( merge_plus )
        merge_plus.setXYpos(loop_b_pipe_x, y_pos)
        #for n in [dot, shuffle_node, tempDot]:
        #    n['selected'].setValue(True)
        #bg = nukescripts.autoBackdrop()
        bg_colours = flag[2] # pairs of colours
        bg_colour = bg_colours[switch_pos]
        bg = nuke.nodes.BackdropNode(xpos = int (x_pos-x_space/4), bdwidth = int (x_space/2), ypos = int(top_dots[-1].ypos()-y_space/4 ), bdheight = y_space*3, tile_color = bg_colour, note_font_size=22, z_order = -1 ) 
        bg['label'].setValue(aov)
        switch_pos = toggle_switch[switch_pos]
        #nuke.delete(tempDot)

        index_no +=1
        final_x_pos = x_pos + x_space
    y_pos +=y_space
    # pipe for unnasigned lights.
    unassigned_light_dot = nuke.nodes.Dot( inputs = [top_dots[-1]], label = '<i> unassigned' )
    unassigned_light_pipe = [unassigned_light_dot]
    unassigned_light_dot.setXpos (final_x_pos)
    unassigned_y_pos = dot.ypos()
    unassigned_light_dot.setYpos(unassigned_y_pos)
    index_no = 0
    for aov in aov_layers:
        
        merge_from=nuke.nodes.Merge2 (operation ='from', tile_color='4278190335.0', label = '<i>'+aov, inputs=[ unassigned_light_pipe[index_no], unassigned_light_pipe[index_no] ], Achannels=aov, output = 'rgb' )
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

    #bg = nukescripts.autoBackdrop()
    #bg['label'].setValue('unassigned lights')
    nuke.delete(tempDot)
    bottom_corner = nuke.nodes.Dot( tile_color='536805631.0', label = '<i> unassigned lights', inputs = [ unassigned_light_pipe[-1] ]  )
    bottom_corner.setXYpos(final_x_pos, y_pos )
    merge_plus = nuke.nodes.Merge2 (operation ='plus', label = '<i> unassigned lights', tile_color='536805631.0', inputs=[ b_pipe_nodes[-1], bottom_corner ], disable = True)
    merge_plus.setXYpos(b_pipe_nodes[-1].xpos(), y_pos)
    b_pipe_nodes.append( merge_plus )
    y_pos+=y_space
    #premult_all=nuke.nodes.Premult(channels = 'all', inputs = [b_pipe_nodes[-1]])
    #premult_all.setXYpos(b_pipe_nodes[-1].xpos(), y_pos)
    #b_pipe_nodes.append( premult_all )
    return b_pipe_nodes[-1]


