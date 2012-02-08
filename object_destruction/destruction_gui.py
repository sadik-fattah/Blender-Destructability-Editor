from bpy import types, props, utils, ops, data, path
from bpy.types import Object, Scene
from . import destruction_proc as dp
from . import destruction_data as dd
import math
import os
import bpy
from mathutils import Vector
#import pickle
#import inspect


class DestructabilityPanel(types.Panel):
    bl_idname = "OBJECT_PT_destructability"
    bl_label = "Destructability"
    bl_context = "object"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    
    def register():
        dp.initialize()

    def unregister():
        dp.uninitialize()
    
    def draw(self, context):        
        
        layout = self.layout
        
       # row = layout.row()
       # row.label(text = "Apply this settings to:")
       # row.prop(context.active_object.destruction, "transmitMode",  text = "")
       # layout.separator()
        
        row = layout.row()
        row.prop(context.active_object.destruction, "destroyable", text = "Destroyable")
        
        row = layout.row()
        row.prop(context.object.destruction, "destructionMode", text = "Mode")
        row.active = context.object.destruction.destroyable

        col = layout.column()
        col.prop(context.object.destruction, "partCount", text = "Parts")
        
        if context.object.destruction.destructionMode == 'DESTROY_F':
            col.prop(context.object.destruction, "roughness", text = "Roughness")
            col.prop(context.object.destruction, "crack_type", text = "Crack Type")
        elif context.object.destruction.destructionMode.startswith('DESTROY_E'):
            col.prop(context.object.destruction, "wallThickness", text = "Thickness")
            col.prop(context.object.destruction, "pieceGranularity", text = "Granularity")
        elif context.object.destruction.destructionMode == 'DESTROY_K':
            col.prop(context.object.destruction, "cut_type", text = "Cut type")
            col.prop(context.object.destruction, "jitter", text = "Jitter")
            col.prop(context.object.destruction, "pieceGranularity", text = "Granularity")
        col.active = context.object.destruction.destroyable
        
        row = layout.row()
        if context.object.name in dd.DataStore.backups:
            row.operator("object.undestroy")
        else:
            row.operator("object.destroy")
        row.active = context.object.destruction.destroyable
        
        layout.separator()
       
        layout.prop(context.object.destruction, "isGround", text = "Is Connectivity Ground")
        layout.prop(context.object.destruction, "groundConnectivity", text = "Calculate Ground Connectivity")
        layout.prop(context.object.destruction, "cubify", text = "Intersect with Grid")
      #  layout.prop(context.object.destruction, "cascadeGround", text = "Cascade Ground")
        
        row = layout.row()
        row.label(text = "Connected Grounds")
        row.active = context.object.destruction.groundConnectivity
        
        row = layout.row()       
        row.template_list(context.object.destruction, "grounds", 
                          context.object.destruction, "active_ground", rows = 2)
        row.operator("ground.remove", icon = 'ZOOMOUT', text = "")
        row.active = context.object.destruction.groundConnectivity
        
        row = layout.row()
        row.label(text = "Select Ground:")
     #   row.prop(context.object.destruction, "groundSelector", text = "")
     #   ops.valid_ground.remove()
        
        row.prop_search(context.object.destruction, "groundSelector", 
                        context.scene, "validGrounds", icon = 'OBJECT_DATA', text = "")
        
      #  ops.valid_ground.add()                 
        row.operator("ground.add", icon = 'ZOOMIN', text = "")
        row.active = context.object.destruction.groundConnectivity
        
        row = layout.row()
        col = row.column()
        col.prop(context.object.destruction, "gridDim", text = "Connectivity Grid")
        col.active = context.object.destruction.groundConnectivity
        
       # col = row.column()
       # col.prop(context.object.destruction, "subgridDim", text = "Cubify Sub Grid")
       # col.active = context.object.destruction.cubify
        
        layout.separator()
         
        layout.prop(context.object.destruction, "destructor", text = "Destructor")
        
        row = layout.row()
        row.label(text = "Destructor Targets")
        row.active = context.object.destruction.destructor
        
        row = layout.row()
        
        row.template_list(context.object.destruction, "destructorTargets", 
                          context.object.destruction, "active_target" , rows = 2) 
                        
        row.operator("target.remove", icon = 'ZOOMOUT', text = "") 
        row.active = context.object.destruction.destructor  
        
        row = layout.row()
        row.label(text = "Select Destroyable: ")
     #   row.prop(context.object.destruction, "targetSelector", text = "")
     #   ops.valid_target.remove()
        
        row.prop_search(context.object.destruction, "targetSelector", context.scene, 
                       "validTargets", icon = 'OBJECT_DATA', text = "")
                       
     #   ops.valid_target.add()               
        row.operator("target.add", icon = 'ZOOMIN', text = "")
        row.active = context.object.destruction.destructor 
        
        row = layout.row()
        col = row.column() 
        
        col.operator("player.setup")
        col.active = not context.scene.player
        
        col = row.column()
        col.operator("player.clear")
        col.active = context.scene.player
        
        row = layout.row()
        
        txt = "To Editor Parenting"
        if not context.scene.converted:
            txt = "To Game Parenting"
       
        row.operator("parenting.convert", text = txt)
        
