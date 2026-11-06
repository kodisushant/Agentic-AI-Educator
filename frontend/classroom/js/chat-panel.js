// Stub file for Member 4: Live Chat Panel Plugin
// Plugin interface: window.ChatPanel = { mount(el, {apiBase, getContext}) }
if (!window.ChatPanel) {
  window.ChatPanel = {
    mount: function(el, options) {
      console.log("[ChatPanel] Mounted in container", el, options);
    }
  };
}
