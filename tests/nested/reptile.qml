import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons as Commons
import "barbarian" as Barb

ShellRoot {
  PanelWindow {
    screen: Quickshell.screens.find(function(sc) { return sc.name === "BARBTEST" }) || Quickshell.screens[0]
    anchors { top: true; right: true }
    implicitWidth: 40
    implicitHeight: 30
    color: "#202020"
    Barb.Reptile { id: reptile }
  }
  IpcHandler {
    target: "atlas.arrange"
    function layouts(): void { reptile.toggle() }
    function features(): void { reptile.open(); reptile.selectTab(2) }
    function quickApps(): void { reptile.open(); reptile.selectTab(1) }
    function status(): string {
      return JSON.stringify({ready: reptile.featuresReady, values: reptile.featureValues,
                            pending: reptile.featureBusy, loadError: reptile.featureLoadError,
                            saveError: reptile.featureSaveError, dirty: reptile.dirtyList,
                            foreground: String(reptile.featureForeground), tab: reptile.tab})
    }
    function markDirty(desk: int): void { reptile.markDirty(desk) }
    function laying(): void { reptile.laying("Test layout progress") }
    function lightTheme(): void {
      Commons.Color.loadUserShell("")
      Commons.Color.loadShell("")
      Commons.Color.background = "#faf6e9"
      Commons.Color.foreground = "#2d353b"
      Commons.Color.accent = "#9c5b25"
      Commons.Color.muted = "#615c4f"
    }
    function placeholder(): string {
      return reptile.placeholder(JSON.stringify({token:"test-placeholder", klass:"test-missing",
          title:"Test missing app", headline:"Test missing app", reason:"This is an isolated test.", actions:[]}))
    }
  }
}
