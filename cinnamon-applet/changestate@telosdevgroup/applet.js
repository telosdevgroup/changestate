const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Util = imports.misc.util;
const GLib = imports.gi.GLib;
const St = imports.gi.St;
const Mainloop = imports.mainloop;
const Settings = imports.ui.settings;

// Standard prime notches across available hardware threads
const PRIME_STEPS = [
    { id: "p2",  cores: 2,  label: "P:2 (~6% Floor)" },
    { id: "p3",  cores: 3,  label: "P:3 (~10%)" },
    { id: "p5",  cores: 5,  label: "P:5 (~16%)" },
    { id: "p7",  cores: 7,  label: "P:7 (~23%)" },
    { id: "p11", cores: 11, label: "P:11 (~35%)" },
    { id: "p13", cores: 13, label: "P:13 (~42%)" },
    { id: "p17", cores: 17, label: "P:17 (~55%)" },
    { id: "p19", cores: 19, label: "P:19 (~61%)" },
    { id: "p23", cores: 23, label: "P:23 (~74% Sweet Spot)" },
    { id: "p29", cores: 29, label: "P:29 (~94%)" },
    { id: "p31", cores: 31, label: "P:31 (100% Throttle)" }
];

class ChangeStateApplet extends Applet.TextIconApplet {
    constructor(metadata, orientation, panel_height, instance_id) {
        super(orientation, panel_height, instance_id);

        this.setAllowedLayout(Applet.AllowedLayout.BOTH);
        this.metadata = metadata;
        this.instance_id = instance_id;

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

        this._buildMenu();
        this._updateState();
        this._timeout = Mainloop.timeout_add_seconds(2, () => {
            this._updateState();
            return true;
        });
    }

    _buildMenu() {
        this.menu.removeAll();

        let header = new PopupMenu.PopupMenuItem("Hardware Power Shifter", { reactive: false });
        header.actor.add_style_class_name("display-subtitle");
        this.menu.addMenuItem(header);
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        this.sliderLabel = new PopupMenu.PopupMenuItem("Gear: P:23 (~74%)", { reactive: false });
        this.menu.addMenuItem(this.sliderLabel);

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
            this.slider.setValue(index / maxIdx);
            this.sliderLabel.label.text = `Gear: ${step.label}`;
            let termFlag = this.always_spawn_terminal ? " --terminal" : "";
            Util.spawnCommandLineAsync(`pkexec /home/dev/Code/changestate ${step.id}${termFlag}`);
        });
        this.menu.addMenuItem(this.slider);

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        let statusItem = new PopupMenu.PopupIconMenuItem("Status Inspector", "utilities-terminal", St.IconType.SYMBOLIC);
        statusItem.connect('activate', () => {
            Util.spawnCommandLineAsync('gnome-terminal --title="ChangeState Status" -- bash -c "/home/dev/Code/changestate status; echo; read -p \\"Press enter to close...\\""');
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
        if (state.startsWith("P:")) {
            let pNum = parseInt(state.split(":")[1]) || 2;
            this.set_applet_icon_name("preferences-system-power");
            this.set_applet_label(`P:${pNum}`);
            this.set_applet_tooltip(`ChangeState: Prime P:${pNum}`);

            let maxIdx = PRIME_STEPS.length - 1;
            for (let i = 0; i < PRIME_STEPS.length; i++) {
                if (PRIME_STEPS[i].cores === pNum) {
                    if (this.slider) this.slider.setValue(i / maxIdx);
                    if (this.sliderLabel) this.sliderLabel.label.text = `Gear: ${PRIME_STEPS[i].label}`;
                    break;
                }
            }
        } else {
            this.set_applet_icon_name("preferences-system-power");
            this.set_applet_label(state.substring(0, 5));
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
