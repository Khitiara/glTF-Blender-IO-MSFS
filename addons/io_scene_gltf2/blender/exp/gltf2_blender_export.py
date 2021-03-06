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
import time

import bpy
import sys
import traceback

from io_scene_gltf2.blender.com import gltf2_blender_json
from io_scene_gltf2.blender.exp import gltf2_blender_export_keys
from io_scene_gltf2.blender.exp import gltf2_blender_gather
from io_scene_gltf2.blender.exp.gltf2_blender_gltf2_exporter import GlTF2Exporter
from io_scene_gltf2.io.com.gltf2_io_debug import print_console, print_newline
from io_scene_gltf2.io.exp import gltf2_io_export
from io_scene_gltf2.io.exp import gltf2_io_draco_compression_extension
from io_scene_gltf2.io.exp.gltf2_io_user_extensions import export_user_extensions


def save(context, export_settings):
    """Start the glTF 2.0 export and saves to content either to a .gltf or .glb file."""
    if bpy.context.active_object is not None:
        if bpy.context.active_object.mode != "OBJECT": # For linked object, you can't force OBJECT mode
            bpy.ops.object.mode_set(mode='OBJECT')

    original_frame = bpy.context.scene.frame_current
    if not export_settings['gltf_current_frame']:
        bpy.context.scene.frame_set(0)

    __notify_start(context)
    start_time = time.time()
    export_settings[gltf2_blender_export_keys.BINARY_FILENAME] = bpy.context.scene['gltf_filename_no_ext'] + '.bin'
    export_settings['gltf_filename'] = bpy.context.scene['gltf_filename_no_ext'] + '.gltf'
    json, buffer = __export(export_settings)
    __write_file(json, buffer, export_settings)

    end_time = time.time()
    __notify_end(context, end_time - start_time)

    if not export_settings['gltf_current_frame']:
        bpy.context.scene.frame_set(original_frame)
    return {'FINISHED'}


def __export(export_settings):
    exporter = GlTF2Exporter(export_settings)
    __gather_gltf(exporter, export_settings)
    buffer = __create_buffer(exporter, export_settings)
    exporter.finalize_images()
    json = __fix_json(exporter.glTF.to_dict())

    return json, buffer


def __gather_gltf(exporter, export_settings):
    export_settings['bounding_box_max_x'] = 0
    export_settings['bounding_box_max_y'] = 0
    export_settings['bounding_box_max_z'] = 0
    export_settings['bounding_box_min_x'] = 0
    export_settings['bounding_box_min_y'] = 0
    export_settings['bounding_box_min_z'] = 0

    active_scene_idx, scenes, animations = gltf2_blender_gather.gather_gltf2(export_settings)

    print(f'gather_gltf2 complete')

    plan = {'active_scene_idx': active_scene_idx, 'scenes': scenes, 'animations': animations}
    export_user_extensions('gather_gltf_hook', export_settings, plan)
    active_scene_idx, scenes, animations = plan['active_scene_idx'], plan['scenes'], plan['animations']

    if export_settings['gltf_draco_mesh_compression']:
        gltf2_io_draco_compression_extension.compress_scene_primitives(scenes, export_settings)
        exporter.add_draco_extension()

    for idx, scene in enumerate(scenes):
        exporter.add_scene(scene, idx==active_scene_idx)
    for animation in animations:
        exporter.add_animation(animation)

    exporter.add_original_extensions(bpy.context.scene['extensionsRequired'], bpy.context.scene['extensionsUsed'])

    bounding_box_max = [
        export_settings['bounding_box_max_x'],
        export_settings['bounding_box_max_y'],
        export_settings['bounding_box_max_z'],
    ]
    bounding_box_min = [
        export_settings['bounding_box_min_x'],
        export_settings['bounding_box_min_y'],
        export_settings['bounding_box_min_z'],
    ]

    extensions = {
        "ASOBO_asset_optimized": {
            "BoundingBoxMax": bounding_box_max,
            "BoundingBoxMin": bounding_box_min,
            "MajorVersion": 4,
            "MinorVersion": 2
        },
        "ASOBO_normal_map_convention": {
            "tangent_space_convention": "DirectX"
        }
    }
    
    exporter.add_asobo_bounding_box(extensions)


def __create_buffer(exporter, export_settings):
    buffer = bytes()
    if export_settings[gltf2_blender_export_keys.FORMAT] == 'GLB':
        buffer = exporter.finalize_buffer(export_settings[gltf2_blender_export_keys.FILE_DIRECTORY], is_glb=True)
    else:
        if export_settings[gltf2_blender_export_keys.FORMAT] == 'GLTF_EMBEDDED':
            exporter.finalize_buffer(export_settings[gltf2_blender_export_keys.FILE_DIRECTORY])
        else:
            exporter.finalize_buffer(export_settings[gltf2_blender_export_keys.FILE_DIRECTORY],
                                     export_settings[gltf2_blender_export_keys.BINARY_FILENAME])

    return buffer


def __fix_json(obj):
    # TODO: move to custom JSON encoder
    fixed = obj
    if isinstance(obj, dict):
        fixed = {}
        for key, value in obj.items():
            if not __should_include_json_value(key, value):
                continue
            fixed[key] = __fix_json(value)
    elif isinstance(obj, list):
        fixed = []
        for value in obj:
            fixed.append(__fix_json(value))
    elif isinstance(obj, float):
        # force floats to int, if they are integers (prevent INTEGER_WRITTEN_AS_FLOAT validator warnings)
        if int(obj) == obj:
            return int(obj)
    return fixed


def __should_include_json_value(key, value):
    allowed_empty_collections = ["KHR_materials_unlit", "ASOBO_material_anisotropic", "ASOBO_material_SSS", "ASOBO_material_glass", \
        "ASOBO_material_blend_gbuffer", "ASOBO_material_clear_coat", "ASOBO_material_environment_occluder", "ASOBO_material_fake_terrain", \
            "ASOBO_material_fresnel_fade", "ASOBO_material_parallax_window", "ASOBO_material_invisible"] # asobo materials

    if value is None:
        return False
    elif __is_empty_collection(value) and key not in allowed_empty_collections:
        return False
    return True


def __is_empty_collection(value):
    return (isinstance(value, dict) or isinstance(value, list)) and len(value) == 0


def __write_file(json, buffer, export_settings):
    try:
        gltf2_io_export.save_gltf(
            json,
            export_settings,
            gltf2_blender_json.BlenderJSONEncoder,
            buffer)
    except AssertionError as e:
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb)  # Fixed format
        tb_info = traceback.extract_tb(tb)
        for tbi in tb_info:
            filename, line, func, text = tbi
            print_console('ERROR', 'An error occurred on line {} in statement {}'.format(line, text))
        print_console('ERROR', str(e))
        raise e


def __notify_start(context):
    print_console('INFO', 'Starting glTF 2.0 export')
    context.window_manager.progress_begin(0, 100)
    context.window_manager.progress_update(0)


def __notify_end(context, elapsed):
    print_console('INFO', 'Finished glTF 2.0 export in {} s'.format(elapsed))
    context.window_manager.progress_end()
    print_newline()