class AddGroundOperator(types.Operator):
    bl_idname = "ground.add"
    bl_label = "add ground"
    
    def execute(self, context):
        found = False
        for prop in context.object.destruction.grounds:
            if prop.name == context.object.destruction.groundSelector:
                found = True
                break
        if not found:
            propNew = context.object.destruction.grounds.add()
            propNew.name = context.object.destruction.groundSelector
            context.object.destruction.groundSelector = ""
            
            if propNew.name == "" or propNew.name == None:
                index = len(context.object.destruction.grounds) - 1
                context.object.destruction.grounds.remove(index)
                return {'CANCELLED'}
           
            index = 0
            for prop in context.scene.validTargets:
                if prop.name == propNew.name:
                    break
                index += 1
            context.scene.validGrounds.remove(index)
                
        return {'FINISHED'}   
    
class RemoveGroundOperator(types.Operator):
    bl_idname = "ground.remove"
    bl_label = "remove ground"
    
    def execute(self, context):
        
        if len(context.object.destruction.grounds) == 0:
            return {'CANCELLED'}
        
        index = context.object.destruction.active_ground
        name = context.object.destruction.grounds[index].name 
        context.object.destruction.grounds.remove(index)
        
        propNew = context.scene.validGrounds.add()
        propNew.name = name
        
        return {'FINISHED'}
       
        
class AddTargetOperator(types.Operator):
    bl_idname = "target.add"
    bl_label = "add target"
    
    def execute(self, context):
        found = False
        for prop in context.object.destruction.destructorTargets:
            if prop.name == context.object.destruction.targetSelector:
                found = True
                break
        if not found:
            propNew = context.object.destruction.destructorTargets.add()
            propNew.name = context.object.destruction.targetSelector
            context.object.destruction.targetSelector = ""
            
            if propNew.name == "" or propNew.name == None:
                index = len(context.object.destruction.destructorTargets) - 1
                context.object.destruction.destructorTargets.remove(index)
                return {'CANCELLED'}
            
            index = 0
            for prop in context.scene.validTargets:
                if prop.name == propNew.name:
                    break
                index += 1
            context.scene.validTargets.remove(index)
        return {'FINISHED'}   
    
class RemoveTargetOperator(types.Operator):
    bl_idname = "target.remove"
    bl_label = "remove target"
    
    def execute(self, context):
        
        if len(context.object.destruction.destructorTargets) == 0:
            return {'CANCELLED'}
        
        index = context.object.destruction.active_target
        name = context.object.destruction.destructorTargets[index].name 
        context.object.destruction.destructorTargets.remove(index)
        
        propNew = context.scene.validTargets.add()
        propNew.name = name
        return {'FINISHED'} 
    
