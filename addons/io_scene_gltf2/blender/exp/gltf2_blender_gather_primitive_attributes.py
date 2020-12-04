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

from . import gltf2_blender_export_keys
from io_scene_gltf2_adenflorian.io.com import gltf2_io
from io_scene_gltf2_adenflorian.io.com import gltf2_io_constants
from io_scene_gltf2_adenflorian.io.com import gltf2_io_debug
from io_scene_gltf2_adenflorian.io.exp import gltf2_io_binary_data
from io_scene_gltf2_adenflorian.blender.exp import gltf2_blender_utils


def gather_primitive_attributes(blender_primitive, export_settings, asobo_vertex_type):
    """
    Gathers the attributes, such as POSITION, NORMAL, TANGENT from a blender primitive.

    :return: a dictionary of attributes
    """
    attributes = {}
    attributes.update(__gather_position(blender_primitive, export_settings))
    attributes.update(__gather_tangent(blender_primitive, export_settings))
    attributes.update(__gather_normal(blender_primitive, export_settings))
    attributes.update(__gather_texcoord(blender_primitive, export_settings))
    attributes.update(__gather_skins(blender_primitive, export_settings, asobo_vertex_type))
    attributes.update(__gather_colors(blender_primitive, export_settings, asobo_vertex_type))
    return attributes


def __gather_position(blender_primitive, export_settings):
    position = blender_primitive["attributes"]["POSITION"]
    componentType = gltf2_io_constants.ComponentType.Float
    return {
        "POSITION": gltf2_io.Accessor(
            buffer_view=position,
            byte_offset=None,
            component_type=componentType,
            count=len(position) // gltf2_io_constants.DataType.num_elements(gltf2_io_constants.DataType.Vec3),
            extensions=None,
            extras=None,
            max=gltf2_blender_utils.max_components(position, gltf2_io_constants.DataType.Vec3),
            min=gltf2_blender_utils.min_components(position, gltf2_io_constants.DataType.Vec3),
            name=None,
            normalized=None,
            sparse=None,
            type=gltf2_io_constants.DataType.Vec3
        )
    }


def __gather_normal(blender_primitive, export_settings):
    if export_settings[gltf2_blender_export_keys.NORMALS]:
        normal = blender_primitive["attributes"]['NORMAL']
        return {
            "NORMAL": gltf2_io.Accessor(
                buffer_view=list(map(lambda x: round(x * 127.0), normal)),
                byte_offset=None,
                # component_type=gltf2_io_constants.ComponentType.Float,
                component_type=gltf2_io_constants.ComponentType.Byte,
                # count=len(normal) // gltf2_io_constants.DataType.num_elements(gltf2_io_constants.DataType.Vec3),
                count=len(normal) // gltf2_io_constants.DataType.num_elements(gltf2_io_constants.DataType.Vec4),
                extensions=None,
                extras=None,
                max=None,
                min=None,
                name=None,
                normalized=None,
                sparse=None,
                # type=gltf2_io_constants.DataType.Vec3
                # What is the 4th component used for?
                # gltf spec mentioned it could be handedness?
                # maybe has something to do with why the normals were flipped when importing?
                type=gltf2_io_constants.DataType.Vec4
            )
        }
    return {}


def __gather_tangent(blender_primitive, export_settings):
    if export_settings[gltf2_blender_export_keys.TANGENTS]:
        if blender_primitive["attributes"].get('TANGENT') is not None:
            tangent = blender_primitive["attributes"]['TANGENT']
            return {
                "TANGENT": gltf2_io.Accessor(
                    buffer_view=list(map(lambda x: round(x * 127.0), tangent)),
                    byte_offset=None,
                    # component_type=gltf2_io_constants.ComponentType.Float,
                    component_type=gltf2_io_constants.ComponentType.Byte,
                    count=len(tangent) // gltf2_io_constants.DataType.num_elements(gltf2_io_constants.DataType.Vec4),
                    extensions=None,
                    extras=None,
                    max=None,
                    min=None,
                    name=None,
                    normalized=None,
                    sparse=None,
                    type=gltf2_io_constants.DataType.Vec4
                )
            }

    return {}


def __gather_texcoord(blender_primitive, export_settings):
    attributes = {}
    if export_settings[gltf2_blender_export_keys.TEX_COORDS]:
        tex_coord_index = 0
        tex_coord_id = 'TEXCOORD_' + str(tex_coord_index)
        while blender_primitive["attributes"].get(tex_coord_id) is not None:
            tex_coord = blender_primitive["attributes"][tex_coord_id]
            attributes[tex_coord_id] = gltf2_io.Accessor(
                buffer_view=tex_coord,
                byte_offset=None,
                # component_type=gltf2_io_constants.ComponentType.Float,
                component_type=gltf2_io_constants.ComponentType.Short, # (e) 2 byte float
                count=len(tex_coord) // gltf2_io_constants.DataType.num_elements(gltf2_io_constants.DataType.Vec2),
                extensions=None,
                extras=None,
                max=None,
                min=None,
                name=None,
                normalized=None,
                sparse=None,
                type=gltf2_io_constants.DataType.Vec2
            )
            tex_coord_index += 1
            tex_coord_id = 'TEXCOORD_' + str(tex_coord_index)
    return attributes


