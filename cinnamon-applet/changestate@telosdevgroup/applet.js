const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Util = imports.misc.util;
const GLib = imports.gi.GLib;
const St = imports.gi.St;
const Mainloop = imports.mainloop;

class ChangeStateApplet extends Applet.TextIconApplet {
    constructor(metadata, orientation, panel_height, instance_id) {
        super(orientation, panel_height, instance_id);

        this.setAllowedLayout(Applet.AllowedLayout.BOTH);
        this.metadata = metadata;

        this.menuManager = new PopupMenu.PopupMenuManager(this);
        this.menu = new Applet.AppletPopupMenu(this, orientation);
        this.menuManager.addMenu(this.menu);

        this._currentState = "UNKNOWN";
        this._stateFile = "/var/run/changestate.state";

        // Build popup menu items
        this._buildMenu();

        // Initial update and periodic refresh
        this._updateState();
        this._timeout = Mainloop.timeout_add_seconds(2, () => {
            this._updateState();
            return true;
        });
    }

    _buildMenu() {
        this.menu.removeAll();

        // Header
        let header = new PopupMenu.PopupMenuItem("Switch Power State", { reactive: false });
        header.actor.add_style_class_name("display-subtitle");
        this.menu.addMenuItem(header);
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        // Menu items
        const states = [
            { id: "mom", label: "MOM (Defensive / 1 Core / Air-Gapped)", icon: "security-high" },
            { id: "lowlow", label: "LowLow (Battery Sip / Wi-Fi ON)", icon: "battery-low" },
            { id: "mid", label: "Mid (Balanced / 50% Cores)", icon: "applications-development" },
            { id: "eleven", label: "Eleven (Cranked to 11 / Full Blast)", icon: "system-run" }
        ];

        for (let s of states) {
            let item = new PopupMenu.PopupIconMenuItem(s.label, s.icon, St.IconType.SYMBOLIC);
            item.connect('activate', () => {
                Util.spawnCommandLineAsync(`pkexec /home/dev/Code/changestate ${s.id}`);
            });
            this.menu.addMenuItem(item);
        }

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        // Status action
        let statusItem = new PopupMenu.PopupIconMenuItem("Open Status Terminal", "utilities-terminal", St.IconType.SYMBOLIC);
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
        switch (state) {
            case "MOM":
                this.set_applet_icon_name("security-high");
                this.set_applet_label("MOM");
                this.set_applet_tooltip("ChangeState: MOM (Metal Over Moss)");
                break;
            case "LOWLOW":
                this.set_applet_icon_name("battery-low");
                this.set_applet_label("LOW");
                this.set_applet_tooltip("ChangeState: LowLow (Battery Sip)");
                break;
            case "MID":
                this.set_applet_icon_name("applications-development");
                this.set_applet_label("MID");
                this.set_applet_tooltip("ChangeState: Mid (Balanced)");
                break;
            case "ELEVEN":
                this.set_applet_icon_name("system-run");
                this.set_applet_label("11");
                this.set_applet_tooltip("ChangeState: Eleven (Full Blast)");
                break;
            default:
                this.set_applet_icon_name("preferences-system-power");
                this.set_applet_label(state.substring(0, 4));
                this.set_applet_tooltip(`ChangeState: ${state}`);
                break;
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
