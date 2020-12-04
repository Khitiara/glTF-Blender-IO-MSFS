# Copyright 2018-2019 The glTF-Blender-IO authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bpy
from mathutils import Vector, Quaternion, Matrix
from math import radians
from ..com.gltf2_blender_extras import set_extras
from .gltf2_blender_mesh import BlenderMesh
from .gltf2_blender_camera import BlenderCamera
from .gltf2_blender_light import BlenderLight
from .gltf2_blender_vnode import VNode

class BlenderNode():
    """Blender Node."""
    def __new__(cls, *args, **kwargs):
        raise RuntimeError("%s should not be instantiated" % cls)

    @staticmethod
    def create_vnode(gltf, vnode_id):
        """Create VNode and all its descendants."""
        vnode = gltf.vnodes[vnode_id]
        if vnode.name is not None:
            print('create_vnode: ' + vnode.name)

        gltf.display_current_node += 1
        if bpy.app.debug_value == 101:
            gltf.log.critical("Node %d of %d (id %s)", gltf.display_current_node, len(gltf.vnodes), vnode_id)

        if vnode.type == VNode.Object:
            BlenderNode.create_object(gltf, vnode_id)
            if vnode.is_arma:
                BlenderNode.create_bones(gltf, vnode_id)

        elif vnode.type == VNode.Bone:
            # These are created with their armature
            pass

        elif vnode.type == VNode.DummyRoot:
            # Don't actually create this
            vnode.blender_object = None

        for child in vnode.children:
            BlenderNode.create_vnode(gltf, child)

    @staticmethod
    def create_object(gltf, vnode_id):
        vnode = gltf.vnodes[vnode_id]
        is_skinned_mesh = False

        if vnode.mesh_node_idx is not None:
            obj = BlenderNode.create_mesh_object(gltf, vnode)
            pynode = gltf.data.nodes[vnode.mesh_node_idx]
            if pynode.skin is not None:
                is_skinned_mesh = True

        elif vnode.camera_node_idx is not None:
            pynode = gltf.data.nodes[vnode.camera_node_idx]
            cam = BlenderCamera.create(gltf, pynode.camera)
            name = vnode.name or cam.name
            obj = bpy.data.objects.new(name, cam)

        elif vnode.light_node_idx is not None:
            pynode = gltf.data.nodes[vnode.light_node_idx]
            light = BlenderLight.create(gltf, pynode.extensions['KHR_lights_punctual']['light'])
            name = vnode.name or light.name
            obj = bpy.data.objects.new(name, light)

        elif vnode.is_arma:
            armature = bpy.data.armatures.new(vnode.arma_name)
            name = vnode.name or armature.name
            obj = bpy.data.objects.new(name, armature)

        else:
            name = vnode.name or vnode.default_name
            obj = bpy.data.objects.new(name, None)

        vnode.blender_object = obj

        # Set extras (if came from a glTF node)
        if isinstance(vnode_id, int):
            pynode = gltf.data.nodes[vnode_id]
            set_extras(obj, pynode.extras)

        # Set transform
        trans, rot, scale = vnode.trs()
        if is_skinned_mesh and gltf.vnodes[vnode.parent].type != VNode.Bone:
            obj.location = Vector((0, 0, 0))
        else:
            obj.location = trans
        obj.rotation_mode = 'QUATERNION'
        if is_skinned_mesh and gltf.vnodes[vnode.parent].type != VNode.Bone:
            obj.rotation_quaternion = Quaternion((1, 0, 0, 0))
        else:
            obj.rotation_quaternion = rot
        # if is_skinned_mesh:
        #     if gltf.vnodes[vnode.parent].type == VNode.Bone:
        #         # mat = gltf.vnodes[gltf.vnodes[gltf.vnodes[vnode.parent].parent].parent].editbone_arma_mat
        #         # obj.location = mat @ Vector((0, 0, 0))
        #         # x = vnode.base_trs[0]
        #         # obj.location = Vector((x[0], -x[1], x[2]))
        #         obj.location = Vector((0, 0, 0))
        #     else:
        #         obj.location = Vector((0, 0, 0))
        # else:
        #     obj.location = trans
        # obj.rotation_mode = 'QUATERNION'
        # if is_skinned_mesh:
        #     if gltf.vnodes[vnode.parent].type == VNode.Bone:
        #         # mat = gltf.vnodes[gltf.vnodes[gltf.vnodes[vnode.parent].parent].parent].editbone_arma_mat
        #         # mat2 = gltf.vnodes[vnode.parent].editbone_arma_mat
        #         # obj.rotation_quaternion = (mat @ Quaternion((1, 0, 0, 0)).to_matrix().to_4x4()).to_quaternion()
        #         # obj.rotation_quaternion = mat.decompose()[1]
                
        #         # obj.rotation_quaternion = (mat @ vnode.base_trs[1].to_matrix().to_4x4()).to_quaternion()
        #         mat_rot_z = Matrix.Rotation(radians(-90.0), 4, 'Z')
        #         # obj.rotation_quaternion = (mat @ mat_rot_z).to_quaternion()
        #         # obj.rotation_quaternion = (mat @ mat_rot_z).to_quaternion()
        #         obj.rotation_quaternion = (mat_rot_z).to_quaternion()
        #         # obj.rotation_quaternion = Quaternion((1, 0, 0, 0))
        #         # obj.rotation_quaternion = vnode.base_trs[1]
        #     else:
        #         obj.rotation_quaternion = Quaternion((1, 0, 0, 0))
        # else:
        #     obj.rotation_quaternion = rot
        # # if is_skinned_mesh and gltf.vnodes[vnode.parent].type != VNode.Bone:
        # #     # if gltf.vnodes[vnode.parent].type == VNode.Bone:
        # #     #     obj.location = vnode.parent.trs()[0]
        # #     # else:
        # #     obj.location = Vector((0, 0, 0))
        # # else:
        # obj.location = trans
        # obj.rotation_mode = 'QUATERNION'
        # # if is_skinned_mesh and gltf.vnodes[vnode.parent].type != VNode.Bone:
        # #     # if gltf.vnodes[vnode.parent].type == VNode.Bone:
        # #     #     obj.location = vnode.parent.trs()[1]
        # #     # else:
        # #     obj.rotation_quaternion = Quaternion((1, 0, 0, 0))
        # # else:
        # obj.rotation_quaternion = rot
        obj.scale = scale

        # Set parent
        if vnode.parent is not None:
            parent_vnode = gltf.vnodes[vnode.parent]
            # print('Set parent for child: ' + vnode.name)
            # print('parent: ' + parent_vnode.name)
            if parent_vnode.type == VNode.Object:
                obj.parent = parent_vnode.blender_object
            # elif is_skinned_mesh and gltf.vnodes[vnode.parent].type == VNode.Bone:
            #     skin = gltf.data.nodes[vnode.mesh_node_idx].skin
            #     pyskin = gltf.data.skins[skin]
            #     arma_vnode = gltf.vnodes[gltf.vnodes[pyskin.joints[0]].bone_arma]
            #     obj.parent = arma_vnode.blender_object
            # elif is_skinned_mesh and gltf.vnodes[vnode.parent].type == VNode.Bone:
            #     # skin = gltf.data.nodes[vnode.mesh_node_idx].skin
            #     # pyskin = gltf.data.skins[skin]
            #     # parent_bone_skeleton_root_bone = gltf.vnodes[pyskin.joints[0]]
            #     super_parent_vnode = gltf.vnodes[gltf.vnodes[parent_vnode.parent].parent]
            #     super_parent_arma_vnode = gltf.vnodes[super_parent_vnode.bone_arma]
            #     # print('parent arma: ' + super_parent_arma_vnode.name)
            #     obj.parent = super_parent_arma_vnode.blender_object
            #     obj.parent_type = 'BONE'
            #     obj.parent_bone = super_parent_vnode.blender_bone_name
            #     obj.location += Vector((0, -super_parent_vnode.bone_length, 0))
            elif parent_vnode.type == VNode.Bone:
                arma_vnode = gltf.vnodes[parent_vnode.bone_arma]
                # print('parent arma: ' + arma_vnode.name)
                obj.parent = arma_vnode.blender_object
                obj.parent_type = 'BONE'
                obj.parent_bone = parent_vnode.blender_bone_name

                # Nodes with a bone parent need to be translated
                # backwards from the tip to the root
                obj.location += Vector((0, -parent_vnode.bone_length, 0))
                # if is_skinned_mesh:
                #     obj.location = parent_vnode.editbone_trans

        bpy.data.scenes[gltf.blender_scene].collection.objects.link(obj)

        return obj

    @staticmethod
    def create_bones(gltf, arma_id):
        arma = gltf.vnodes[arma_id]
        blender_arma = arma.blender_object
        blender_arma.show_in_front = True
        armature = blender_arma.data

        # Find all bones for this arma
        bone_ids = []
        def visit(id):  # Depth-first walk
            if gltf.vnodes[id].type == VNode.Bone:
                bone_ids.append(id)
                for child in gltf.vnodes[id].children:
                    visit(child)
        for child in arma.children:
            visit(child)

        # Switch into edit mode to create all edit bones

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.window.scene = bpy.data.scenes[gltf.blender_scene]
        bpy.context.view_layer.objects.active = blender_arma
        bpy.ops.object.mode_set(mode="EDIT")

        for id in bone_ids:
            vnode = gltf.vnodes[id]
            editbone = armature.edit_bones.new(vnode.name or vnode.default_name)
            vnode.blender_bone_name = editbone.name
            editbone.use_connect = False  # TODO?

            # Give the position of the bone in armature space
            arma_mat = vnode.editbone_arma_mat
            editbone.head = arma_mat @ Vector((0, 0, 0))
            editbone.tail = arma_mat @ Vector((0, 1, 0))
            editbone.align_roll(arma_mat @ Vector((0, 0, 1)) - editbone.head)
            editbone.length = vnode.bone_length

            if isinstance(id, int):
                pynode = gltf.data.nodes[id]
                set_extras(editbone, pynode.extras)

        # Set all bone parents
        for id in bone_ids:
            vnode = gltf.vnodes[id]
            parent_vnode = gltf.vnodes[vnode.parent]
            if parent_vnode.type == VNode.Bone:
                editbone = armature.edit_bones[vnode.blender_bone_name]
                parent_editbone = armature.edit_bones[parent_vnode.blender_bone_name]
                editbone.parent = parent_editbone

        # Switch back to object mode and do pose bones
        bpy.ops.object.mode_set(mode="OBJECT")

        for id in bone_ids:
            vnode = gltf.vnodes[id]
            pose_bone = blender_arma.pose.bones[vnode.blender_bone_name]

            # BoneTRS = EditBone * PoseBone
            # Set PoseBone to make BoneTRS = vnode.trs.
            t, r, s = vnode.trs()
            et, er = vnode.editbone_trans, vnode.editbone_rot
            pose_bone.location = er.conjugated() @ (t - et)
            pose_bone.rotation_mode = 'QUATERNION'
            pose_bone.rotation_quaternion = er.conjugated() @ r
            pose_bone.scale = s

            if isinstance(id, int):
                pynode = gltf.data.nodes[id]
                set_extras(pose_bone, pynode.extras)

    @staticmethod
    def create_mesh_object(gltf, vnode):
        pynode = gltf.data.nodes[vnode.mesh_node_idx]
        pymesh = gltf.data.meshes[pynode.mesh]

        # Key to cache the Blender mesh by.
        # Same cache key = instances of the same Blender mesh.
        cache_key = None
        if not pymesh.shapekey_names:
            cache_key = (pynode.skin,)
        else:
            # Unlike glTF, all instances of a Blender mesh share shapekeys.
            # So two instances that might have different morph weights need
            # different cache keys.
            if pynode.weight_animation is False:
                cache_key = (pynode.skin, tuple(pynode.weights or []))
            else:
                cache_key = None  # don't use the cache at all

        if cache_key is not None and cache_key in pymesh.blender_name:
            mesh = bpy.data.meshes[pymesh.blender_name[cache_key]]
        else:
            gltf.log.info("Blender create Mesh node %s", pymesh.name or pynode.mesh)
            mesh = BlenderMesh.create(gltf, pynode.mesh, pynode.skin)
            if cache_key is not None:
                pymesh.blender_name[cache_key] = mesh.name

        name = vnode.name or mesh.name
        obj = bpy.data.objects.new(name, mesh)

        if pymesh.shapekey_names:
            BlenderNode.set_morph_weights(gltf, pynode, obj)

        if pynode.skin is not None:
            BlenderNode.setup_skinning(gltf, pynode, obj)

        return obj

    @staticmethod
    def set_morph_weights(gltf, pynode, obj):
        pymesh = gltf.data.meshes[pynode.mesh]
        weights = pynode.weights or pymesh.weights or []
        for i, weight in enumerate(weights):
            if pymesh.shapekey_names[i] is not None:
                obj.data.shape_keys.key_blocks[pymesh.shapekey_names[i]].value = weight

    @staticmethod
    def setup_skinning(gltf, pynode, obj):
        pyskin = gltf.data.skins[pynode.skin]

        # Armature/bones should have already been created.

        # Create vertex groups for each joint
        for node_idx in pyskin.joints:
            bone = gltf.vnodes[node_idx]
            obj.vertex_groups.new(name=bone.blender_bone_name)

        # Create an Armature modifier
        first_bone = gltf.vnodes[pyskin.joints[0]]
        arma = gltf.vnodes[first_bone.bone_arma]
        mod = obj.modifiers.new(name="Armature", type="ARMATURE")
        mod.object = arma.blender_object