def __gather_colors(blender_primitive, export_settings, asobo_vertex_type):
    attributes = {}
    if export_settings[gltf2_blender_export_keys.COLORS]:
        color_index = 0
        color_id = 'COLOR_' + str(color_index)
        component_type = gltf2_io_constants.ComponentType.UnsignedShort if asobo_vertex_type == 'VTX' else gltf2_io_constants.ComponentType.Byte
        # converter = (lambda x: round(x * 65535.0)) if asobo_vertex_type == 'VTX' else (lambda x: round(x * 127.0))
        # All the colors in the vanilla gltf are 15360
        converter = (lambda x: 15360) if asobo_vertex_type == 'VTX' else (lambda x: -1)
        while blender_primitive["attributes"].get(color_id) is not None:
            internal_color = blender_primitive["attributes"][color_id]
            attributes[color_id] = gltf2_io.Accessor(
                buffer_view=list(map(converter, internal_color)),
                byte_offset=None,
                # component_type=gltf2_io_constants.ComponentType.Float,
                component_type=component_type,
                count=len(internal_color) // gltf2_io_constants.DataType.num_elements(gltf2_io_constants.DataType.Vec4),
                extensions=None,
                extras=None,
                max=None,
                min=None,
                name=None,
                normalized=None,
                sparse=None,
                type=gltf2_io_constants.DataType.Vec4
            )
            color_index += 1
            color_id = 'COLOR_' + str(color_index)
    return attributes


def __gather_skins(blender_primitive, export_settings, asobo_vertex_type):
    attributes = {}
    if export_settings[gltf2_blender_export_keys.SKINS]:
        bone_set_index = 0
        joint_id = 'JOINTS_' + str(bone_set_index)
        weight_id = 'WEIGHTS_' + str(bone_set_index)
        while blender_primitive["attributes"].get(joint_id) and blender_primitive["attributes"].get(weight_id):
            if bone_set_index >= 1:
                if not export_settings['gltf_all_vertex_influences']:
                    gltf2_io_debug.print_console("WARNING", "There are more than 4 joint vertex influences."
                                                            "The 4 with highest weight will be used (and normalized).")
                    break

            # joints
            internal_joint = blender_primitive["attributes"][joint_id]
            joint = gltf2_io.Accessor(
                buffer_view=internal_joint,
                byte_offset=None,
                component_type=gltf2_io_constants.ComponentType.UnsignedShort,
                count=len(internal_joint) // gltf2_io_constants.DataType.num_elements(gltf2_io_constants.DataType.Vec4),
                extensions=None,
                extras=None,
                max=None,
                min=None,
                name=None,
                normalized=None,
                sparse=None,
                type=gltf2_io_constants.DataType.Vec4
            )
            attributes[joint_id] = joint

            # weights
            internal_weight = blender_primitive["attributes"][weight_id]
            # normalize first 4 weights, when not exporting all influences
            if not export_settings['gltf_all_vertex_influences']:
                for idx in range(0, len(internal_weight), 4):
                    weight_slice = internal_weight[idx:idx + 4]
                    total = sum(weight_slice)
                    if total > 0:
                        factor = 1.0 / total
                        internal_weight[idx:idx + 4] = [w * factor for w in weight_slice]
            weight_data_type = gltf2_io_constants.DataType.Scalar if asobo_vertex_type == 'BLEND1' else gltf2_io_constants.DataType.Vec4
            weight = gltf2_io.Accessor(
                buffer_view=internal_weight if asobo_vertex_type == 'BLEND1' else [round(x * 65535.0) for x in internal_weight],
                byte_offset=None,
                component_type=gltf2_io_constants.ComponentType.Float if asobo_vertex_type == 'BLEND1' else gltf2_io_constants.ComponentType.UnsignedShort,
                count=len(internal_weight) // gltf2_io_constants.DataType.num_elements(
                    weight_data_type),
                extensions=None,
                extras=None,
                max=None,
                min=None,
                name=None,
                normalized=None,
                sparse=None,
                type=weight_data_type
            )
            attributes[weight_id] = weight

            bone_set_index += 1
            joint_id = 'JOINTS_' + str(bone_set_index)
            weight_id = 'WEIGHTS_' + str(bone_set_index)
    return attributes