class SetupPlayer(types.Operator):
    bl_idname = "player.setup"
    bl_label = "Setup Player"
    
    def execute(self, context):
        
        if context.scene.player:
            return
        
        context.scene.player = True
       
        
        ops.object.add()
        context.active_object.name = "Player"
       
        ops.object.add(type = 'CAMERA')
        context.active_object.name = "Eye"
         
        ops.object.add(type = 'EMPTY')
        context.active_object.name = "Launcher"
        ops.transform.translate(value = (0.5, 0.8, -0.8))
      
        data.objects["Eye"].parent = data.objects["Player"]
        data.objects["Launcher"].parent = data.objects["Eye"]
        
        data.objects["Player"].select = False
        data.objects["Eye"].select = True
        data.objects["Launcher"].select = False
        ops.transform.rotate(value = [math.radians(90)], 
                             constraint_axis = [True, False, False])
                             
        data.objects["Player"].select = True
        data.objects["Eye"].select = False
        data.objects["Launcher"].select = False
        ops.transform.rotate(value = [math.radians(90)], 
                             constraint_axis = [False, False, True])                     
        
        data.objects["Eye"].select = False
        data.objects["Player"].select = True
        ops.transform.translate(value = (3, 0, 3))
        
        ops.mesh.primitive_ico_sphere_add(layers = [False, True, False, False, False,
                                                    False, False, False, False, False,
                                                    False, False, False, False, False,
                                                    False, False, False, False, False])
        context.active_object.name = "Ball"   
        
        context.active_object.game.physics_type = 'RIGID_BODY'
        context.active_object.game.collision_bounds_type = 'SPHERE'                                          
        
        #load bge scripts
        print(__file__)
        currentDir = path.abspath(os.path.split(__file__)[0])
        
       # print(path.abspath(data.texts
        print(ops.text.open(filepath = currentDir + "\destruction_bge.py", internal = False))
        print(ops.text.open(filepath = currentDir + "\player.py", internal = False))
        print(ops.text.open(filepath = currentDir + "\destruction_data.py", internal = False))
        
        
        #setup logic bricks -player
        context.scene.objects.active = data.objects["Player"]
              
        #mouse aim and destruction setup
        ops.logic.controller_add(type = 'LOGIC_AND', object = "Player")
        ops.logic.controller_add(type = 'PYTHON', object = "Player")
        ops.logic.controller_add(type = 'PYTHON', object = "Player")
        
        context.active_object.game.controllers[1].mode = 'MODULE'
        context.active_object.game.controllers[1].module = "player.aim"
        
        context.active_object.game.controllers[2].mode = 'MODULE'
        context.active_object.game.controllers[2].module = "destruction_bge.setup"
        
        ops.logic.sensor_add(type = 'ALWAYS', object = "Player")
        ops.logic.sensor_add(type = 'MOUSE', object = "Player")
        context.active_object.game.sensors[1].mouse_event = 'MOVEMENT'
        
        ops.logic.actuator_add(type = 'SCENE', object = "Player")
        context.active_object.game.actuators[0].mode = 'CAMERA'
        context.active_object.game.actuators[0].camera = data.objects["Eye"]
        
        
        context.active_object.game.controllers[0].link(
            context.active_object.game.sensors[0],
            context.active_object.game.actuators[0])
        
        context.active_object.game.controllers[1].link(
            context.active_object.game.sensors[1])
        
        context.active_object.game.controllers[2].link(
            context.active_object.game.sensors[0]) 
                     
        #keyboard movement -> 6 directions, WSADYX as keys
        
        motionkeys = [ 'W', 'S', 'A',  'D' , 'Y', 'X' ]
        offsets  =  [[0.0, 0.1, 0.0],[0.0, -0.1, 0.0], [-0.1, 0.0, 0.0],
                     [0.1, 0.0, 0.0],[0.0, 0.0, -0.1], [0.0, 0.0, 0.1] ] 
        
        for i in range(0, 6):
            ops.logic.controller_add(type = 'LOGIC_AND', object = "Player")
            ops.logic.sensor_add(type = 'KEYBOARD', object = "Player")
            ops.logic.actuator_add(type = 'MOTION', object = "Player")
            
            context.active_object.game.sensors[i+2].key = motionkeys[i]
            context.active_object.game.actuators[i+1].offset_location = offsets[i]
            
            context.active_object.game.controllers[i+3].link(
            context.active_object.game.sensors[i+2],
            context.active_object.game.actuators[i+1])
                     
            
        #launcher
        context.scene.objects.active = data.objects["Launcher"]
        ops.logic.controller_add(type = 'PYTHON', object = "Launcher")
        
        context.active_object.game.controllers[0].mode = 'MODULE'
        context.active_object.game.controllers[0].module = "player.shoot"
        
        ops.logic.sensor_add(type = 'MOUSE', object = "Launcher")
        context.active_object.game.sensors[0].mouse_event = 'LEFTCLICK'
        
        ops.logic.actuator_add(type = 'EDIT_OBJECT', name = "Shoot", object = "Launcher")
        context.active_object.game.actuators[0].mode = 'ADDOBJECT'
        context.active_object.game.actuators[0].object = data.objects["Ball"]
        
        context.active_object.game.controllers[0].link(
            context.active_object.game.sensors[0],
            context.active_object.game.actuators[0])
        
        #ball
        context.scene.objects.active = data.objects["Ball"]
        ops.logic.controller_add(type = 'PYTHON', object = "Ball")
        ops.logic.sensor_add(type = 'COLLISION', object = "Ball")
        
        context.active_object.game.sensors[0].use_pulse_true_level = True
        
        context.active_object.game.controllers[0].mode = 'MODULE'
        context.active_object.game.controllers[0].module = "destruction_bge.collide"
        
        context.active_object.game.controllers[0].link(
            context.active_object.game.sensors[0])
        
        #by default destroy all destroyable objects
        context.active_object.destruction.destructor = True
        
        for o in context.scene.objects:
            if o.destruction.destroyable:
                target = context.active_object.destruction.destructorTargets.add()
                target.name = o.name
               #ctx = context.copy()
               #ctx["object"] = o
               #ops.valid_target.add(ctx)
               #context.scene.objects.active = o
               #context.object.destruction.selector
               #ops.target.add()
               
        context.scene.objects.active = context.object
        #ground and cells
        context.object.destruction.groundConnectivity = True
     #   context.object.destruction.gridDim = (2, 2, 2)
        
        ops.mesh.primitive_plane_add(location = (0, 0, -0.9))
        context.active_object.name = "Ground"
        context.active_object.destruction.isGround = True
        dp.updateValidGrounds(context.active_object)
        
        g = context.object.destruction.grounds.add()
        g.name = "Ground"
        
       # context        
        context.scene.objects.active = context.object
        return {'FINISHED'}
    
