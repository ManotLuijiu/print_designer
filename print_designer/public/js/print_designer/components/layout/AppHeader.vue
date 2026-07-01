<template>
	<div class="header">
		<h3
			class="title"
			:contenteditable="contenteditable"
			@keydown="handleKeyDown"
			@click="handleCLick"
			@blur="editNameOnBlur"
		>
			{{ print_format_name }}
		</h3>
		<button
			class="btn btn-sm btn-default export-jinja-btn"
			@click="openExportJinjaDialog"
			:title="
				__(
					'Export the current Print Designer format as a Jinja HTML + CSS bundle (Phase 1 MVP)'
				)
			"
		>
			<span>{{ __("Export Jinja") }}</span>
		</button>
		<div class="dropdown import-dropdown">
			<button
				class="btn btn-sm btn-default dropdown-toggle import-template-btn"
				type="button"
				data-toggle="dropdown"
				aria-haspopup="true"
				aria-expanded="false"
				:title="
					__(
						'Download the empty template, or import a completed Jinja bridge template into the current Print Designer format (template-first, MVP)'
					)
				"
			>
				<span>{{ __("Import") }}</span>
				<span class="caret"></span>
			</button>
			<ul class="dropdown-menu">
				<li>
					<a
						href="#"
						@click.prevent="downloadImportTemplate"
						:title="
							__(
								'Download the empty bridge import template with required PD:HEADER / PD:CONTENT / PD:FOOTER / PD:CSS markers'
							)
						"
					>
						{{ __("Download Template") }}
					</a>
				</li>
				<li>
					<a
						href="#"
						@click.prevent="openImportDialog"
						:title="
							__(
								'Import a completed Jinja bridge template into the current Print Designer format (template-first, MVP)'
							)
						"
					>
						{{ __("Import Template") }}
					</a>
				</li>
				<li v-if="ptgAvailable">
					<a
						href="#"
						@click.prevent="openPTGImportDialog"
						:title="
							__(
								'Pull generated HTML + CSS from a PTG Template (annotated form) into this Print Format. Requires the print_template_generator app.'
							)
						"
					>
						{{ __("Import PTG") }}
					</a>
				</li>
			</ul>
		</div>
		<button class="btn btn-sm btn-default exit-btn" @click="goToLastPage">
			<span>Exit</span>
		</button>
	</div>
</template>
<script setup>
import { ref } from "vue";
import { useMainStore } from "../../store/MainStore";
import { selectElementContents } from "../../utils";
import { showExportJinjaDialog } from "../dialogs/ExportJinjaDialog";
import { showImportJinjaBridgeDialog } from "../dialogs/ImportJinjaBridgeDialog";
import { showPTGImportDialog } from "../dialogs/PTGImportDialog";

const MainStore = useMainStore();

// Hide the "Import PTG" menu item if the PTG app is not installed.
const ptgAvailable = ref(
	frappe.boot && frappe.boot.installed_apps
		? frappe.boot.installed_apps.includes("print_template_generator")
		: false
);

const openExportJinjaDialog = () => {
	const formatName = MainStore.printDesignName || props.print_format_name;
	showExportJinjaDialog(formatName);
};

const openImportDialog = () => {
	const formatName = MainStore.printDesignName || props.print_format_name;
	showImportJinjaBridgeDialog(formatName);
};

const openPTGImportDialog = () => {
	const formatName = MainStore.printDesignName || props.print_format_name;
	showPTGImportDialog(formatName);
};

const downloadImportTemplate = () => {
	const formatName = MainStore.printDesignName || props.print_format_name;
	frappe.call({
		method:
			"print_designer.api.print_format_export_import.download_print_designer_import_template",
		args: { print_format_name: formatName },
		callback: (r) => {
			if (!r || !r.message) return;
			const text = r.message;
			const blob = new Blob([text], { type: "text/html;charset=utf-8" });
			const url = URL.createObjectURL(blob);
			const a = document.createElement("a");
			a.href = url;
			a.download = `print_designer_import_template${formatName ? "_" + formatName : ""}.html`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
			frappe.show_alert({
				message: __("Template downloaded"),
				indicator: "green",
			});
		},
	});
};

const contenteditable = ref(false);

const handleCLick = (e) => {
	if (!contenteditable.value) {
		contenteditable.value = true;
	}
	setTimeout(function () {
		if (document.activeElement !== e.target) {
			e.target.focus();
			selectElementContents(e.target);
		} else {
			e.target.focus();
		}
	}, 0);
};

const editNameOnBlur = (e) => {
	contenteditable.value = false;
	const new_name = e.target.innerText.trim();
	const doctype = "Print Format";
	const docname = MainStore.printDesignName;
	if (new_name === "" || new_name === docname) {
		e.target.innerText = docname;
		return;
	}
	if (new_name === docname) return;

	const callback = (r, rt) => {
		if (!r.exc) {
			$(document).trigger("rename", [doctype, docname, r.message || new_name]);
			if (locals[doctype] && locals[doctype][docname]) delete locals[doctype][docname];
			frappe.set_route();
			frappe.set_route("print-designer", new_name);
		}
	};

	frappe.call({
		method: "frappe.rename_doc",
		freeze: true,
		freeze_message: "Renaming Format Name...",
		args: {
			doctype: doctype,
			old: docname,
			new: new_name,
			merge: false,
		},
		callback: callback,
	});
};

const handleKeyDown = (e) => {
	if (["Escape", "Enter", "Tab"].indexOf(e.key) != -1) {
		e.target.blur();
	}
	if (e.key == "Tab") {
		e.preventDefault();
	}
};

const props = defineProps({
	print_format_name: String,
});
const goToLastPage = () => {
	let prev_route = frappe.get_prev_route();
	if (prev_route[0] !== "print-designer") {
		frappe.set_route(prev_route);
	} else {
		frappe.set_route();
	}
};
</script>
<style scoped lang="scss">
.header {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	padding: 0 16px;
	display: flex;
	justify-content: center;
	align-items: center;
	gap: 16px;
	height: calc(var(--navbar-height) - 1px);
	z-index: 1020;
	user-select: none;

	.title {
		flex: auto;
		font-size: var(--text-lg);
		font-weight: var(--weight-semibold);
		letter-spacing: 0.015em;
		margin-bottom: 0;
		user-select: none;
		cursor: text;
	}

/* Standard: adjacent buttons in a row share a fixed width.
 *
 * See harness/style_guide/print_designer_ui_conventions.md §1 for the
 * full rule. When the longest button's label changes, re-measure and
 * update the single `width` value below — do not apply width
 * individually to each button.
 */
.exit-btn,
.export-jinja-btn,
.import-template-btn {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 2px 8px;
		width: 100px;
		justify-content: center;
}

	[contenteditable] {
		outline: none;
		padding: 6px 8px;
		&:hover {
			padding-bottom: 5px;
			border-bottom: 1px solid #d5c291;
		}
		&:focus {
			border-bottom: 1px solid var(--primary);
			padding-bottom: 5px;
		}
	}
}
</style>
