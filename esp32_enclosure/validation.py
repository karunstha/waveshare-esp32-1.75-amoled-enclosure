"""Parameter sanity checks that run before any geometry is built."""

from __future__ import annotations

from . import config as cfg


def validate_parameters() -> None:
    cavity_width = cfg.CASE_WIDTH - 2 * cfg.SIDE_WALL
    cavity_height = cfg.CASE_HEIGHT - 2 * cfg.SIDE_WALL
    cavity_depth = cfg.CASE_DEPTH - cfg.FRONT_WALL - cfg.REAR_WALL
    usable_depth_from_front = cfg.CASE_DEPTH - cfg.REAR_WALL
    required_depth_from_front = (
        cfg.NON_CONNECTOR_HARDWARE_DEPTH
        if cfg.ALLOW_REAR_CONNECTOR_PROTRUSION
        else cfg.MODULE_MAX_DEPTH
    ) + cfg.DEVICE_REAR_CLEARANCE

    if min(cavity_width, cavity_height, cavity_depth) <= 0:
        raise ValueError("Wall values leave no internal cavity.")
    if cfg.DISPLAY_POCKET_DIAMETER >= min(cfg.CASE_WIDTH, cfg.CASE_HEIGHT):
        raise ValueError("Display pocket is larger than the enclosure face.")
    if not 0 <= cfg.DISPLAY_VERTICAL_RADIUS_COMPENSATION:
        raise ValueError("Display vertical-radius compensation is invalid.")
    if cfg.DISPLAY_POCKET_VERTICAL_DIAMETER >= cfg.CASE_HEIGHT:
        raise ValueError("Compensated display pocket exceeds case height.")
    if cfg.DISPLAY_POCKET_DIAMETER <= cfg.BOARD_OPENING_DIAMETER:
        raise ValueError("Display pocket must be wider than the board opening.")
    if cfg.DISPLAY_POCKET_VERTICAL_DIAMETER <= cfg.BOARD_OPENING_VERTICAL_DIAMETER:
        raise ValueError("Vertical display support band has no width.")
    required_radial_space = cfg.BOARD_OUTER_DIAMETER + 2 * cfg.DEVICE_RADIAL_CLEARANCE
    if min(cavity_width, cavity_height) < required_radial_space:
        raise ValueError(
            "Side-wall thickness leaves insufficient radial device clearance."
        )
    if cfg.DISPLAY_POCKET_DIAMETER + 2 * cfg.DISPLAY_SUPPORT_WALL_THICKNESS >= min(
        cfg.CASE_WIDTH, cfg.CASE_HEIGHT
    ):
        raise ValueError("Circular display support is larger than the enclosure.")
    if (
        cfg.DISPLAY_POCKET_VERTICAL_DIAMETER
        + 2 * cfg.DISPLAY_SUPPORT_WALL_THICKNESS
        >= cfg.CASE_HEIGHT
    ):
        raise ValueError("Compensated display support exceeds case height.")
    if cfg.ENABLE_DISPLAY_CABLE_RELIEFS and not (
        0 < cfg.DISPLAY_CABLE_RELIEF_WIDTH < cfg.DISPLAY_POCKET_DIAMETER
    ):
        raise ValueError("Display cable-relief width is invalid.")
    if cfg.DISPLAY_RECESS_DEPTH <= cfg.FRONT_WALL:
        raise ValueError("Display platform must sit behind the front shell.")
    if cfg.DISPLAY_RECESS_DEPTH + cfg.DISPLAY_PLATFORM_THICKNESS >= cfg.CASE_DEPTH - cfg.REAR_WALL:
        raise ValueError("Display platform leaves no usable rear cavity.")
    if cfg.ENABLE_RECESSED_SCREW_WELLS:
        screw_gap = cfg.CASE_DEPTH - cfg.REAR_WALL - cfg.SCREW_MOUNT_DEPTH_FROM_FRONT
        if screw_gap <= 0:
            raise ValueError("Rear wall reaches or crosses the screw mounts.")
        if not 0 <= cfg.SCREW_WELL_DEPTH_REDUCTION < screw_gap:
            raise ValueError("Screw-well depth reduction consumes the bump.")
        if cfg.SCREW_WELL_INNER_DIAMETER <= cfg.SCREW_HOLE_DIAMETER:
            raise ValueError("Screw well must be wider than its through-hole.")
        if cfg.SCREW_WELL_FLOOR_THICKNESS >= (
            cfg.CASE_DEPTH
            - cfg.SCREW_MOUNT_DEPTH_FROM_FRONT
            - cfg.SCREW_WELL_DEPTH_REDUCTION
        ):
            raise ValueError("Screw-well floor consumes the complete recess.")
    if cfg.USB_C_OPENING_WIDTH + 2 * cfg.USB_C_TUNNEL_WALL >= cfg.CASE_WIDTH:
        raise ValueError("USB-C guide tunnel is wider than the enclosure.")
    if cfg.USB_C_OPENING_DEPTH + 2 * cfg.USB_C_TUNNEL_WALL >= cfg.CASE_DEPTH:
        raise ValueError("USB-C guide tunnel is deeper than the enclosure.")
    if cfg.USB_C_CENTRE_FROM_FRONT - cfg.USB_C_OPENING_DEPTH / 2.0 < 0:
        raise ValueError("USB-C opening extends beyond the front surface.")
    if (
        cfg.USB_C_CENTRE_FROM_FRONT
        + cfg.USB_C_OPENING_DEPTH / 2.0
        + cfg.USB_C_TUNNEL_WALL
        > cfg.CASE_DEPTH
    ):
        raise ValueError("USB-C guide tunnel extends beyond the rear surface.")
    if cfg.USB_C_TUNNEL_LENGTH <= cfg.SIDE_WALL:
        raise ValueError("USB-C guide tunnel must extend beyond the side wall.")
    if cfg.ENABLE_DUMMY_ESP32 and (
        cfg.DUMMY_PCB_THICKNESS <= 0
        or cfg.DUMMY_PCB_FRONT_FROM_DISPLAY + cfg.DUMMY_PCB_THICKNESS
        > cfg.MODULE_MAX_DEPTH + cfg.DIMENSION_EPSILON
        or cfg.DUMMY_CARRIER_FRONT_FROM_DISPLAY + cfg.DUMMY_CARRIER_DEPTH
        > cfg.DUMMY_PCB_FRONT_FROM_DISPLAY + cfg.DIMENSION_EPSILON
        or min(cfg.DUMMY_CARRIER_WIDTH, cfg.DUMMY_CARRIER_HEIGHT) <= 0
        or cfg.DUMMY_USB_C_HEIGHT <= 0
        or cfg.DUMMY_SCREW_BOSS_DIAMETER <= cfg.SCREW_HOLE_DIAMETER
        or cfg.DUMMY_SCREW_BOSS_DEPTH <= 0
        or cfg.DUMMY_SCREW_BOSS_FRONT_FROM_DISPLAY
        + cfg.DUMMY_SCREW_BOSS_DEPTH
        > cfg.MODULE_MAX_DEPTH + cfg.DIMENSION_EPSILON
        or any(
            min(width, depth, height) <= 0
            or depth_from_front + depth / 2.0
            > cfg.MODULE_MAX_DEPTH + cfg.DIMENSION_EPSILON
            for _, _, depth_from_front, _, width, depth, height
            in cfg.DUMMY_MAJOR_COMPONENT_BOXES
        )
    ):
        raise ValueError("Dummy ESP32 fit-check dimensions are invalid.")
    if cfg.ENABLE_BASE_AIR_VENTS and (
        cfg.BASE_AIR_VENT_DIAMETER <= 0
        or cfg.BASE_AIR_VENT_PITCH <= cfg.BASE_AIR_VENT_DIAMETER
        or cfg.BASE_SIDE_VENT_COLUMNS < 2
        or cfg.BASE_SIDE_VENT_ROWS < 1
        or not 0 < cfg.BASE_SIDE_VENT_MAIN_DEPTH_FRACTION < 1
        or (
            cfg.ENABLE_ACCESSORY_SIDE_AIR_VENTS
            and (
                cfg.ACCESSORY_SIDE_VENT_COLUMNS < 2
                or not 0 < cfg.ACCESSORY_SIDE_VENT_DEPTH_FRACTION < 1
            )
        )
        or cfg.BASE_TOP_VENT_COLUMNS < 2
        or cfg.BASE_TOP_VENT_ROWS < 1
    ):
        raise ValueError("Base airflow vent pattern is invalid.")
    if cfg.ENABLE_BASE_MIC_PORTS and (
        cfg.BASE_MIC_PORT_DIAMETER <= 0 or len(cfg.BASE_MIC_CENTRES_X) != 2
    ):
        raise ValueError("Exactly two valid USB-C microphone ports are required.")
    if cfg.ENABLE_REAR_SUPPORT_ACCESS_HOLE and not (
        0 < cfg.REAR_SUPPORT_ACCESS_HOLE_DIAMETER < min(cfg.CASE_WIDTH, cfg.CASE_HEIGHT)
    ):
        raise ValueError("Rear support-access hole diameter is invalid.")
    if cfg.ENABLE_BACK_ACCESSORY_LAYER:
        if cfg.ACCESSORY_INTERNAL_DEPTH <= cfg.ACCESSORY_WALL_THICKNESS:
            raise ValueError("Accessory depth reduction consumes the chamber.")
        if not 0 <= cfg.ACCESSORY_DEPTH_REDUCTION < cfg.ACCESSORY_MAX_HEIGHT:
            raise ValueError("Accessory depth reduction is invalid.")
        if cfg.ACCESSORY_COVER_THICKNESS <= 0:
            raise ValueError("Accessory cover thickness is invalid.")
        if cfg.ENABLE_COVER_ALIGNMENT_SKIRT and (
            cfg.ACCESSORY_ALIGNMENT_SKIRT_DEPTH <= 0
            or cfg.ACCESSORY_ALIGNMENT_SKIRT_DEPTH >= cfg.ACCESSORY_INTERNAL_DEPTH
            or cfg.ACCESSORY_ALIGNMENT_SKIRT_THICKNESS <= 0
            or cfg.ACCESSORY_ALIGNMENT_SKIRT_CLEARANCE < 0
            or cfg.ACCESSORY_ALIGNMENT_SKIRT_THICKNESS
            + cfg.ACCESSORY_ALIGNMENT_SKIRT_CLEARANCE
            >= cfg.ACCESSORY_WALL_THICKNESS
        ):
            raise ValueError("Cover alignment-skirt dimensions are invalid.")
        if cfg.ENABLE_FLUSH_SNAP_COVER and (
            cfg.ACCESSORY_SNAP_CLIP_LENGTH <= 0
            or cfg.ACCESSORY_SNAP_CLIP_LENGTH >= cfg.ACCESSORY_INTERNAL_DEPTH
            or cfg.ACCESSORY_SNAP_CLIP_THICKNESS <= 0
            or cfg.ACCESSORY_SNAP_CLIP_WIDTH <= 0
            or cfg.ACCESSORY_SNAP_HOOK_PROJECTION <= 0
            or cfg.ACCESSORY_SNAP_HOOK_PROJECTION > cfg.ACCESSORY_WALL_THICKNESS
            or cfg.ACCESSORY_SNAP_HOOK_LENGTH <= 0
            or cfg.ACCESSORY_SNAP_SLOT_CLEARANCE < 0
            or cfg.ACCESSORY_SNAP_ROOT_DEPTH <= 0
            or cfg.ACCESSORY_SNAP_ROOT_DEPTH >= cfg.ACCESSORY_SNAP_CLIP_LENGTH
            or cfg.ACCESSORY_SNAP_ROOT_EXTRA_WIDTH < 0
            or cfg.ACCESSORY_SNAP_ROOT_EXTRA_THICKNESS < 0
            or abs(cfg.ACCESSORY_SNAP_CLIP_X_CENTRE)
            + (
                cfg.ACCESSORY_SNAP_CLIP_WIDTH
                + cfg.ACCESSORY_SNAP_ROOT_EXTRA_WIDTH
            ) / 2.0
            >= cfg.CASE_WIDTH / 2.0
        ):
            raise ValueError("Flush snap-cover dimensions are invalid.")
        if cfg.ENABLE_FLUSH_SNAP_COVER:
            battery = next(
                module for module in cfg.ACCESSORY_MODULES
                if module.name.startswith("Battery")
            )
            left_modules = (
                module for module in cfg.ACCESSORY_MODULES
                if module.name.startswith(("GPS", "Speaker"))
            )
            left_module_right_edge = max(
                module.x + module.width / 2.0 for module in left_modules
            )
            battery_left_edge = battery.x - battery.width / 2.0
            reinforced_clip_width = (
                cfg.ACCESSORY_SNAP_CLIP_WIDTH
                + cfg.ACCESSORY_SNAP_ROOT_EXTRA_WIDTH
            )
            clip_left_edge = (
                cfg.ACCESSORY_SNAP_CLIP_X_CENTRE
                - reinforced_clip_width / 2.0
            )
            clip_right_edge = (
                cfg.ACCESSORY_SNAP_CLIP_X_CENTRE
                + reinforced_clip_width / 2.0
            )
            if not (
                left_module_right_edge < clip_left_edge
                and clip_right_edge < battery_left_edge
            ):
                raise ValueError("Top/bottom snap clips overlap a module footprint.")
        if (
            cfg.ENABLE_GPS_MIDDLE_PANEL_OPENING
            and not (
                0 < cfg.GPS_MIDDLE_PANEL_OPENING_SIZE <= 24.0
                and cfg.GPS_SCREW_KEEP_OUT_MARGIN >= 0
            )
        ):
            raise ValueError("GPS middle-panel window parameters are invalid.")
        if cfg.ENABLE_SPEAKER_VENTS and (
            cfg.SPEAKER_VENT_HOLE_DIAMETER <= 0
            or cfg.SPEAKER_VENT_PITCH <= cfg.SPEAKER_VENT_HOLE_DIAMETER
            or cfg.SPEAKER_VENT_COLUMNS < 1
            or cfg.SPEAKER_VENT_ROWS < 1
        ):
            raise ValueError("Speaker vent pattern is invalid.")
        if cfg.ENABLE_ACCESSORY_BOTTOM_MIC_VENTS and (
            cfg.ACCESSORY_BOTTOM_MIC_VENT_DIAMETER <= 0
            or cfg.ACCESSORY_BOTTOM_MIC_VENT_PITCH
            <= cfg.ACCESSORY_BOTTOM_MIC_VENT_DIAMETER
        ):
            raise ValueError("Accessory microphone rosette pattern is invalid.")
        for module in cfg.ACCESSORY_MODULES:
            holder_half_w = (
                module.width + cfg.MODULE_HOLDER_CLEARANCE
            ) / 2.0 + cfg.ACCESSORY_WALL_THICKNESS
            holder_half_h = (
                module.height + cfg.MODULE_HOLDER_CLEARANCE
            ) / 2.0 + cfg.ACCESSORY_WALL_THICKNESS
            if abs(module.x) + holder_half_w > cfg.CASE_WIDTH / 2.0:
                raise ValueError(f"{module.name} holder exceeds enclosure width.")
            if abs(module.z) + holder_half_h > cfg.CASE_HEIGHT / 2.0:
                raise ValueError(f"{module.name} holder exceeds enclosure height.")
    if usable_depth_from_front < required_depth_from_front:
        raise ValueError(
            f"Usable depth from the flush display face is "
            f"{usable_depth_from_front:.2f} mm; at least "
            f"{required_depth_from_front:.2f} mm is required."
        )
