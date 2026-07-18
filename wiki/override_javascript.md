To override JavaScript functions, classes, or form events in the Frappe Framework, you must leverage a custom application and inject your scripts using hooks.py. Directly modifying core files is bad practice and will be overwritten during updates.The implementation details vary based on exactly what element requires overriding:1. Overriding Form Events (DocType JS)To modify or completely rewrite standard form events (like onload, refresh, or validate), use frappe.ui.form.off to clear the core handler before registering your new logic.Create a script at your_custom_app/public/js/custom_todo.js:javascript// Clear the existing onload event handler for this DocType
frappe.ui.form.off("ToDo", "onload");

// Define your new override logic
frappe.ui.form.on("ToDo", {
onload: function(frm) {
console.log("This is an overridden onload event!");
// Your custom logic goes here
}
});
Use code with caution.Bind this file to the target DocType inside your_custom_app/hooks.py:pythondoctype_js = {
"ToDo": "public/js/custom_todo.js"
}
Use code with caution.2. Overriding Core JavaScript Classes (Monkey Patching)For global framework components, controls, or classes (e.g., FormTimeline, FileUploader), modify the class prototype directly within a custom asset bundle.Create a bundle script at your_custom_app/public/js/patching.bundle.js:javascript// Import the original class from the Frappe core location
import FormTimeline from "../frappe/frappe/public/js/frappe/form/footer/form_timeline";

// Override the specific method via prototype monkey patching
FormTimeline.prototype.get_recipient = function() {
console.log("Intercepted recipient resolution.");
// Return your custom implementation
return this.frm.doc.owner;
};
Use code with caution.Register this asset bundle to load globally in your_custom_app/hooks.py:pythonapp_include_js = [
"/assets/your_custom_app/js/patching.bundle.js"
]
Use code with caution.3. Overriding List ViewsTo alter how the standard listing page displays or filters data for a DocType, hook into the global list settings array.Create a script at your_custom_app/public/js/custom_list.js:javascriptfrappe.listview_settings['Task'] = {
hide_name_filter: true,
onload: function(listview) {
console.log("Custom logic injected into Task list view.");
}
};
Use code with caution.Bind the file to the specific DocType in your_custom_app/hooks.py:pythondoctype_js = {
"Task": "public/js/custom_list.js"
}
Use code with caution.4. Overriding Desk PagesUnlike standard forms, core pages (e.g., POS, Backups) do not support extensions natively; you must completely recreate or overwrite the module.Create your_custom_app/public/js/custom_page.js.Copy the entire contents of the original page's JavaScript file and make your required modifications inside this new file.Link it in your_custom_app/hooks.py using page_js:pythonpage_js = {
"backups": "public/js/custom_page.js"
}
Use code with caution.Apply ChangesAfter creating your overrides, clear the server cache, clear the asset compilation cache, and refresh your browser:bashbench clear-cache
bench build --app your_custom_app

# include js in page

# page_js = {"page" : "public/js/file.js"}

<!-- From ERPNext's hooks.py -->

page_js = {"print": "public/js/print.js"}
