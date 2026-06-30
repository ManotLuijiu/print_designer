import { createApp } from "vue";
import { createPinia } from "pinia";
import Designer from "./App.vue";
// import QrcodeVue from 'qrcode.vue';
class PrintDesigner {
  constructor({ wrapper, print_format }) {
    this.$wrapper = $(wrapper);
    this.print_format = print_format;
    const app = createApp(Designer, { print_format_name: this.print_format });
    app.use(createPinia());
    SetVueGlobals(app);
    app.mount(this.$wrapper.get(0));

    // Prefer the modern Desk navbar selector, fall back to legacy header.
    // Guard all access so a missing element never breaks initialization.
    const headerContainer =
      document.querySelector(".navbar .container") ||
      document.querySelector("header .container");

    const originalHeaderStyles = headerContainer
      ? {
          width: headerContainer.style.width,
          minWidth: headerContainer.style.minWidth,
          userSelect: headerContainer.style.userSelect,
        }
      : null;

    if (headerContainer) {
      headerContainer.style.width = "100%";
      headerContainer.style.minWidth = "100%";
      headerContainer.style.userSelect = "none";
    }

    frappe.router.once("change", () => {
      if (headerContainer && originalHeaderStyles) {
        Object.assign(headerContainer.style, originalHeaderStyles);
      }
      app.unmount();
    });
  }
}

frappe.provide("frappe.ui");
frappe.ui.PrintDesigner = PrintDesigner;
export default PrintDesigner;
