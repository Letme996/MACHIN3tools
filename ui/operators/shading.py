import bpy
from bpy.props import IntProperty, StringProperty
from math import degrees, radians
from mathutils import Matrix
from ... utils.registration import get_prefs


show_overlays = {'SOLID': True,
                 'MATERIAL': False,
                 'RENDERED': False,
                 'WIREFRAME': True}


class SwitchShading(bpy.types.Operator):
    bl_idname = "machin3.switch_shading"
    bl_label = "MACHIN3: Switch Shading"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    shading_type: StringProperty(name="Shading Type", default='SOLID')

    # hidden (screen casting)
    toggled_overlays = False

    @classmethod
    def description(cls, context, properties):
        shading = context.space_data.shading
        overlay = context.space_data.overlay
        shading_type = properties.shading_type

        if shading.type == shading_type:
            return f"{'Disable' if overlay.show_overlays else 'Enable'} Overlays for {shading_type.capitalize()} Shading"
        else:
            return f"Switch to {shading_type.capitalize()} shading"

    def execute(self, context):
        global show_overlays

        overlay = context.space_data.overlay
        shading = context.space_data.shading

        # toggle overlays
        if shading.type == self.shading_type:
            show_overlays[self.shading_type] = not show_overlays[self.shading_type]
            self.toggled_overlays = 'Enable' if show_overlays[self.shading_type] else 'Disable'

        # change shading to self.shading_type
        else:
            shading.type = self.shading_type
            self.toggled_overlays = False

        overlay.show_overlays = show_overlays[self.shading_type]
        return {'FINISHED'}


class ToggleOutline(bpy.types.Operator):
    bl_idname = "machin3.toggle_outline"
    bl_label = "Toggle Outline"
    bl_description = "Toggle Object Outlines"
    bl_options = {'REGISTER'}

    def execute(self, context):
        shading = context.space_data.shading

        shading.show_object_outline = not shading.show_object_outline

        return {'FINISHED'}


class ToggleCavity(bpy.types.Operator):
    bl_idname = "machin3.toggle_cavity"
    bl_label = "Toggle Cavity"
    bl_description = "Toggle Cavity (Screen Space Ambient Occlusion)"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene

        scene.M3.show_cavity = not scene.M3.show_cavity

        return {'FINISHED'}


class ToggleCurvature(bpy.types.Operator):
    bl_idname = "machin3.toggle_curvature"
    bl_label = "Toggle Curvature"
    bl_description = "Toggle Curvature (Edge Highlighting)"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene

        scene.M3.show_curvature = not scene.M3.show_curvature

        return {'FINISHED'}


matcap1_color_type = None


class MatcapSwitch(bpy.types.Operator):
    bl_idname = "machin3.matcap_switch"
    bl_label = "Matcap Switch"
    bl_description = "Quickly Switch between two Matcaps"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if context.space_data.type == 'VIEW_3D':
            shading = context.space_data.shading
            return shading.type == "SOLID" and shading.light == "MATCAP"

    def execute(self, context):
        view = context.space_data
        shading = view.shading

        matcap1 = get_prefs().switchmatcap1
        matcap2 = get_prefs().switchmatcap2

        switch_background = get_prefs().matcap_switch_background

        force_single = get_prefs().matcap2_force_single
        global matcap1_color_type

        disable_overlays = get_prefs().matcap2_disable_overlays

        if matcap1 and matcap2 and "NOT FOUND" not in [matcap1, matcap2]:
            if shading.studio_light == matcap1:
                shading.studio_light = matcap2

                if switch_background:
                    shading.background_type = get_prefs().matcap2_switch_background_type

                    if get_prefs().matcap2_switch_background_type == 'VIEWPORT':
                        shading.background_color = get_prefs().matcap2_switch_background_viewport_color

                if force_single and shading.color_type != 'SINGLE':
                    matcap1_color_type = shading.color_type
                    shading.color_type = 'SINGLE'

                if disable_overlays and view.overlay.show_overlays:
                    view.overlay.show_overlays = False

            elif shading.studio_light == matcap2:
                shading.studio_light = matcap1

                if switch_background:
                    shading.background_type = get_prefs().matcap1_switch_background_type

                    if get_prefs().matcap1_switch_background_type == 'VIEWPORT':
                        shading.background_color = get_prefs().matcap1_switch_background_viewport_color

                if force_single and matcap1_color_type:
                    shading.color_type = matcap1_color_type
                    matcap1_color_type = None

                if disable_overlays and not view.overlay.show_overlays:
                    view.overlay.show_overlays = True

            else:
                shading.studio_light = matcap1

        return {'FINISHED'}


class RotateStudioLight(bpy.types.Operator):
    bl_idname = "machin3.rotate_studiolight"
    bl_label = "MACHIN3: Rotate Studiolight"
    bl_options = {'REGISTER', 'UNDO'}

    angle: IntProperty(name="Angle")

    @classmethod
    def description(cls, context, properties):
        return "Rotate Studio Light by %d degrees\nALT: Rotate visible lights too" % (int(properties.angle))

    def invoke(self, context, event):
        current = degrees(context.space_data.shading.studiolight_rotate_z)
        new = (current + self.angle)

        # deal with angles beyond 360
        if new > 360:
            new = new % 360

        # shift angle into blender's -180 to 180 range
        if new > 180:
            new = -180 + (new - 180)

        context.space_data.shading.studiolight_rotate_z = radians(new)

        if event.alt:
            rmx = Matrix.Rotation(radians(self.angle), 4, 'Z')
            lights = [obj for obj in context.visible_objects if obj.type == 'LIGHT']

            for light in lights:
                light.matrix_world = rmx @ light.matrix_world

        return {'FINISHED'}
