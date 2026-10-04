const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Util = imports.misc.util;
const GLib = imports.gi.GLib;
const St = imports.gi.St;
const Mainloop = imports.mainloop;
const Settings = imports.ui.settings;

// Standard fallback capacity tiers if dynamic host detection is unreachable
const DEFAULT_CAPACITY_TIERS = [
    { id: "p2",  prime: 2,  pct: 6,   label: "P:2 (6% Floor Capacity)" },
    { id: "p3",  prime: 3,  pct: 10,  label: "P:3 (10% Capacity)" },
    { id: "p5",  prime: 5,  pct: 16,  label: "P:5 (16% Capacity)" },
    { id: "p7",  prime: 7,  pct: 23,  label: "P:7 (23% Capacity)" },
    { id: "p11", prime: 11, pct: 35,  label: "P:11 (35% Capacity)" },
    { id: "p13", prime: 13, pct: 42,  label: "P:13 (42% Capacity)" },
    { id: "p17", prime: 17, pct: 55,  label: "P:17 (55% Capacity)" },
    { id: "p19", prime: 19, pct: 61,  label: "P:19 (61% Capacity)" },
    { id: "p23", prime: 23, pct: 75,  label: "P:23 (75% Balanced Capacity)" },
    { id: "p29", prime: 29, pct: 93,  label: "P:29 (93% Capacity)" },
    { id: "p31", prime: 31, pct: 100, label: "P:31 (100% Full Capacity)" }
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

        // Dynamically query machine-tailored capacity tiers
        this.capacityTiers = this._loadMachineTiers();

        this._buildMenu();
        this._updateState();
        this._timeout = Mainloop.timeout_add_seconds(2, () => {
            this._updateState();
            return true;
        });
    }

    _loadMachineTiers() {
        try {
            let [ok, out] = GLib.spawn_command_line_sync("changestate tiers-json");
            if (ok && out) {
                let parsed = JSON.parse(out.toString());
                if (Array.isArray(parsed) && parsed.length > 0) {
                    return parsed;
                }
            }
        } catch (e) {
            global.logWarning("ChangeState: dynamic tier query fallback: " + e);
        }
        return DEFAULT_CAPACITY_TIERS;
    }

    _buildMenu() {
        this.menu.removeAll();

        let header = new PopupMenu.PopupMenuItem("Elastic Capacity Controller", { reactive: false });
        header.actor.add_style_class_name("display-subtitle");
        this.menu.addMenuItem(header);
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        this.sliderLabel = new PopupMenu.PopupMenuItem("Target: P:23 (75% Balanced Capacity)", { reactive: false });
        this.menu.addMenuItem(this.sliderLabel);

        // Find index of P:23 (the universal 75% sweet spot)
        let sweetIdx = this.capacityTiers.findIndex(s => s.id === "p23");
        let initialRatio = sweetIdx !== -1 ? (sweetIdx / (this.capacityTiers.length - 1)) : 0.8;

        this.slider = new PopupMenu.PopupSliderMenuItem(initialRatio);
        this.slider.connect('value-changed', (item, value) => {
            let maxIdx = this.capacityTiers.length - 1;
            let index = Math.round(value * maxIdx);
            let tier = this.capacityTiers[index];
            this.sliderLabel.label.text = `Target: ${tier.label}`;
        });

        this.slider.connect('drag-end', () => {
            let maxIdx = this.capacityTiers.length - 1;
            let index = Math.round(this.slider.value * maxIdx);
            let tier = this.capacityTiers[index];
            this.slider.setValue(index / maxIdx);
            this.sliderLabel.label.text = `Target: ${tier.label}`;
            let termFlag = this.always_spawn_terminal ? " --terminal" : "";
            Util.spawnCommandLineAsync(`pkexec changestate ${tier.id}${termFlag}`);
        });
        this.menu.addMenuItem(this.slider);

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        let statusItem = new PopupMenu.PopupIconMenuItem("Current Hardware State", "utilities-terminal", St.IconType.SYMBOLIC);
        statusItem.connect('activate', () => {
            Util.spawnCommandLineAsync('gnome-terminal --title="ChangeState Status" -- bash -c "changestate status; echo; read -p \\"Press enter to close...\\""');
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

            let maxIdx = this.capacityTiers.length - 1;
            for (let i = 0; i < this.capacityTiers.length; i++) {
                if (this.capacityTiers[i].prime === pNum || this.capacityTiers[i].id === `p${pNum}`) {
                    if (this.slider) this.slider.setValue(i / maxIdx);
                    if (this.sliderLabel) this.sliderLabel.label.text = `Active: ${this.capacityTiers[i].label}`;
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
