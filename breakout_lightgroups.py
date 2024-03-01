import re

def get_layers(readNode):
    '''returns a list of all the layers '''
    channels = readNode.channels()
    layers = list( set([c.split('.')[0] for c in channels]) )
    layers.sort()
    return layers

def get_lightgroup_minicomp_settings():
    '''Customize lightgroup naming conventions used'''
    settings={}
    p = nuke.Panel('Lighrgroup Shuffle out settings')
    p.addSingleLineInput('lightgroup flags (comma seperated)', '_ASS_, _L_, Light, light ')
    p.addBooleanCheckBox('show shuffle postage stamps', False)
    p.addSingleLineInput('xSpace', '600')
    p.addSingleLineInput('ySpace', '300')
    ret = p.show()
    flags=p.value('lightgroup flags (comma seperated)')
    flags= re.sub(' ', '', flags)
    settings['flags'] = flags.split(',')
    settings['pstamps'] = p.value('show shuffle postage stamps')
    settings['xSpace'] = p.value('xSpace')
    settings['ySpace'] = p.value('ySpace')
    return settings



def get_lightgroups(node, flags ):
    '''Returns a list of aovs which are lightgroups (based on naming convention flags set in LightGroupLabels list) ''' 
    
    lightGroupLayers=[]
    for aov in get_layers(n):
    
        for flag in flags:
            if flag in aov and aov not in lightGroupLayers:
                lightGroupLayers.append(aov)
    lightGroupLayers.sort()
    return lightGroupLayers

def deselect_all_nodes():
    for n in nuke.selectedNodes():
        n['selected'].setValue(False)

#print get_lightgroups(nuke.selectedNode(),['_ASS_', '_L_', 'lights', 'Lights'] )

def shuffle_out_lightgroups(node, settings = get_lightgroup_minicomp_settings() ):
    '''This will create a mini comp from the layers flagged as lightgroups in the user defined settings. Flags, spacing and use of postage stamps can be set in the panel as per the lightgroup_minicomp_settings function() '''

    xPos, yPos=int(node.xpos()), int(node.ypos())
    xSpace, ySpace = int(settings['xSpace']), int(settings['ySpace'])
    yPos+=ySpace
    beautyDot=nuke.nodes.NoOp(label = 'beauty', inputs=[node])
    beautyDot.setXYpos(node.xpos(), yPos)
    yPos+=ySpace
    unpremult=nuke.nodes.Unpremult(channels='all', inputs=[beautyDot])
    unpremult.setXYpos(node.xpos(), yPos)
    yPos+=ySpace


    indexNo =0
    bPipeNodes=[unpremult] #all the merge nodes will be added to this list
    topDots = [unpremult]
    for lg in get_lightgroups(node, settings['flags']):
        deselect_all_nodes()
        selected=[]
        xPos +=xSpace
        yPos +=ySpace

        dot=nuke.nodes.Dot( inputs=[ topDots [indexNo] ] )
        topDots.append(dot)
        dot.setXpos (xPos)
        dot.setYpos(unpremult.ypos())
        shuffleNode = nuke.nodes.Shuffle2( label=lg, inputs=[topDots[indexNo+1]] )
        shuffleNode['in1'].setValue( lg )
        shuffleNode['postage_stamp'].setValue( settings['pstamps'])
        shuffleNode.setYpos(dot.ypos()+ 100)
        tempDot=nuke.nodes.Dot( ) #defines corner of backdrop
        tempDot.setXpos(xPos+int(xSpace/2))
        tempDot.setYpos(shuffleNode.ypos()+ ySpace*3)
        yPos +=ySpace
        fromNode=nuke.nodes.Merge2 (operation ='from', tile_color='4278190335.0', label = '<i>'+lg, inputs=[ bPipeNodes[indexNo], bPipeNodes[indexNo] ], Achannels=lg)
        fromNode.setXYpos(node.xpos(), yPos )
        bottomCorner = nuke.nodes.Dot( inputs=[ shuffleNode ], tile_color='536805631.0', label = '<i>'+lg )
        yPos +=int(ySpace/2)
        bottomCorner.setXYpos(xPos, yPos )
        merge = nuke.nodes.Merge2 (operation ='plus', label = '<i>'+lg, tile_color='536805631.0', inputs=[ fromNode, bottomCorner ])
        bPipeNodes.append( merge )
        merge.setXYpos(node.xpos(), yPos)
        for n in [dot, shuffleNode, tempDot]:
            n['selected'].setValue(True)
        bg = nukescripts.autoBackdrop()
        bg['label'].setValue(lg)
        nuke.delete(tempDot)

        indexNo +=1
    yPos +=ySpace
    alphaDot = nuke.nodes.Dot(inputs = [beautyDot])
    alphaDot2 = nuke.nodes.Dot(inputs = [alphaDot])
    alphaDot.setXYpos(unpremult.xpos()-int(xSpace/2), beautyDot.ypos() )
    alphaDot2.setXYpos(alphaDot.xpos(), yPos )
    copyAlpha = nuke.nodes.Copy(from0 = 'rgba.alpha', to0 = 'rgba.alpha', inputs = [merge, alphaDot2] )
    copyAlpha.setXYpos(node.xpos(), yPos )
    yPos+=ySpace
    removeNode=nuke.nodes.Remove(inputs = [copyAlpha], operation='keep', channels='rgba', label ='<b>[value operation] [value channels]')
    removeNode.setXYpos(node.xpos(), yPos)
    yPos+=ySpace
    premult = nuke.nodes.Premult(inputs = [removeNode] )
    premult.setXYpos(node.xpos(), yPos)

n= nuke.selectedNode()
shuffle_out_lightgroups(n)



