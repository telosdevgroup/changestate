const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Util = imports.misc.util;
const GLib = imports.gi.GLib;
const St = imports.gi.St;
const Mainloop = imports.mainloop;
const Settings = imports.ui.settings;

// Discrete prime notches across available hardware threads
// MOM is intentionally excluded from the daily operational shifter slider.
const PRIME_STEPS = [
    { id: "p2",  cores: 2,  label: "P:2 (~6% Capacity / Floor)" },
    { id: "p3",  cores: 3,  label: "P:3 (~10% Capacity)" },
    { id: "p5",  cores: 5,  label: "P:5 (~16% Capacity / LowLow)" },
    { id: "p7",  cores: 7,  label: "P:7 (~23% Capacity)" },
    { id: "p11", cores: 11, label: "P:11 (~35% Capacity)" },
    { id: "p13", cores: 13, label: "P:13 (~42% Capacity)" },
    { id: "p17", cores: 17, label: "P:17 (~55% Capacity)" },
    { id: "p19", cores: 19, label: "P:19 (~61% Capacity)" },
    { id: "p23", cores: 23, label: "P:23 (~74% Capacity / 75% Sweet Spot)" },
    { id: "p29", cores: 29, label: "P:29 (~94% Capacity)" },
    { id: "p31", cores: 31, label: "P:31 (100% Capacity / Eleven)" }
];

class ChangeStateApplet extends Applet.TextIconApplet {
    constructor(metadata, orientation, panel_height, instance_id) {
        super(orientation, panel_height, instance_id);

        this.setAllowedLayout(Applet.AllowedLayout.BOTH);
        this.metadata = metadata;
        this.instance_id = instance_id;

        // Settings Pane Integration
        this.always_spawn_terminal = false;
        try {
            this.settings = new Settings.AppletSettings(this, metadata.uuid, instance_id);
            this.settings.bind("always-spawn-terminal", "always_spawn_terminal");
        } catch (e) {
            global.logError("ChangeState AppletSettings initialization error: " + e);
        }

        this.menuManager = new PopupMenu.PopupMenuManager(this);
        this.menu = new Applet.AppletPopupMenu(this, orientation);
        this.menuManager.addMenu(this.menu);

        this._currentState = "UNKNOWN";
        this._stateFile = "/var/run/changestate.state";

        // Build popup menu items (shifter slider)
        this._buildMenu();

        // Initial update and periodic refresh
        this._updateState();
        this._timeout = Mainloop.timeout_add_seconds(2, () => {
            this._updateState();
            return true;
        });
    }

    // Callback called from Cinnamon Settings window button
    on_mom_triggered() {
        let termFlag = this.always_spawn_terminal ? " --terminal" : "";
        Util.spawnCommandLineAsync(`pkexec /home/dev/Code/tdg/compstate/changestate mom${termFlag}`);
    }

    _buildMenu() {
        this.menu.removeAll();

        // Header
        let header = new PopupMenu.PopupMenuItem("Hardware Power Shifter", { reactive: false });
        header.actor.add_style_class_name("display-subtitle");
        this.menu.addMenuItem(header);
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        // Shifter notch readout
        this.sliderLabel = new PopupMenu.PopupMenuItem("Gear: P:23 (~74% / 75% Sweet Spot)", { reactive: false });
        this.menu.addMenuItem(this.sliderLabel);

        // Continuous Prime Stepping Shifter
        // Default cursor around P:23 notch (index 8 of 10 = 0.8)
        this.slider = new PopupMenu.PopupSliderMenuItem(0.8);
        this.slider.connect('value-changed', (item, value) => {
            let maxIdx = PRIME_STEPS.length - 1;
            let index = Math.round(value * maxIdx);
            let step = PRIME_STEPS[index];
            this.sliderLabel.label.text = `Gear: ${step.label}`;
        });

        this.slider.connect('drag-end', () => {
            let maxIdx = PRIME_STEPS.length - 1;
            let index = Math.round(this.slider.value * maxIdx);
            let step = PRIME_STEPS[index];
            // Snap handle cleanly to selected prime notch
            this.slider.setValue(index / maxIdx);
            this.sliderLabel.label.text = `Gear: ${step.label}`;
            let termFlag = this.always_spawn_terminal ? " --terminal" : "";
            Util.spawnCommandLineAsync(`pkexec /home/dev/Code/tdg/compstate/changestate ${step.id}${termFlag}`);
        });
        this.menu.addMenuItem(this.slider);

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        // Quick Status Inspect Action
        let statusItem = new PopupMenu.PopupIconMenuItem("Open Status Terminal", "utilities-terminal", St.IconType.SYMBOLIC);
        statusItem.connect('activate', () => {
            Util.spawnCommandLineAsync('gnome-terminal --title="ChangeState Status" -- bash -c "/home/dev/Code/tdg/compstate/changestate status; echo; read -p \\"Press enter to close...\\""');
        });
        this.menu.addMenuItem(statusItem);
    }