class ClearPlayer(types.Operator):
    bl_idname = "player.clear"
    bl_label = "Clear Player"
    
    def execute(self, context):
        
        if not context.scene.player:
            return
        context.scene.player = False
        
        for o in data.objects:
            o.select = False
        
        context.scene.layers = [True, True, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False]
        data.objects["Player"].select = True
        data.objects["Eye"].select = True
        data.objects["Launcher"].select = True
        data.objects["Ball"].select = True
        data.objects["Ground"].select = True
     
        ops.object.delete()
        
        context.scene.layers = [True, False, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False,
                                False, False, False, False, False]
                                
        data.texts.remove(data.texts["destruction_bge.py"])
        data.texts.remove(data.texts["player.py"])                        
        
        return {'FINISHED'}
    
        
class ConvertParenting(types.Operator):
    bl_idname = "parenting.convert"
    bl_label = "Convert Parenting"
    
    def execute(self, context):
        if not context.scene.converted:
            self.convert(context)
        else:
            self.unconvert(context)
        context.scene.converted = not context.scene.converted
        return {'FINISHED'}
        
    
    def convert(self, context):
        
        #temporarily parent all grounds to the parent object
        #rotate back, unparent with keep transform
        parent = None
        groundNames = None
        oldRot = None
        grounds = []
        for o in context.scene.objects:
            if o.name.startswith("P0"):
                parent = o
                groundNames = self.grounds(context, o, True)
                gNames = groundNames.split(" ")
                grounds = [g for g in gNames if g != ""]
                for g in grounds:
                    if g != "":
                        ground = context.scene.objects[g]
                        #ground.parent = parent
                        ground.select = True
                        ctx = context.copy()
                        ctx["object"] = parent
                        ops.object.parent_set(ctx)
                        ground.select = False
                       # print("Ground: ", ground.name)
               
                #clear rotation and drag ground with me
                oldRot = tuple(parent.rotation_euler)    
                parent.rotation_euler = (0, 0, 0)  
                
                for g in grounds:
                    ground = context.scene.objects[g]
                    ground.select = True
                    ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')
                    ops.object.transform_apply(rotation = True)
                    ground.select = False
                break
                  
        for o in context.scene.objects: #data.objects:
            
            if context.scene.player:
                if o.name == "Player" or o.name == "Eye" or \
                   o.name == "Launcher" or o.name == "Ground":
                       continue
            index = -1
            context.scene.objects.active = o
          #  ctx = dp.setObject(context, o)
            if o.parent != None:
                index = 0
                ops.object.game_property_new()
                o.game.properties[0].name = "myParent"
                o.game.properties[0].type = 'STRING'
                o.game.properties[0].value = o.parent.name
              #  o.parent = None
            
           # ctx = dp.setObject(context, o)    
            ops.object.game_property_new()
            o.game.properties[index + 1].name = "destroyable"
            o.game.properties[index + 1].type = 'BOOL'
            o.game.properties[index + 1].value = o.destruction.destroyable
            
        #    ctx = dp.setObject(context, o)
            ops.object.game_property_new()
            o.game.properties[index + 2].name = "isGround"
            o.game.properties[index + 2].type = 'BOOL'
            o.game.properties[index + 2].value = o.destruction.isGround
            
        #    ctx = dp.setObject(context, o)
            ops.object.game_property_new()
            o.game.properties[index + 3].name = "groundConnectivity"
            o.game.properties[index + 3].type = 'BOOL'
            o.game.properties[index + 3].value = o.destruction.groundConnectivity
            
         #   ctx = dp.setObject(context, o)
            ops.object.game_property_new()
            o.game.properties[index + 4].name = "grounds"
            o.game.properties[index + 4].type = 'STRING'
            o.game.properties[index + 4].value = self.grounds(context, o)
            
          #  ctx = dp.setObject(context, o)
            ops.object.game_property_new()
            o.game.properties[index + 5].name = "destructor"
            o.game.properties[index + 5].type = 'BOOL'
            o.game.properties[index + 5].value = o.destruction.destructor
            
          #  ctx = dp.setObject(context, o)
            ops.object.game_property_new()
            o.game.properties[index + 6].name = "destructorTargets"
            o.game.properties[index + 6].type = 'STRING'
            o.game.properties[index + 6].value = self.targets(o)
            
