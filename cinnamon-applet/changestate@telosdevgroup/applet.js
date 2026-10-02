const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Util = imports.misc.util;
const GLib = imports.gi.GLib;
const Gio = imports.gi.Gio;
const St = imports.gi.St;
const Mainloop = imports.mainloop;
const Settings = imports.ui.settings;

const ALL_PRIMES = [1, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71];

function getHostTotalCores() {
    let count = 0;
    try {
        let dir = Gio.File.new_for_path("/sys/devices/system/cpu");
        let enumerator = dir.enumerate_children("standard::name", Gio.FileQueryInfoFlags.NONE, null);
        let info;
        while ((info = enumerator.next_file(null)) !== null) {
            let name = info.get_name();
            if (/^cpu[0-9]+$/.test(name)) {
                count++;
            }
        }
    } catch (e) {
        // fallback
    }
    return count > 0 ? count : 16;
}

function getPrimeStepsForHost() {
    let totalCores = getHostTotalCores();
    let steps = [];
    for (let p of ALL_PRIMES) {
        if (p <= totalCores) {
            let pct = Math.round((p / totalCores) * 100);
            let suffix = "";
            if (p === 1) suffix = " (Floor)";
            else if (pct >= 95) suffix = " (Full Throttle)";
            else if (pct >= 70 && pct <= 80) suffix = " (Sweet Spot)";
            steps.push({
                id: `p${p}`,
                cores: p,
                label: `P:${p} (~${pct}%${suffix})`
            });
        }
    }
    return steps.length > 0 ? steps : [{ id: "p1", cores: 1, label: "P:1 (Floor)" }];
}

function snapToNearestPrime(count) {
    let closest = ALL_PRIMES[0];
    let minDiff = Math.abs(count - closest);
    for (let p of ALL_PRIMES) {
        let diff = Math.abs(count - p);
        if (diff < minDiff) {
            minDiff = diff;
            closest = p;
        }
    }
    return closest;
}

class ChangeStateApplet extends Applet.TextIconApplet {
    constructor(metadata, orientation, panel_height, instance_id) {
        super(orientation, panel_height, instance_id);

        this.setAllowedLayout(Applet.AllowedLayout.BOTH);
        this.metadata = metadata;
        this.instance_id = instance_id;

        this.primeSteps = getPrimeStepsForHost();

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

        let defaultStep = this.primeSteps[Math.min(this.primeSteps.length - 1, 2)];
        this.sliderLabel = new PopupMenu.PopupMenuItem(`Gear: ${defaultStep.label}`, { reactive: false });
        this.menu.addMenuItem(this.sliderLabel);

        this.slider = new PopupMenu.PopupSliderMenuItem(0.8);
        this.slider.connect('value-changed', (item, value) => {
            let maxIdx = this.primeSteps.length - 1;
            let index = Math.round(value * maxIdx);
            let step = this.primeSteps[index];
            this.sliderLabel.label.text = `Gear: ${step.label}`;
        });

        this.slider.connect('drag-end', () => {
            let maxIdx = this.primeSteps.length - 1;
            let index = Math.round(this.slider.value * maxIdx);
            let step = this.primeSteps[index];
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

    _getActiveCoreCount() {
        try {
            if (GLib.file_test("/sys/devices/system/cpu/online", GLib.FileTest.EXISTS)) {
                let [ok, contents] = GLib.file_get_contents("/sys/devices/system/cpu/online");
                if (ok) {
                    let onlineStr = contents.toString().trim();
                    let count = 0;
                    for (let part of onlineStr.split(",")) {
                        if (part.includes("-")) {
                            let [start, end] = part.split("-").map(Number);
                            count += (end - start + 1);
                        } else if (part.length > 0) {
                            count += 1;
                        }
                    }
                    if (count > 0) return count;
                }
            }
        } catch (e) {
            // fallback
        }
        return null;
    }

    _updateState() {
        let state = null;
        try {
            if (GLib.file_test(this._stateFile, GLib.FileTest.EXISTS)) {
                let [ok, contents] = GLib.file_get_contents(this._stateFile);
                if (ok) {
                    state = contents.toString().trim().toUpperCase();
                }
            }
        } catch (e) {
            state = null;
        }

        if (!state) {
            let activeCores = this._getActiveCoreCount();
            if (activeCores) {
                let primeNum = snapToNearestPrime(activeCores);
                state = `P:${primeNum}`;
            } else {
                state = "AUTO";
            }
        }

        if (state !== this._currentState) {
            this._currentState = state;
            this._applyDisplay(state);
        }
    }

    _applyDisplay(state) {
        if (state.startsWith("P:")) {
            let pNum = parseInt(state.split(":")[1]) || 1;
            this.set_applet_icon_name("preferences-system-power");
            this.set_applet_label(`P:${pNum}`);
            this.set_applet_tooltip(`ChangeState: Prime P:${pNum}`);

            let maxIdx = this.primeSteps.length - 1;
            for (let i = 0; i < this.primeSteps.length; i++) {
                if (this.primeSteps[i].cores === pNum) {
                    if (this.slider && maxIdx > 0) this.slider.setValue(i / maxIdx);
                    if (this.sliderLabel) this.sliderLabel.label.text = `Gear: ${this.primeSteps[i].label}`;
                    break;
                }
            }
        } else {
            this.set_applet_icon_name("preferences-system-power");
            this.set_applet_label(state);
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
