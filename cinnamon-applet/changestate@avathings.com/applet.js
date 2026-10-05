const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Util = imports.misc.util;
const GLib = imports.gi.GLib;
const St = imports.gi.St;
const Mainloop = imports.mainloop;
const Settings = imports.ui.settings;

// Standard fallback capacity tiers if dynamic host detection is unreachable
const DEFAULT_CAPACITY_TIERS = [
    { id: "p2",  prime: 2,  pct: 6,   label: "P:2 · ~6% (Floor)" },
    { id: "p3",  prime: 3,  pct: 10,  label: "P:3 · ~10%" },
    { id: "p5",  prime: 5,  pct: 16,  label: "P:5 · ~16%" },
    { id: "p7",  prime: 7,  pct: 23,  label: "P:7 · ~23%" },
    { id: "p11", prime: 11, pct: 35,  label: "P:11 · ~35%" },
    { id: "p13", prime: 13, pct: 42,  label: "P:13 · ~42%" },
    { id: "p17", prime: 17, pct: 55,  label: "P:17 · ~55%" },
    { id: "p19", prime: 19, pct: 61,  label: "P:19 · ~61%" },
    { id: "p23", prime: 23, pct: 75,  label: "P:23 · ~75% (Balanced)" },
    { id: "p29", prime: 29, pct: 93,  label: "P:29 · ~93%" },
    { id: "p31", prime: 31, pct: 100, label: "P:31 · 100% (Max)" }
];

class ChangeStateApplet extends Applet.TextIconApplet {
    constructor(metadata, orientation, panel_height, instance_id) {
        super(orientation, panel_height, instance_id);

        this.setAllowedLayout(Applet.AllowedLayout.BOTH);
        this.metadata = metadata;
        this.instance_id = instance_id;

        this.always_spawn_terminal = false;
        this.always_require_password = false;
        try {
            this.settings = new Settings.AppletSettings(this, metadata.uuid, instance_id);
            this.settings.bind("always-spawn-terminal", "always_spawn_terminal");
            this.settings.bind("always-require-password", "always_require_password");
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

        // 1. Dynamic target capacity status header: Full-width, crisp white, never cut off
        this.sliderLabel = new PopupMenu.PopupBaseMenuItem({ reactive: false });
        let headerLabel = new St.Label({
            text: "P:23 · ~75% (Balanced)",
            style: "color: #ffffff; font-size: 1.35em; font-weight: 800; padding: 10px 4px; letter-spacing: 0.5px;"
        });
        headerLabel.clutter_text.set_ellipsize(0); // 0 = PANGO_ELLIPSIZE_NONE (never truncate)
        headerLabel.clutter_text.set_line_wrap(false);
        this.sliderLabel.addActor(headerLabel, { span: -1, expand: true });
        this.sliderLabel.label = headerLabel;
        this.menu.addMenuItem(this.sliderLabel);

        // Generous min-width with no margin/overflow clipping
        this.menu.box.set_style("min-width: 380px; padding: 10px;");

        // Find index of P:23 (the universal 75% sweet spot)
        let sweetIdx = this.capacityTiers.findIndex(s => s.id === "p23");
        let initialRatio = sweetIdx !== -1 ? (sweetIdx / (this.capacityTiers.length - 1)) : 0.8;

        // 2. Punchy Notched Slider
        this.slider = new PopupMenu.PopupSliderMenuItem(initialRatio);
        this.slider.actor.set_style("padding: 14px 4px; min-height: 38px;");
        this._isDragging = false;
        this._lastNotchIndex = sweetIdx;

        this.slider.connect('drag-begin', () => {
            this._isDragging = true;
        });

        this.slider.connect('value-changed', (item, value) => {
            let maxIdx = this.capacityTiers.length - 1;
            let clampedVal = Math.max(0.0, Math.min(1.0, value));
            let index = Math.round(clampedVal * maxIdx);
            index = Math.max(0, Math.min(maxIdx, index));
            if (index !== this._lastNotchIndex) {
                this._lastNotchIndex = index;
            }
            let tier = this.capacityTiers[index];
            if (tier && this.sliderLabel) {
                this.sliderLabel.label.text = tier.label;
            }
        });

        this.slider.connect('drag-end', () => {
            let maxIdx = this.capacityTiers.length - 1;
            let clampedVal = Math.max(0.0, Math.min(1.0, this.slider.value));
            let index = Math.round(clampedVal * maxIdx);
            index = Math.max(0, Math.min(maxIdx, index));
            let tier = this.capacityTiers[index];
            this._lastNotchIndex = index;
            this.slider.setValue(index / maxIdx);
            if (tier && this.sliderLabel) {
                this.sliderLabel.label.text = tier.label;
            }
            this._isDragging = false;

            let termFlag = this.always_spawn_terminal ? " --terminal" : "";
            let pkFlag = this.always_require_password ? "--disable-internal-agent " : "";
            Util.spawnCommandLineAsync(`pkexec ${pkFlag}changestate ${tier.id}${termFlag}`);
        });
        this.menu.addMenuItem(this.slider);

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        // 3. Actions: Punchy icons, larger readable text, generous touch targets
        let statusItem = new PopupMenu.PopupIconMenuItem("Current Hardware State", "utilities-terminal", St.IconType.SYMBOLIC);
        statusItem.label.set_style("font-size: 1.25em; font-weight: 500; padding: 8px 4px;");
        statusItem.connect('activate', () => {
            Util.spawnCommandLineAsync('gnome-terminal --title="ChangeState Status" -- bash -c "changestate status; echo; read -p \\"Press enter to close...\\""');
        });
        this.menu.addMenuItem(statusItem);

        let settingsItem = new PopupMenu.PopupIconMenuItem("ChangeState Settings", "preferences-system", St.IconType.SYMBOLIC);
        settingsItem.label.set_style("font-size: 1.25em; font-weight: 500; padding: 8px 4px;");
        settingsItem.connect('activate', () => {
            this.configureApplet();
        });
        this.menu.addMenuItem(settingsItem);
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
                    if (this.slider && !this._isDragging) {
                        this.slider.setValue(i / maxIdx);
                    }
                    if (this.sliderLabel && !this._isDragging) {
                        this.sliderLabel.label.text = this.capacityTiers[i].label;
                    }
                    break;
                }
            }
        } else {
            this.set_applet_icon_name("preferences-system-power");
            this.set_applet_label(state.substring(0, 5));
            this.set_applet_tooltip(`ChangeState: ${state}`);
        }
    }

    _openProjectPage() {
        Util.spawnCommandLineAsync('xdg-open "https://github.com/telosdevgroup/changestate"');
    }

    _openGithubSponsors() {
        Util.spawnCommandLineAsync('xdg-open "https://github.com/sponsors"');
    }

    _openSupportTip() {
        Util.spawnCommandLineAsync('xdg-open "https://avathings.lemonsqueezy.com"');
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