#            ctx = dp.setObject(context, o)
#            ops.object.game_property_new(ctx)
#            o.game.properties[index + 7].name = "grid"
#            o.game.properties[index + 7].type = 'STRING'
#            o.game.properties[index + 7].value = self.pickleGrid(o.name)

            
            bbox = o.destruction.gridBBox
            dim  = o.destruction.gridDim

          #  ctx = dp.setObject(context, o)
            ops.object.game_property_new()
            o.game.properties[index + 7].name = "gridbbox"
            o.game.properties[index + 7].type = 'STRING'
            o.game.properties[index + 7].value = str(round(bbox[0], 2)) + " " + \
                                                 str(round(bbox[1], 2)) + " " + \
                                                 str(round(bbox[2], 2)) 
            
         #   ctx = dp.setObject(context, o)
            ops.object.game_property_new()
            o.game.properties[index + 8].name = "griddim"
            o.game.properties[index + 8].type = 'STRING'
            o.game.properties[index + 8].value = str(dim[0]) + " " + str(dim[1]) + " " + str(dim[2])
            
            
            
        #parent again , rotate to rotation, clear parent with keeptransform    
        for g in grounds:
            ground = context.scene.objects[g]
            ground.select = True
            ctx = context.copy()
            ctx["object"] = parent
            ops.object.parent_set(ctx)
            ground.select = False
            #ground.parent = parent
       
        #restore rotation
        if parent != None:
            parent.rotation_euler = oldRot  
        
        for g in grounds:
            ground = context.scene.objects[g]
            ground.select = True
            ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')
            ops.object.transform_apply(rotation = True)
            ground.select = False
        
  
        for o in data.objects: #restrict to P_ parents only ! no use all
            if context.scene.player:
                if o.name == "Player" or o.name == "Eye" or \
                   o.name == "Launcher" or o.name == "Ground":
                    continue
            #o.parent = None
           # ctx = context.copy()
        #    ctx["object"] = o
            o.select = True
            ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')
            o.select = False
                       
    def unconvert(self, context):
        pos = Vector((0.0, 0.0, 0.0))
        for o in context.scene.objects:
             if o.name.startswith("P0"):
                 pos = dd.DataStore.backups[o.name].location
                 break
        
        for o in context.scene.objects:
            
            if context.scene.player:
                if o.name == "Player" or o.name == "Eye" or \
                   o.name == "Launcher" or o.name == "Ground":
                       continue
            
            context.scene.objects.active = o
            if len(o.game.properties) > 8:
                #correct some parenting error -> children at wrong position
                par = data.objects[o.game.properties[0].value]
                if par.name.startswith("P0"):
                    o.location -= pos
                o.parent = par
                
            while len(o.game.properties) > 0:
                #ctx = dp.setObject(context, o)
                ops.object.game_property_remove()
    
    def grounds(self, context, o, namesOnly = False):
       retVal = ""
       for g in o.destruction.grounds:
           if not namesOnly:
               retVal = retVal + g.name + ";" + self.getVerts(context.scene.objects[g.name], context)
           else:
               retVal = retVal + g.name + " " 
       return retVal
   
    def getVerts(self,g, context):
        #use bbox here first, maybe later exact shape -> bad performance!!
        bboxMesh = g.bound_box.data.to_mesh(context.scene, False, 'PREVIEW')
        retVal = ""
        print("GETVERTS:", bboxMesh.edge_keys)
        for key in bboxMesh.edge_keys:
            vStart = bboxMesh.vertices[key[0]].co
            vEnd = bboxMesh.vertices[key[1]].co
           # dataStr = str(round(vStart[0], 1)) + "," + str(round(vStart[1], 1)) + "," + \
        #              str(round(vStart[2], 1)) + "," + str(round(vEnd[0], 1)) + "," + \
         #             str(round(vEnd[1], 1)) + "," + str(round(vEnd[2], 1)) + "_"
            dataStr = str(round(vStart[0], 1)) + "," + str(round(vEnd[0], 1)) + "," + \
                      str(round(vStart[1], 1)) + "," + str(round(vEnd[1], 1)) + "," + \
                      str(round(vStart[2], 1)) + "," + str(round(vEnd[2], 1)) + "_"
            retVal = retVal + dataStr
        retVal = retVal.rstrip("_")
        return retVal     
   
    def targets(self, o):
       retVal = ""
       for t in o.destruction.destructorTargets:
           retVal = retVal + t.name + " "
       return retVal
   
#    def pickleGrid(self, name):
#        print(name, dd.DataStore.grids, name in dd.DataStore.grids.keys())
#        if name not in dd.DataStore.grids.keys():
#            return ""
#        grid = dd.DataStore.grids[name]
#        print(inspect.getmembers(grid.cells[(0,0,0)]))
#        strObj = str(pickle.dumps(grid), 'ascii')
#        print("Pickled: ", strObj)
#        return strObj                 
#   
class DestroyObject(types.Operator):
    bl_idname = "object.destroy"
    bl_label = "Destroy Object"
    
    def execute(self, context):
        dd.DataStore.proc.processDestruction(context)
        return {'FINISHED'}

class UndestroyObject(types.Operator):
    bl_idname = "object.undestroy"
    bl_label = "Undestroy Object"
    
    def execute(self, context):
        #context.scene.objects.link(context.object.destruction["backup"])
        context.scene.objects.link(dd.DataStore.backups[context.object.name])
        del dd.DataStore.backups[context.object.name]
        
        for o in data.objects:
            o.select = False
            
        context.object.select = True
        self.selectShards(context.object)
        ops.object.delete()
       
        return {'FINISHED'}
    
    def selectShards(self, object):
        for c in object.children:
            c.select = True
            self.selectShards(c)
            