    _updateState() {
        let state = "MANUAL";
        try {
            if (GLib.file_test(this._stateFile, GLib.FileTest.EXISTS)) {
                let [ok, contents] = GLib.file_get_contents(this._stateFile);
                if (ok) {
                    state = contents.toString().trim().toUpperCase();
                }
            }
        } catch (e) {
            state = "MANUAL";
        }

        if (state !== this._currentState) {
            this._currentState = state;
            this._applyDisplay(state);
        }
    }

    _applyDisplay(state) {
        if (state === "MOM") {
            this.set_applet_icon_name("security-high");
            this.set_applet_label("MOM");
            this.set_applet_tooltip("ChangeState: MOM (Metal Over Moss / Submerged)");
            if (this.sliderLabel) this.sliderLabel.label.text = "Gear: MOM (Defensive Lockdown)";
            if (this.slider) this.slider.setValue(0);
        } else if (state.startsWith("P:")) {
            let pNum = parseInt(state.split(":")[1]) || 2;
            this.set_applet_icon_name("preferences-system-power");
            this.set_applet_label(`P:${pNum}`);
            this.set_applet_tooltip(`ChangeState: Prime ${pNum}`);

            // Sync slider handle to current prime notch
            let maxIdx = PRIME_STEPS.length - 1;
            for (let i = 0; i < PRIME_STEPS.length; i++) {
                if (PRIME_STEPS[i].cores === pNum) {
                    if (this.slider) this.slider.setValue(i / maxIdx);
                    if (this.sliderLabel) this.sliderLabel.label.text = `Gear: ${PRIME_STEPS[i].label}`;
                    break;
                }
            }
        } else if (state === "LOWLOW") {
            this.set_applet_icon_name("battery-low");
            this.set_applet_label("P:5");
            this.set_applet_tooltip("ChangeState: LowLow (~16% / Server Ready)");
            // Align with p5
            let maxIdx = PRIME_STEPS.length - 1;
            if (this.slider) this.slider.setValue(2 / maxIdx);
            if (this.sliderLabel) this.sliderLabel.label.text = "Gear: P:5 (~16% / LowLow)";
        } else if (state in { "FOUR": 1, "4": 1, "CRUISE": 1, "DEV": 1, "MID": 1 }) {
            this.set_applet_icon_name("applications-development");
            this.set_applet_label("P:23");
            this.set_applet_tooltip("ChangeState: Four / Cruising (~74% Sweet Spot)");
            let maxIdx = PRIME_STEPS.length - 1;
            if (this.slider) this.slider.setValue(8 / maxIdx);
            if (this.sliderLabel) this.sliderLabel.label.text = "Gear: P:23 (~74% / 75% Sweet Spot)";
        } else if (state === "ELEVEN") {
            this.set_applet_icon_name("system-run");
            this.set_applet_label("P:31");
            this.set_applet_tooltip("ChangeState: Eleven (100% Throttle / 97W GPU)");
            if (this.slider) this.slider.setValue(1.0);
            if (this.sliderLabel) this.sliderLabel.label.text = "Gear: P:31 (100% / Eleven)";
        } else {
            this.set_applet_icon_name("preferences-system-power");
            this.set_applet_label(state.substring(0, 4));
            this.set_applet_tooltip(`ChangeState: ${state}`);
        }
    }

    on_applet_clicked(event) {
        this.menu.toggle();
    }

    on_applet_removed_from_panel() {
        if (this._timeout) {
            Mainloop.source_remove(this._timeout);
            this._timeout = null;
        }
    }
}

function main(metadata, orientation, panel_height, instance_id) {
    return new ChangeStateApplet(metadata, orientation, panel_height, instance_id);
}
